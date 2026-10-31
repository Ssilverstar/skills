"""Agent Observatory: 호스트 스냅샷을 읽어 SQLite에 보관하고 웹 UI·API·OpenTelemetry로 노출한다."""

import json
import logging
import math
import os
import signal
import sqlite3
import sys
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import urllib.parse

from opentelemetry import trace

log = logging.getLogger("observatory")
tracer = trace.get_tracer("agent-observatory")
STATIC = Path(__file__).with_name("static")
STATIC_FILES = {"app.js": "text/javascript", "style.css": "text/css"}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")


def parse_ts(value):
    """ISO8601 문자열 → UTC datetime. 해석할 수 없으면 None."""
    if not isinstance(value, str):
        return None
    try:
        ts = datetime.fromisoformat(value)
    except ValueError:
        return None
    return (ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def num(value):
    """유한한 숫자만 통과시킨다. None·문자열·bool·NaN·Infinity는 미확인(None)으로 남기고 0으로 바꾸지 않는다."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return value


def _dicts(value):
    return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def _dict(value):
    return value if isinstance(value, dict) else {}


# input은 캐시 읽기·쓰기를 포함하고 reasoning은 output의 일부다. type별 시계열을 서로 더하지 않는다.
TOKEN_TYPES = ("input", "cached_input", "cache_write_input", "output", "reasoning", "total")

# 이름 → (단위, 설명). 값이 없는(None) 지표는 내보내지 않는다.
METRICS = {
    "observatory.snapshot.age": ("s", "마지막 호스트 스냅샷 이후 경과 시간"),
    "observatory.snapshot.errors": ("{error}", "스냅샷에 기록된 수집 오류 수"),
    "observatory.host.cpu.utilization": ("%", "호스트 CPU 사용률"),
    "observatory.host.memory.used": ("By", "호스트 메모리 사용량"),
    "observatory.host.memory.utilization": ("%", "호스트 메모리 사용률"),
    "observatory.gpu.utilization": ("%", "GPU 사용률"),
    "observatory.gpu.temperature": ("Cel", "GPU 온도"),
    "observatory.gpu.power": ("W", "GPU 전력"),
    "observatory.gpu.memory.used": ("By", "GPU 전용 메모리 사용량(보고될 때만)"),
    "observatory.inference.reachable": ("1", "추론 서버 응답 여부(1/0)"),
    "observatory.inference.models": ("{model}", "추론 서버가 보고한 모델 수"),
    "observatory.agent.tokens": ("{token}", "에이전트 로컬 기록 누적 토큰(type 간 포함관계, 합산 금지)"),
    "observatory.agent.model.tokens": ("{token}", "에이전트·모델별 누적 토큰(agent.tokens와 합산 금지)"),
    "observatory.agent.sessions": ("{session}", "에이전트 로컬 세션 수"),
    "observatory.agent.plan.used": ("%", "공식/관측 플랜 한도 사용률"),
    "observatory.skills.installed": ("{skill}", "에이전트별 설치 스킬 수"),
    "observatory.skills.enabled": ("{skill}", "에이전트별 활성 스킬 수"),
    "observatory.skills.repository": ("{skill}", "저장소 원본 스킬 수"),
}


def metric_points(snap, now=None):
    """스냅샷 → [(지표명, 값, 속성)]. 미확인 값은 생략한다."""
    if not isinstance(snap, dict):
        return []
    out = []

    def add(name, value, **attrs):
        value = num(value)
        if value is not None:
            out.append((name, value, {k: str(v) for k, v in attrs.items() if v is not None}))

    collected = parse_ts(snap.get("collected_at"))
    if collected:
        add("observatory.snapshot.age", ((now or datetime.now(timezone.utc)) - collected).total_seconds())
    if isinstance(snap.get("errors"), list):
        add("observatory.snapshot.errors", len(snap["errors"]))

    hw = _dict(snap.get("hardware"))
    host = hw.get("hostname")
    add("observatory.host.cpu.utilization", hw.get("cpu_percent"), host=host)
    add("observatory.host.memory.used", hw.get("memory_used_bytes"), host=host)
    add("observatory.host.memory.utilization", hw.get("memory_used_percent"), host=host)
    for i, gpu in enumerate(_dicts(hw.get("gpu"))):
        attrs = {"host": host, "gpu_index": i, "gpu_name": gpu.get("name")}
        add("observatory.gpu.utilization", gpu.get("utilization_percent"), **attrs)
        add("observatory.gpu.temperature", gpu.get("temperature_c"), **attrs)
        add("observatory.gpu.power", gpu.get("power_watts"), **attrs)
        add("observatory.gpu.memory.used", gpu.get("memory_used_bytes"), **attrs)
    inf = _dict(hw.get("inference"))
    if isinstance(inf.get("reachable"), bool):
        add("observatory.inference.reachable", int(inf["reachable"]), endpoint=inf.get("endpoint"))
    if isinstance(inf.get("models"), list):
        add("observatory.inference.models", len(inf["models"]), endpoint=inf.get("endpoint"))

    for agent in _dicts(snap.get("agents")):
        aid = agent.get("id")
        usage = _dict(agent.get("usage"))
        for t in TOKEN_TYPES:
            add("observatory.agent.tokens", usage.get(f"{t}_tokens"), agent=aid, type=t)
        add("observatory.agent.sessions", usage.get("sessions"), agent=aid)
        for m in _dicts(agent.get("models")):
            for t in TOKEN_TYPES:
                add("observatory.agent.model.tokens", m.get(f"{t}_tokens"), agent=aid, model=m.get("model"), type=t)
        plan = _dict(agent.get("plan"))
        for lim in _dicts(plan.get("limits")):
            add("observatory.agent.plan.used", lim.get("used_percent"), agent=aid, plan=plan.get("name"), limit=lim.get("label"))

    skills = _dict(snap.get("skills"))
    if isinstance(skills.get("repository"), list):
        add("observatory.skills.repository", len(skills["repository"]))
    for entry in _dicts(skills.get("agents")):
        add("observatory.skills.installed", entry.get("installed_count"), agent=entry.get("agent"))
        add("observatory.skills.enabled", entry.get("enabled_count"), agent=entry.get("agent"))
    return out


# 프로브는 정제된 집계만 쓰지만, 원문성 키가 섞여 들어와도 메모리·DB에 남기지 않는다(방어적 제거).
PRIVATE_KEYS = {"prompt", "prompts", "user_prompt", "tool_input", "tool_parameters", "tool_content", "content",
                "messages", "transcript", "transcript_path", "email", "user_email", "account_email"}


def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def telemetry(snap):
    """에이전트별 수집 방식. 현재 값은 모두 프로브 브리지이며, native OTel 수신은 설계 단계라 아직 없다."""
    out = {}
    for a in _dicts(_dict(snap).get("agents")):
        usage_ok = num(_dict(a.get("usage")).get("total_tokens")) is not None
        quota_ok = bool(_dicts(_dict(a.get("plan")).get("limits")))
        out[a.get("id")] = {"usage": "bridge" if usage_ok else "unsupported", "usage_source": a.get("source"),
                            "quota": "bridge" if quota_ok else "unsupported",
                            "quota_source": _dict(a.get("plan")).get("source")}
    return out


# native OTel(collector allowlist 통과분) → Prometheus. 에이전트 → (토큰 지표 increase 질의, 마지막 수신 시각 질의)
# 표본 시각 = collector 수신 시각(exporter send_timestamps). exporter가 5분 뒤 시계열을 내리므로
# 즉시 질의 대신 window 전체에서 가장 늦은 표본 시각을 찾는다(1분 단위 하위 질의라 최대 1분 늦게 보임).
NATIVE_QUERIES = {
    "claude": ('sum by (model, type) (increase(claude_code_token_usage_tokens_total[{w}]))',
               'max(max_over_time(timestamp(claude_code_token_usage_tokens_total)[{w}:1m]))'),
    "codex": ('sum by (model, token_type) (increase(codex_turn_token_usage_sum[{w}]))',
              'max(max_over_time(timestamp(codex_turn_token_usage_count)[{w}:1m]))'),
}


def native_usage(prom_url, window="24h", fetch=None):
    """최근 window 동안 native counter 증가분과 마지막 수신 시각. bridge 세션 누적과는 기간이 달라 대체·합산하지 않는다.
    증가분이 0인 시계열(합성 시험·오래된 값)은 제외한다. Prometheus가 없으면 None.
    한계: increase()는 시계열의 첫 표본을 0부터 세지 않으므로 처음(또는 5분 넘게 쉬고 다시) 받은 값은 빠질 수 있다."""
    if not prom_url:
        return None
    fetch = fetch or (lambda q: json.load(urllib.request.urlopen(
        f"{prom_url}/api/v1/query?" + urllib.parse.urlencode({"query": q}), timeout=2)))
    out = {}
    try:
        for agent, (usage_q, seen_q) in NATIVE_QUERIES.items():
            tokens = {}
            for r in fetch(usage_q.format(w=window))["data"]["result"]:
                value = num(float(r["value"][1]))
                if value:
                    m = r["metric"]
                    tokens.setdefault(m.get("model", "unknown"), {})[m.get("type") or m.get("token_type") or "unknown"] = value
            seen = fetch(seen_q.format(w=window))["data"]["result"]
            last = datetime.fromtimestamp(float(seen[0]["value"][1]), timezone.utc).isoformat() if seen else None
            if tokens or last:
                out[agent] = {"window": window, "tokens": tokens, "last_received_at": last,
                              "source": "native OTel → collector allowlist → Prometheus"}
    except Exception:  # Prometheus 장애는 native 표시만 비우고 앱은 계속 동작
        return None
    return out


def compact(snap):
    """DB 이력용 사본: 수백 KB인 에이전트별 스킬 목록을 빼고 개수만 남긴다."""
    skills = _dict(snap.get("skills"))
    if not skills:
        return snap
    agents = [{k: v for k, v in e.items() if k != "skills"} for e in _dicts(skills.get("agents"))]
    return {**snap, "skills": {**skills, "agents": agents, "compacted": True}}


def history_point(collected_at, snap):
    """그래프·이력 표에 필요한 값만 추린다."""
    hw = _dict(snap.get("hardware"))
    inf = _dict(hw.get("inference"))
    return {
        "collected_at": collected_at,
        "cpu_percent": num(hw.get("cpu_percent")),
        "memory_used_percent": num(hw.get("memory_used_percent")),
        "inference_reachable": inf.get("reachable") if isinstance(inf.get("reachable"), bool) else None,
        "gpu": [{k: (gpu.get(k) if k == "name" else num(gpu.get(k)))
                 for k in ("name", "utilization_percent", "temperature_c", "power_watts", "memory_used_bytes")}
                for gpu in _dicts(hw.get("gpu"))],
        "agents": {a.get("id"): num(_dict(a.get("usage")).get("total_tokens")) for a in _dicts(snap.get("agents"))},
        "errors": len(snap["errors"]) if isinstance(snap.get("errors"), list) else None,
    }


BUCKET_SECONDS = 300
GAUGES = ("cpu_percent", "memory_used_percent")
GPU_GAUGES = ("utilization_percent", "temperature_c", "power_watts", "memory_used_bytes")


def bucket_start(ts):
    epoch = int(ts.timestamp()) // BUCKET_SECONDS * BUCKET_SECONDS
    return datetime.fromtimestamp(epoch, timezone.utc)


def aggregate_points(points):
    """원본 Point 목록(시간순) → 5분 집계 Point. 게이지는 평균(+min/max/last/n/unknown),
    누적 토큰·도달 여부는 마지막 관측값. 누적값을 더하지 않고, 전부 null이면 null로 둔다."""
    stats, n = {}, len(points)

    def gauge(path, values):
        known = [v for v in values if v is not None]
        stats[path] = {"min": min(known) if known else None, "max": max(known) if known else None,
                       "last": known[-1] if known else None, "n": n, "unknown": n - len(known)}
        return sum(known) / len(known) if known else None

    def last(values):
        known = [v for v in values if v is not None]
        return known[-1] if known else None

    out = {"collected_at": points[0]["collected_at"], "samples": n}
    for key in GAUGES:
        out[key] = gauge(key, [p[key] for p in points])
    out["inference_reachable"] = last([p["inference_reachable"] for p in points])
    gpus = max((len(p["gpu"]) for p in points), default=0)
    out["gpu"] = []
    for i in range(gpus):
        rows = [p["gpu"][i] if i < len(p["gpu"]) else {} for p in points]
        g = {"name": last([r.get("name") for r in rows])}
        for key in GPU_GAUGES:
            g[key] = gauge(f"gpu.{i}.{key}", [r.get(key) for r in rows])
        out["gpu"].append(g)
    ids = {k for p in points for k in p["agents"]}
    out["agents"] = {k: last([p["agents"].get(k) for p in points]) for k in sorted(ids, key=str)}
    errors = [p["errors"] for p in points if p["errors"] is not None]
    out["errors"] = max(errors) if errors else None
    out["stats"] = stats
    return out


class Monitor:
    def __init__(self, snapshot_path, db_path, stale_seconds=180, raw_hours=24, agg_days=30,
                 raw_max_rows=10000, agg_max_rows=10000):
        self.snapshot_path = Path(snapshot_path)
        self.stale_seconds = stale_seconds
        self.raw_hours, self.agg_days = raw_hours, agg_days
        self.raw_max_rows, self.agg_max_rows = raw_max_rows, agg_max_rows
        self.lock = threading.Lock()
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        # 삭제한 공간을 돌려받도록 incremental auto_vacuum. 기존 DB는 한 번 VACUUM해야 설정이 적용된다.
        if self.db.execute("PRAGMA auto_vacuum").fetchone()[0] != 2:
            self.db.execute("PRAGMA auto_vacuum=INCREMENTAL")
            self.db.execute("VACUUM")
        self.db.execute("PRAGMA journal_mode=WAL")
        # collected_at UNIQUE: 같은 스냅샷을 여러 번 읽어도 한 행만 남는다.
        self.db.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY,
            collected_at TEXT NOT NULL UNIQUE,
            ingested_at TEXT NOT NULL,
            body TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS agg_5m (
            bucket_start TEXT PRIMARY KEY,
            samples INTEGER NOT NULL,
            point TEXT NOT NULL)""")
        self.db.commit()
        self.latest, self.source, self.error, self._mtime = None, None, None, None
        self._space_at = None
        self.prom_url = None  # main()에서 PROMETHEUS_URL로 설정
        self._native = (None, None)  # (조회 시각, 결과) 60초 캐시
        with self.lock:
            self.maintain()  # 기존 DB 마이그레이션: 과거 원본을 집계하고 보존 기간 밖 원본을 정리
        row = self.db.execute("SELECT body FROM snapshots ORDER BY collected_at DESC LIMIT 1").fetchone()
        if row:
            self.latest, self.source = json.loads(row[0]), "history"

    def poll(self):
        """스냅샷 파일이 바뀌었으면 읽어 저장한다. 새 행이 추가되면 True."""
        with tracer.start_as_current_span("snapshot.poll") as span:
            try:
                mtime = self.snapshot_path.stat().st_mtime_ns
            except FileNotFoundError:
                span.set_attribute("snapshot.present", False)
                return False
            if mtime == self._mtime:
                return False
            try:
                # NaN/Infinity 리터럴은 미확인(null)으로 읽어 API가 항상 유효한 JSON을 내도록 한다.
                snap = json.loads(self.snapshot_path.read_text(encoding="utf-8"), parse_constant=lambda _: None)
                if not isinstance(snap, dict):
                    raise ValueError("최상위 값이 객체가 아님")
                snap = scrub(snap)
                collected = parse_ts(snap.get("collected_at"))
                if collected is None:
                    raise ValueError("collected_at 누락 또는 형식 오류")
            except (OSError, ValueError) as exc:
                # 쓰는 도중이거나 손상된 파일: 이전 정상 스냅샷을 유지하고 다음 주기에 다시 읽는다.
                self.error = f"스냅샷을 읽지 못함: {exc}"
                span.set_attribute("snapshot.error", self.error)
                return False
            self._mtime = mtime
            key = collected.isoformat()
            with self.lock:
                self.latest, self.source, self.error = snap, "file", None
                added = self.db.execute(
                    "INSERT OR IGNORE INTO snapshots (collected_at, ingested_at, body) VALUES (?, ?, ?)",
                    (key, datetime.now(timezone.utc).isoformat(), json.dumps(compact(snap), ensure_ascii=False)),
                ).rowcount == 1
                if added:
                    self.maintain(dirty=(bucket_start(collected).isoformat(),))
                self.db.commit()
            span.set_attribute("snapshot.added", added)
            return added

    def maintain(self, now=None, dirty=()):
        """완료된 5분 버킷 집계 → 보존 기간·건수 상한 정리 → (1시간마다) WAL·여유 공간 정리. 호출자가 lock을 잡는다.
        집계는 원본에서 다시 계산하는 REPLACE라 몇 번 실행해도 결과가 같다(멱등)."""
        now = now or datetime.now(timezone.utc)
        current = bucket_start(now).isoformat()
        last_agg = self.db.execute("SELECT MAX(bucket_start) FROM agg_5m").fetchone()[0]
        # 마지막 집계 버킷 이후 + 이번에 원본이 들어온 버킷(dirty, 늦게 도착한 과거 스냅샷)만 다시 본다.
        rows = self.db.execute("SELECT collected_at, body FROM snapshots WHERE collected_at >= ? AND collected_at < ? "
                               "ORDER BY collected_at", (last_agg or "", current)).fetchall()
        for key in dirty:
            if key < (last_agg or "") and key < current:
                end = (parse_ts(key) + timedelta(seconds=BUCKET_SECONDS)).isoformat()
                rows += self.db.execute("SELECT collected_at, body FROM snapshots WHERE collected_at >= ? "
                                        "AND collected_at < ? ORDER BY collected_at", (key, end)).fetchall()
        buckets = {}
        for collected_at, body in rows:
            key = bucket_start(parse_ts(collected_at)).isoformat()
            buckets.setdefault(key, []).append(history_point(collected_at, json.loads(body)))
        for key, points in buckets.items():
            have = self.db.execute("SELECT samples FROM agg_5m WHERE bucket_start = ?", (key,)).fetchone()
            if have is None or len(points) > have[0]:  # 원본 일부가 지워진 버킷은 다시 계산하지 않는다
                point = {**aggregate_points(points), "collected_at": key}
                self.db.execute("INSERT OR REPLACE INTO agg_5m (bucket_start, samples, point) VALUES (?, ?, ?)",
                                (key, len(points), json.dumps(point, ensure_ascii=False)))
        # 원본은 버킷 경계에서 잘라 버킷이 반쯤 지워지지 않게 한다.
        raw_cut = bucket_start(now - timedelta(hours=self.raw_hours)).isoformat()
        self.db.execute("DELETE FROM snapshots WHERE collected_at < ?", (raw_cut,))
        self.db.execute("DELETE FROM snapshots WHERE id NOT IN "
                        "(SELECT id FROM snapshots ORDER BY collected_at DESC LIMIT ?)", (self.raw_max_rows,))
        agg_cut = (now - timedelta(days=self.agg_days)).isoformat()
        self.db.execute("DELETE FROM agg_5m WHERE bucket_start < ?", (agg_cut,))
        self.db.execute("DELETE FROM agg_5m WHERE bucket_start NOT IN "
                        "(SELECT bucket_start FROM agg_5m ORDER BY bucket_start DESC LIMIT ?)", (self.agg_max_rows,))
        self.db.commit()
        if self._space_at is None or now - self._space_at >= timedelta(hours=1):
            self._space_at = now
            self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.db.execute("PRAGMA incremental_vacuum")

    def close(self):
        with self.lock:
            self.db.close()

    def count(self, table="snapshots"):
        with self.lock:
            return self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # table은 코드 상수만

    def state(self):
        snap = self.latest
        collected = parse_ts(snap.get("collected_at")) if snap else None
        age = (datetime.now(timezone.utc) - collected).total_seconds() if collected else None
        if snap is None:
            status = "waiting"
        elif age is None or age > self.stale_seconds:
            status = "stale"
        else:
            status = "ok"
        tel = telemetry(snap) if snap else {}
        native = self.native()
        for agent, info in (native or {}).items():
            # 세션 누적(usage)은 계속 bridge. native는 기간이 다른 별도 관측으로만 붙인다.
            tel.setdefault(agent, {})["native_usage"] = info
        return {"status": status, "source": self.source, "age_seconds": age,
                "stale_after_seconds": self.stale_seconds, "error": self.error, "snapshot": snap,
                "telemetry": tel}

    def native(self):
        at, cached = self._native
        now = time.monotonic()
        if at is None or now - at > 60:
            cached = native_usage(self.prom_url)
            self._native = (now, cached)
        return cached

    def history(self, hours=24, limit=500):
        """24시간 이하는 정제 스냅샷 원본, 그보다 길면 5분 집계를 돌려준다."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        raw = hours <= self.raw_hours
        with self.lock:
            if raw:
                rows = self.db.execute("SELECT collected_at, body FROM snapshots WHERE collected_at >= ? "
                                       "ORDER BY collected_at", (cutoff,)).fetchall()
            else:
                rows = self.db.execute("SELECT bucket_start, point FROM agg_5m WHERE bucket_start >= ? "
                                       "ORDER BY bucket_start", (cutoff,)).fetchall()
            total = self.db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
            agg_total = self.db.execute("SELECT COUNT(*) FROM agg_5m").fetchone()[0]
        step = max(1, -(-len(rows) // limit))  # 올림 나눗셈으로 limit 이하로 균등 추출
        picked = rows[::step]
        if rows and picked[-1] is not rows[-1]:
            picked[-1] = rows[-1]  # 최신 값은 항상 포함
        points = ([history_point(c, json.loads(b)) for c, b in picked] if raw
                  else [json.loads(b) for _, b in picked])
        return {"hours": hours, "resolution": "raw" if raw else "5m", "matched": len(rows), "step": step,
                "stored_total": total, "agg_total": agg_total,
                "raw_retention_hours": self.raw_hours, "agg_retention_days": self.agg_days,
                "agg_bucket_seconds": BUCKET_SECONDS, "raw_max_rows": self.raw_max_rows,
                "agg_max_rows": self.agg_max_rows,
                # FE 호환용(이전 필드명): 집계 보존 일수와 원본 건수 상한
                "retention_days": self.agg_days, "max_rows": self.raw_max_rows,
                "points": points}


def check_url(url):
    if not url:
        return "not_configured"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            return "ok" if resp.status < 400 else f"http_{resp.status}"
    except Exception:  # 연결 거부·타임아웃 등은 모두 '응답 없음'으로 보고한다
        return "unreachable"


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentObservatory"
    sys_version = ""

    def do_GET(self):
        url = urlparse(self.path)
        route = url.path if url.path in ("/", "/health", "/api/snapshot", "/api/history") else (
            "/static/*" if url.path.startswith("/static/") else "other")
        with tracer.start_as_current_span(f"GET {route}", kind=trace.SpanKind.SERVER) as span:
            span.set_attribute("http.request.method", "GET")
            span.set_attribute("http.route", route)
            code = self.route(url)
            span.set_attribute("http.response.status_code", code)

    def route(self, url):
        mon = self.server.monitor
        name = "index.html" if url.path == "/" else url.path.removeprefix("/static/")
        ctype = STATIC_FILES.get(name) if url.path.startswith("/static/") else ("text/html" if url.path == "/" else None)
        if ctype:  # 허용 목록만 제공해 경로 탈출을 막는다
            try:
                return self.send(200, (STATIC / name).read_bytes(), ctype + "; charset=utf-8")
            except FileNotFoundError:
                return self.json(404, {"error": f"정적 파일 없음: {name}"})
        if url.path == "/health":
            state = mon.state()
            return self.json(200, {"status": "ok", "snapshot": state["status"], "snapshot_age_seconds": state["age_seconds"],
                                   "snapshot_error": state["error"], "db_rows": mon.count(), "agg_rows": mon.count("agg_5m"),
                                   "collector": check_url(os.environ.get("COLLECTOR_HEALTH_URL")),
                                   "prometheus": check_url(os.environ.get("PROMETHEUS_HEALTH_URL"))})
        if url.path == "/api/snapshot":
            return self.json(200, mon.state())
        if url.path == "/api/history":
            q = parse_qs(url.query)
            try:
                hours = float(q.get("hours", ["24"])[0])
                limit = int(q.get("limit", ["500"])[0])
                if not math.isfinite(hours):
                    raise ValueError
            except ValueError:
                return self.json(400, {"error": "hours/limit는 유한한 숫자여야 합니다"})
            return self.json(200, mon.history(min(max(hours, 0.1), 24 * 365), min(max(limit, 10), 5000)))
        return self.json(404, {"error": "not found"})

    def json(self, code, payload):
        return self.send(code, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)
        return code

    def log_message(self, *args):  # UI 폴링으로 접근 로그가 넘치지 않게 끈다
        pass


def setup_otel(monitor):
    """OTLP HTTP로 지표·트레이스를 내보낸다. 엔드포인트 등은 표준 OTEL_* 환경변수를 따른다."""
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.metrics import Observation
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": os.environ.get("OTEL_SERVICE_NAME", "agent-observatory")})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
    meter_provider = MeterProvider(resource=resource, metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())])
    metrics.set_meter_provider(meter_provider)
    register_gauges(meter_provider.get_meter("agent-observatory"), monitor, Observation)
    return tracer_provider, meter_provider


def register_gauges(meter, monitor, Observation):
    def callback(name):
        def observe(_options):
            return [Observation(v, a) for n, v, a in metric_points(monitor.latest) if n == name]
        return observe

    for name, (unit, desc) in METRICS.items():
        meter.create_observable_gauge(name, callbacks=[callback(name)], unit=unit, description=desc)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    env = os.environ
    monitor = Monitor(env.get("SNAPSHOT_PATH", "/data/host/snapshot.json"),
                      env.get("DB_PATH", "/data/db/monitor.sqlite3"),
                      stale_seconds=float(env.get("STALE_SECONDS", "180")),
                      raw_hours=float(env.get("RAW_RETENTION_HOURS", "24")),
                      agg_days=float(env.get("AGG_RETENTION_DAYS", "30")),
                      raw_max_rows=int(env.get("RAW_MAX_ROWS", "10000")),
                      agg_max_rows=int(env.get("AGG_MAX_ROWS", "10000")))
    monitor.prom_url = env.get("PROMETHEUS_URL")
    providers = setup_otel(monitor) if env.get("OTEL_SDK_DISABLED", "").lower() != "true" else ()
    interval = float(env.get("POLL_SECONDS", "15"))

    def loop():
        while True:
            try:
                monitor.poll()
            except Exception:
                log.exception("스냅샷 폴링 실패")
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True).start()
    server = ThreadingHTTPServer((env.get("HOST", "127.0.0.1"), int(env.get("PORT", "8787"))), Handler)
    server.monitor = monitor
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    log.info("listening on %s:%s, snapshot=%s", *server.server_address[:2], monitor.snapshot_path)
    try:
        server.serve_forever()
    finally:
        for provider in providers:
            provider.shutdown()


if __name__ == "__main__":
    main()
