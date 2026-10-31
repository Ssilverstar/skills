"""QA-001: server.py API·DB·OTel 계약 테스트 (CONTRACT-001 / api.md 기준).

규칙: 표준 unittest만, 합성 픽스처(fixtures/)만 사용, 임시 디렉터리에 스냅샷·DB 생성,
HTTP는 127.0.0.1 임시 포트만 사용한다. 실패 테스트는 지우지 않고 defects에 재현법을 남긴다.
"""

import copy
import http.client
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "app"))

import server  # noqa: E402  (테스트 대상, 읽기 전용)

FIXTURES = Path(__file__).with_name("fixtures")


def now_utc():
    return datetime.now(timezone.utc)


def iso(offset_seconds):
    return (now_utc() + timedelta(seconds=offset_seconds)).isoformat()


def fixture_snapshot(collected_at):
    snap = json.loads((FIXTURES / "snapshot_full.json").read_text(encoding="utf-8"))
    snap["collected_at"] = collected_at
    return snap


class TempMonitorCase(unittest.TestCase):
    """tempdir에 스냅샷·DB를 만들고 mtime을 결정적으로 바꿔 재작성을 보증한다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qa001-")
        self.addCleanup(self.tmp.cleanup)
        self.snap_path = Path(self.tmp.name) / "snapshot.json"
        self.db_path = Path(self.tmp.name) / "monitor.sqlite3"
        self._mt_ns = time.time_ns()

    def write_snapshot(self, payload):
        self.snap_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        # mtime 기반 변경 감지라 파일 재작성 후 os.utime으로 mtime을 반드시 바꾼다.
        self._mt_ns += 1_000_000
        os.utime(self.snap_path, ns=(self._mt_ns, self._mt_ns))

    def make_monitor(self, **kwargs):
        monitor = server.Monitor(self.snap_path, self.db_path, **kwargs)
        self.addCleanup(monitor.close)  # 통합 시 추가: SQLite 연결을 명시적으로 닫아 ResourceWarning 제거
        return monitor


def db_collected_ats(db_path):
    import sqlite3

    con = sqlite3.connect(db_path)
    try:
        return [r[0] for r in con.execute("SELECT collected_at FROM snapshots ORDER BY collected_at")]
    finally:
        con.close()


def db_bodies(db_path):
    import sqlite3

    con = sqlite3.connect(db_path)
    try:
        return [json.loads(r[0]) for r in con.execute("SELECT body FROM snapshots ORDER BY collected_at")]
    finally:
        con.close()


# ---------------------------------------------------------------- TC1 waiting

class TC1WaitingTest(TempMonitorCase):
    def setUp(self):
        super().setUp()
        for var in ("COLLECTOR_HEALTH_URL", "PROMETHEUS_HEALTH_URL"):
            saved = os.environ.pop(var, None)
            self.addCleanup(lambda v=saved, k=var: os.environ.setdefault(k, v) if v is not None else None)
        self.mon = self.make_monitor()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.httpd.monitor = self.mon
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.stop_http)
        self.port = self.httpd.server_address[1]

    def stop_http(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read()
        finally:
            conn.close()

    def test_no_snapshot_state_is_waiting(self):
        self.assertFalse(self.mon.poll(), "스냅샷 파일이 없으면 poll은 False")
        state = self.mon.state()
        self.assertEqual(state["status"], "waiting")
        self.assertIsNone(state["snapshot"])
        self.assertIsNone(state["source"])

    def test_api_snapshot_matches_state(self):
        status, headers, body = self.get("/api/snapshot")
        self.assertEqual(status, 200)
        self.assertTrue(headers.get("content-type", "").startswith("application/json"))
        payload = json.loads(body)
        state = self.mon.state()
        for key in ("status", "source", "snapshot", "stale_after_seconds", "error"):
            self.assertEqual(payload[key], state[key])
        self.assertEqual(payload["status"], "waiting")
        self.assertIsNone(payload["snapshot"])

    def test_health_waiting_zero_rows(self):
        status, _, body = self.get("/health")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["snapshot"], "waiting")
        self.assertEqual(payload["db_rows"], 0)
        for key in ("snapshot_age_seconds", "snapshot_error", "collector", "prometheus"):
            self.assertIn(key, payload)
        self.assertIn(payload["collector"], {"ok", "unreachable", "not_configured"})
        self.assertIn(payload["prometheus"], {"ok", "unreachable", "not_configured"})


# ------------------------------------------------------- TC2 collect & dedup

class TC2CollectDedupTest(TempMonitorCase):
    def test_first_poll_ok_and_dedup(self):
        at = iso(0)  # 고정 문자열: 재작성 시 collected_at이 흔들리면 중복 테스트가 성립하지 않음
        self.write_snapshot(fixture_snapshot(at))
        mon = self.make_monitor()
        self.assertTrue(mon.poll(), "정상 스냅샷 첫 poll은 True")
        self.assertEqual(mon.state()["status"], "ok")
        self.assertEqual(mon.state()["source"], "file")
        self.assertEqual(mon.count(), 1)

        # 같은 파일 재폴링(mtime 변화 없음): 행 추가 없음
        self.assertFalse(mon.poll())
        self.assertEqual(mon.count(), 1)

        # 같은 collected_at 재작성(mtime 변경): UNIQUE로 행 추가 없음
        self.write_snapshot(fixture_snapshot(at))
        self.assertFalse(mon.poll(), "같은 collected_at 재폴링은 새 행이면 안 됨")
        self.assertEqual(mon.count(), 1)
        self.assertIsNone(mon.state()["error"])


# ------------------------------------------------------------ TC3 compaction

class TC3CompactionTest(TempMonitorCase):
    def test_db_is_compacted_memory_is_full(self):
        at1 = iso(-120)
        self.write_snapshot(fixture_snapshot(at1))
        mon = self.make_monitor()
        self.assertTrue(mon.poll())

        at2 = iso(-60)
        self.write_snapshot(fixture_snapshot(at2))
        self.assertTrue(mon.poll(), "collected_at이 다르면 새 행")
        self.assertEqual(mon.count(), 2)

        bodies = db_bodies(self.db_path)
        self.assertEqual(len(bodies), 2)
        for body in bodies:
            self.assertIs(body["skills"]["compacted"], True, "DB 본문은 압축본(compactsed=true)")
            for entry in body["skills"]["agents"]:
                self.assertNotIn("skills", entry, "DB 압축본에는 skills 목록이 없어야 한다")
                self.assertIn("installed_count", entry, "개수는 유지")

        latest = mon.state()["snapshot"]
        self.assertNotIn("compacted", latest.get("skills", {}), "메모리 latest는 전체본")
        self.assertEqual(len(latest["skills"]["agents"][0]["skills"]), 2)


# ----------------------------------------------------------- TC4 restart

class TC4RestartHistoryTest(TempMonitorCase):
    def test_restart_restores_history(self):
        self.write_snapshot(fixture_snapshot(iso(-60)))
        mon = self.make_monitor()
        self.assertTrue(mon.poll())

        mon2 = self.make_monitor()  # 재시작: 같은 DB로 새 Monitor
        state = mon2.state()
        self.assertEqual(state["source"], "history")
        self.assertEqual(state["status"], "ok")
        self.assertIs(state["snapshot"]["skills"]["compacted"], True)
        for entry in state["snapshot"]["skills"]["agents"]:
            self.assertNotIn("skills", entry, "복원본은 압축본이어야 한다")


# --------------------------------------------------------------- TC5 stale

class TC5StaleTest(TempMonitorCase):
    def test_old_collected_at_is_stale(self):
        self.write_snapshot(fixture_snapshot(iso(-240)))  # stale_seconds 기본 180 초과
        mon = self.make_monitor()
        self.assertTrue(mon.poll())
        state = mon.state()
        self.assertEqual(state["status"], "stale")
        self.assertIsNotNone(state["snapshot"], "stale이어도 마지막 값은 유지")
        self.assertGreater(state["age_seconds"], mon.stale_seconds)


# ------------------------------------------------------------ TC6 corrupt

class TC6CorruptTest(TempMonitorCase):
    def test_corrupt_inputs_keep_previous_latest(self):
        good_at = iso(-60)
        self.write_snapshot(fixture_snapshot(good_at))
        mon = self.make_monitor()
        self.assertTrue(mon.poll())
        before = mon.state()["snapshot"]

        cases = [
            "{ broken json",                                  # 손상 JSON
            json.dumps({"schema_version": 1}),                # collected_at 누락
            json.dumps([1, 2, 3]),                            # 최상위 배열
            json.dumps({"collected_at": "not-a-date"}),       # collected_at 형식 오류
        ]
        for raw in cases:
            self.snap_path.write_text(raw, encoding="utf-8")
            self._mt_ns += 1_000_000
            os.utime(self.snap_path, ns=(self._mt_ns, self._mt_ns))
            self.assertFalse(mon.poll(), f"손상 입력은 poll False: {raw[:20]}")
            self.assertIsNotNone(mon.error, f"손상 입력에 error 메시지 필요: {raw[:20]}")
            self.assertIs(mon.state()["snapshot"], before, "이전 latest 유지")
        self.assertEqual(mon.count(), 1, "손상 입력으로 행이 추가되면 안 됨")

        # 복구: 이후 정상 스냅샷은 다시 수집되고 error가 해제된다.
        self.write_snapshot(fixture_snapshot(iso(-30)))
        self.assertTrue(mon.poll())
        self.assertIsNone(mon.state()["error"])


# ------------------------------------------------------------- TC7 retention

class TC7RetentionTest(TempMonitorCase):
    # 통합 시 갱신(Claude): 보존 정책 v2(원본 24시간·건수 상한 raw_max_rows, 5분 집계 30일)
    def test_max_rows_prunes_oldest(self):
        mon = self.make_monitor(raw_max_rows=3)
        times = [iso(-60 * m) for m in (100, 80, 60, 40, 20)]
        for at in times:
            self.write_snapshot(fixture_snapshot(at))
            self.assertTrue(mon.poll())
        self.assertEqual(mon.count(), 3)
        kept = set(db_collected_ats(self.db_path))
        self.assertEqual(kept, {parse_key(at) for at in times[-3:]})

    def test_retention_days_prunes_old_snapshots(self):
        mon = self.make_monitor(raw_hours=24)
        self.write_snapshot(fixture_snapshot(iso(-10 * 24 * 3600)))  # 10일 전
        self.assertTrue(mon.poll())
        self.assertEqual(mon.count(), 0, "원본 보존 24시간 초과 행은 삭제")
        self.assertEqual(mon.count("agg_5m"), 1, "삭제 전에 5분 집계로 남음(30일 이내)")
        self.assertIsNotNone(mon.latest, "삭제와 무관하게 메모리 latest는 유지")
        self.write_snapshot(fixture_snapshot(iso(-3600)))  # 1시간 전
        self.assertTrue(mon.poll())
        self.assertEqual(mon.count(), 1)


def parse_key(collected_at):
    from datetime import datetime as dt

    ts = dt.fromisoformat(collected_at)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


# --------------------------------------------------------------- TC8 history

class TC8HistoryTest(TempMonitorCase):
    def setUp(self):
        super().setUp()
        self.at_r4 = iso(-10 * 3600)   # 24h 내, 6h 밖
        self.at_r1 = iso(-2 * 3600)    # 6h 내, cpu 문자열 → null
        self.at_r2 = iso(-1 * 3600)    # 6h 내, cpu None
        self.at_r3 = iso(-10 * 60)     # 최신, cpu 정상
        self.at_r5 = iso(-30 * 3600)   # 24h 밖
        self.at_r6 = iso(-26 * 3600)   # 24h 밖
        rows = [
            (self.at_r5, 12.5),
            (self.at_r4, 12.5),
            (self.at_r1, "12"),
            (self.at_r2, None),
            (self.at_r3, 5.0),
            (self.at_r6, 12.5),
        ]
        self.mon = self.make_monitor()
        # mtime 기반 변경 감지: 쓰고 → poll하고를 교대해야 6개가 모두 수집된다.
        for at, cpu in rows:
            snap = fixture_snapshot(at)
            snap["hardware"]["cpu_percent"] = cpu
            self.write_snapshot(snap)
            self.assertTrue(self.mon.poll())

    def test_hours_filter_and_counts(self):
        h24 = self.mon.history(hours=24, limit=500)
        self.assertEqual(h24["matched"], 4)
        # 통합 시 갱신(Claude): 24시간 밖 원본 2건은 원본에서 지워지고, 완료된 모든 버킷은 5분 집계로 남는다.
        self.assertEqual(h24["stored_total"], 4)
        self.assertEqual(h24["agg_total"], 6, "완료된 버킷 6개 모두 집계(늦게 들어온 26시간 전 r6 포함)")
        self.assertEqual(h24["resolution"], "raw")
        self.assertEqual([p["collected_at"] for p in h24["points"]],
                         [parse_key(a) for a in (self.at_r4, self.at_r1, self.at_r2, self.at_r3)])
        h6 = self.mon.history(hours=6, limit=500)
        self.assertEqual(h6["matched"], 3)

    def test_downsample_keeps_latest_under_limit(self):
        h = self.mon.history(hours=24, limit=3)
        pts = h["points"]
        self.assertLessEqual(len(pts), 3)
        self.assertEqual(pts[-1]["collected_at"], parse_key(self.at_r3), "마지막 점은 항상 최신")

    def test_nulls_stay_null_not_zero(self):
        h = self.mon.history(hours=24, limit=500)
        by_at = {p["collected_at"]: p for p in h["points"]}
        self.assertIsNone(by_at[parse_key(self.at_r2)]["cpu_percent"], "None은 null 유지")
        self.assertIsNone(by_at[parse_key(self.at_r1)]["cpu_percent"], "문자열 숫자는 0이 아니라 null")
        latest = by_at[parse_key(self.at_r3)]
        self.assertIsNone(latest["gpu"][0]["memory_used_bytes"], "GB10 VRAM null 유지")
        self.assertIs(latest["inference_reachable"], True)
        self.assertEqual(latest["cpu_percent"], 5.0)


# ----------------------------------------------------------------- TC9 HTTP

class TC9HttpTest(TempMonitorCase):
    def setUp(self):
        super().setUp()
        for var in ("COLLECTOR_HEALTH_URL", "PROMETHEUS_HEALTH_URL"):
            os.environ.pop(var, None)
        self.write_snapshot(fixture_snapshot(iso(-60)))
        self.mon = self.make_monitor()
        self.assertTrue(self.mon.poll())
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.httpd.monitor = self.mon
        self.httpd.daemon_threads = True
        thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.stop_http)
        self.port = self.httpd.server_address[1]

    def stop_http(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            return resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read()
        finally:
            conn.close()

    def assert_security_headers(self, headers):
        self.assertEqual(headers.get("cache-control"), "no-store")
        csp = headers.get("content-security-policy", "")
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self'", csp)
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")

    def test_static_traversal_and_denied_names_are_404(self):
        for path in ("/static/../server.py", "/static/server.py", "/static/app.css"):
            status, headers, body = self.get(path)
            self.assertEqual(status, 404, path)
            self.assertNotIn(b"def main", body, "소스가 노출되면 안 됨")
            self.assert_security_headers(headers)

    def test_history_bad_hours_is_400(self):
        for path in ("/api/history?hours=x", "/api/history?limit=abc"):
            status, headers, body = self.get(path)
            self.assertEqual(status, 400, path)
            self.assert_security_headers(headers)
            self.assertIn("error", json.loads(body))

    def test_history_ok_shape_and_headers(self):
        status, headers, body = self.get("/api/history?hours=24")
        self.assertEqual(status, 200)
        self.assert_security_headers(headers)
        payload = json.loads(body)
        for key in ("hours", "matched", "stored_total", "step", "retention_days", "max_rows", "points"):
            self.assertIn(key, payload)
        self.assertEqual(payload["matched"], 1)

    def test_headers_on_snapshot_and_404(self):
        for path in ("/api/snapshot", "/health", "/nope"):
            status, headers, _ = self.get(path)
            self.assertIn(status, (200, 404))
            self.assert_security_headers(headers)

    def test_root_serves_index_when_fe_present_else_clean_response(self):
        index = server.STATIC / "index.html"
        if index.exists():  # FE-001 병행 작업: 파일이 있으면 200 검사
            status, headers, body = self.get("/")
            self.assertEqual(status, 200)
            self.assertTrue(headers.get("content-type", "").startswith("text/html"))
            self.assert_security_headers(headers)
        # 파일 유무와 무관하게 서버는 HTTP 응답 자체를 반환해야 한다(연결 끊김 금지).
        try:
            status, _, _ = self.get("/")
        except (http.client.RemoteDisconnected, ConnectionResetError):
            self.fail("static/index.html 부재 시 응답 없이 연결이 끊긴다(defect QA-001-D1)")
        else:
            self.assertIn(status, (200, 404, 503), "index.html 없음은 404/503로 답해야 한다(defect QA-001-D1)")

    def test_static_appjs_when_fe_present(self):
        appjs = server.STATIC / "app.js"
        if not appjs.exists():  # 계약상 파일이 있을 때만 200 검사
            self.skipTest("FE-001 진행 중: app/static/app.js 아직 없음")
        status, headers, _ = self.get("/static/app.js")
        self.assertEqual(status, 200)
        self.assertTrue(headers.get("content-type", "").startswith("text/javascript"))
        self.assert_security_headers(headers)


# ---------------------------------------------------------- TC10 metric_points

TC10_SNAP = {
    "collected_at": "2026-10-31T00:00:00+00:00",
    "errors": ["e1"],
    "hardware": {
        "hostname": "qa-host",
        "cpu_percent": True,          # bool → 미출력
        "memory_used_bytes": None,     # None → 미출력
        "memory_used_percent": "72",   # 문자열 → 미출력
        "gpu": [{"name": "GB10", "utilization_percent": 37.5, "temperature_c": 54,
                 "power_watts": 14.62, "memory_used_bytes": None}],
        "inference": {"endpoint": "127.0.0.1:1", "reachable": True, "models": ["m-a", "m-b"]},
    },
    "agents": [{
        "id": "qa",
        "usage": {"input_tokens": 100, "cached_input_tokens": 40, "cache_write_input_tokens": 10,
                  "output_tokens": 50, "reasoning_tokens": 20, "total_tokens": 150, "sessions": 3},
        "models": [
            {"model": "m1", "input_tokens": 60, "total_tokens": 80, "sessions": 2},
            {"model": "m2", "input_tokens": 40, "total_tokens": 50, "sessions": 1},
        ],
        "plan": {"name": "syntheticplan", "limits": [{"label": "weekly", "used_percent": 7}]},
    }],
    "skills": {"repository": [{"name": "a"}],
               "agents": [{"agent": "codex", "installed_count": 5, "enabled_count": None}]},
}


class TC10MetricPointsTest(unittest.TestCase):
    def setUp(self):
        self.points = server.metric_points(TC10_SNAP, now=now_utc())

    def by_name(self, name):
        return [(attrs, value) for n, value, attrs in self.points if n == name]

    def test_unknown_bool_string_values_not_emitted(self):
        self.assertEqual(self.by_name("observatory.host.cpu.utilization"), [], "bool True는 미출력")
        self.assertEqual(self.by_name("observatory.host.memory.used"), [], "None은 미출력")
        self.assertEqual(self.by_name("observatory.host.memory.utilization"), [], "문자열 '72'는 미출력")
        self.assertEqual(self.by_name("observatory.gpu.memory.used"), [], "null VRAM은 미출력(0 아님)")
        self.assertEqual(self.by_name("observatory.skills.enabled"), [], "enabled_count null은 미출력")

    def test_inference_reachable_bool_to_one_zero(self):
        pts = self.by_name("observatory.inference.reachable")
        self.assertEqual([v for _, v in pts], [1], "reachable True → 1")
        snap2 = copy.deepcopy(TC10_SNAP)
        snap2["hardware"]["inference"]["reachable"] = False
        pts2 = [(n, v) for n, v, _ in server.metric_points(snap2) if n == "observatory.inference.reachable"]
        self.assertEqual([v for _, v in pts2], [0], "reachable False → 0")
        snap3 = copy.deepcopy(TC10_SNAP)
        snap3["hardware"]["inference"]["reachable"] = "true"
        pts3 = [p for p in server.metric_points(snap3) if p[0] == "observatory.inference.reachable"]
        self.assertEqual(pts3, [], "bool이 아니면 미출력")
        models = self.by_name("observatory.inference.models")
        self.assertEqual([v for _, v in models], [2])

    def test_token_types_including_cache_write_are_separate(self):
        usage_values = {"input": 100, "cached_input": 40, "cache_write_input": 10,
                        "output": 50, "reasoning": 20, "total": 150}
        for t, expected in usage_values.items():
            self.assertIn(t, server.TOKEN_TYPES, f"TOKEN_TYPES에 {t} 필요")
            pts = [(a, v) for a, v in self.by_name("observatory.agent.tokens") if a.get("type") == t]
            self.assertEqual([v for _, v in pts], [expected], f"agent.tokens type={t}")

    def test_usage_and_models_are_not_summed(self):
        totals = [v for a, v in self.by_name("observatory.agent.tokens") if a.get("type") == "total"]
        self.assertEqual(totals, [150], "usage.total 그대로")
        model_totals = {a.get("model"): v for a, v in self.by_name("observatory.agent.model.tokens")
                        if a.get("type") == "total"}
        self.assertEqual(model_totals, {"m1": 80, "m2": 50})
        emitted = {v for _, v, _ in self.points}
        self.assertNotIn(130, emitted, "models 합산(80+50)을 별도 지표로 내보내면 안 됨")
        self.assertNotIn(280, emitted, "usage+models(150+130) 합산 금지")


# -------------------------------------------------------------- TC11 OTel

class TC11OtelGaugeTest(TempMonitorCase):
    def test_register_gauges_with_in_memory_reader(self):
        from opentelemetry.metrics import Observation
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        self.write_snapshot(fixture_snapshot(iso(-60)))
        mon = self.make_monitor()
        self.assertTrue(mon.poll())

        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        server.register_gauges(provider.get_meter("qa001"), mon, Observation)
        data = reader.get_metrics_data()

        points = {}
        for rm in data.resource_metrics:
            for sm in rm.scope_metrics:
                for metric in sm.metrics:
                    for dp in metric.data.data_points:
                        points.setdefault(metric.name, []).append((dict(dp.attributes), dp.value))

        gpu = points.get("observatory.gpu.utilization", [])
        self.assertEqual([(a.get("gpu_name"), v) for a, v in gpu],
                         [("NVIDIA GB10 (synthetic)", 37.5)], "gpu.utilization 값 일치")
        self.assertNotIn("observatory.gpu.memory.used", points, "null 지표는 내보내지 않음")

        tokens = {(a.get("agent"), a.get("type")): v for a, v in points.get("observatory.agent.tokens", [])}
        self.assertEqual(tokens.get(("codex", "total")), 1500)
        self.assertEqual(tokens.get(("codex", "cache_write_input")), 50)
        model_tokens = {(a.get("agent"), a.get("model"), a.get("type")): v
                        for a, v in points.get("observatory.agent.model.tokens", [])}
        self.assertEqual(model_tokens.get(("codex", "synthetic-model-a", "total")), 900)
        emitted_values = {v for _, vs in points.items() for _, v in vs}
        self.assertNotIn(3000, emitted_values, "usage(1500)+models(900+600) 합산 금지")
        plan = [(a, v) for a, v in points.get("observatory.agent.plan.used", []) if a.get("agent") == "codex"]
        self.assertEqual([v for _, v in plan], [7])


if __name__ == "__main__":
    unittest.main()
