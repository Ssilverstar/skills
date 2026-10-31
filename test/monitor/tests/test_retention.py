"""보존 정책 v2 회귀(Claude 소유): 원본 24시간·5분 집계 30일, 멱등 집계, null, 마이그레이션, 프라이버시."""

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import server  # noqa: E402

NOW = datetime(2026, 10, 31, 12, 2, 30, tzinfo=timezone.utc)  # 현재 버킷 12:00~12:05


def snap(at, cpu=10.0, gpu=50.0, total=1000, reachable=True):
    return {"collected_at": at.isoformat(),
            "hardware": {"cpu_percent": cpu, "memory_used_percent": 40.0,
                         "gpu": [{"name": "GB10", "utilization_percent": gpu, "temperature_c": 60,
                                  "power_watts": 20.0, "memory_used_bytes": None}],
                         "inference": {"reachable": reachable}},
            "agents": [{"id": "codex", "usage": {"total_tokens": total}, "plan": {"limits": [{"used_percent": 5}]}},
                       {"id": "antigravity", "usage": {"total_tokens": None}, "plan": {"limits": []}}],
            "errors": []}


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.db_path = self.dir / "db.sqlite3"

    def monitor(self, **kw):
        mon = server.Monitor(self.dir / "missing.json", self.db_path, **kw)
        self.addCleanup(mon.close)
        return mon

    def insert(self, mon, *snaps):
        with mon.lock:
            for s in snaps:
                mon.db.execute("INSERT INTO snapshots (collected_at, ingested_at, body) VALUES (?, ?, ?)",
                               (s["collected_at"], s["collected_at"], json.dumps(s)))
            mon.db.commit()

    def agg(self, mon):
        with mon.lock:
            return {k: (n, json.loads(p)) for k, n, p in
                    mon.db.execute("SELECT bucket_start, samples, point FROM agg_5m ORDER BY bucket_start")}


class AggregatePointsTest(unittest.TestCase):
    def test_gauges_average_and_cumulative_last_without_sum(self):
        pts = [server.history_point(s["collected_at"], s) for s in (
            snap(NOW, cpu=10, total=100), snap(NOW, cpu=None, total=None, reachable=False), snap(NOW, cpu=30, total=300))]
        out = server.aggregate_points(pts)
        self.assertEqual(out["cpu_percent"], 20)
        self.assertEqual(out["stats"]["cpu_percent"], {"min": 10, "max": 30, "last": 30, "n": 3, "unknown": 1})
        self.assertEqual(out["agents"]["codex"], 300, "누적 토큰은 마지막 관측값(합산 600 아님)")
        self.assertIsNone(out["agents"]["antigravity"], "미확인은 0이 아니라 null")
        self.assertFalse(out["inference_reachable"] is None)
        self.assertEqual(out["samples"], 3)

    def test_all_null_gauge_stays_null(self):
        pts = [server.history_point(s["collected_at"], s) for s in (snap(NOW, cpu=None), snap(NOW, cpu=None))]
        out = server.aggregate_points(pts)
        self.assertIsNone(out["cpu_percent"])
        self.assertEqual(out["stats"]["cpu_percent"]["unknown"], 2)
        self.assertIsNone(out["gpu"][0]["memory_used_bytes"], "GB10 N/A 메모리는 집계 후에도 null")


class MaintainTest(Base):
    def test_only_complete_buckets_and_idempotent(self):
        mon = self.monitor()
        t = NOW.replace(minute=0, second=0)
        self.insert(mon, snap(t - timedelta(minutes=4)), snap(t - timedelta(minutes=1)), snap(t + timedelta(minutes=1)))
        with mon.lock:
            mon.maintain(now=NOW)
        first = self.agg(mon)
        self.assertEqual(list(first), [(t - timedelta(minutes=5)).isoformat()], "진행 중인 현재 버킷은 집계하지 않음")
        self.assertEqual(first[(t - timedelta(minutes=5)).isoformat()][0], 2)
        with mon.lock:
            mon.maintain(now=NOW)
            mon.maintain(now=NOW)
        self.assertEqual(self.agg(mon), first, "여러 번 실행해도 결과 동일")

    def test_raw_cut_on_bucket_boundary_and_row_cap(self):
        mon = self.monitor(raw_hours=24, raw_max_rows=3)
        cut = server.bucket_start(NOW - timedelta(hours=24))
        self.insert(mon, snap(cut - timedelta(seconds=1)), snap(cut), snap(cut + timedelta(seconds=1)),
                    snap(NOW - timedelta(minutes=30)), snap(NOW - timedelta(minutes=20)))
        with mon.lock:
            mon.maintain(now=NOW)
            kept = [r[0] for r in mon.db.execute("SELECT collected_at FROM snapshots ORDER BY collected_at")]
        self.assertNotIn((cut - timedelta(seconds=1)).isoformat(), kept, "경계 직전 버킷 원본은 삭제")
        self.assertEqual(len(kept), 3, "건수 상한")
        self.assertEqual(kept[-1], (NOW - timedelta(minutes=20)).isoformat(), "최신 원본 유지")
        self.assertIn((cut - timedelta(minutes=5)).isoformat(), self.agg(mon), "삭제 전 집계로 보존")

    def test_partial_bucket_not_overwritten_after_cap(self):
        mon = self.monitor(raw_max_rows=10)
        t = NOW - timedelta(hours=1)
        b = server.bucket_start(t)
        self.insert(mon, snap(b + timedelta(seconds=10)), snap(b + timedelta(seconds=40)), snap(b + timedelta(seconds=70)))
        with mon.lock:
            mon.maintain(now=NOW)
            mon.db.execute("DELETE FROM snapshots WHERE collected_at = ?", ((b + timedelta(seconds=10)).isoformat(),))
            mon.maintain(now=NOW, dirty=(b.isoformat(),))
        self.assertEqual(self.agg(mon)[b.isoformat()][0], 3, "원본 일부 삭제 후 표본 수가 줄어든 재계산 금지")

    def test_agg_retention_and_cap(self):
        mon = self.monitor(agg_days=30, agg_max_rows=2)
        old = server.bucket_start(NOW - timedelta(days=31))
        with mon.lock:
            for i, key in enumerate([old, NOW - timedelta(hours=3), NOW - timedelta(hours=2), NOW - timedelta(hours=1)]):
                k = server.bucket_start(key).isoformat()
                mon.db.execute("INSERT INTO agg_5m VALUES (?, 1, '{}')", (k,))
            mon.maintain(now=NOW)
        keys = list(self.agg(mon))
        self.assertEqual(len(keys), 2)
        self.assertNotIn(old.isoformat(), keys)
        self.assertEqual(keys[-1], server.bucket_start(NOW - timedelta(hours=1)).isoformat())

    def test_history_resolution_switch(self):
        mon = self.monitor()
        self.insert(mon, snap(datetime.now(timezone.utc) - timedelta(hours=30)),
                    snap(datetime.now(timezone.utc) - timedelta(minutes=30)))
        with mon.lock:
            mon.maintain()
        raw, agg = mon.history(hours=24), mon.history(hours=24 * 7)
        self.assertEqual((raw["resolution"], agg["resolution"]), ("raw", "5m"))
        self.assertEqual(raw["matched"], 1)
        self.assertEqual(agg["matched"], 2)
        self.assertIn("stats", agg["points"][0])
        self.assertEqual(agg["agg_bucket_seconds"], 300)


class MigrationTest(Base):
    def test_existing_v1_db_is_migrated(self):
        db = sqlite3.connect(self.db_path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE snapshots (id INTEGER PRIMARY KEY, collected_at TEXT NOT NULL UNIQUE, "
                   "ingested_at TEXT NOT NULL, body TEXT NOT NULL)")
        base = datetime.now(timezone.utc)
        for h in (72, 48, 30, 2, 1):
            s = snap(base - timedelta(hours=h))
            db.execute("INSERT INTO snapshots (collected_at, ingested_at, body) VALUES (?, ?, ?)",
                       (s["collected_at"], s["collected_at"], json.dumps(s)))
        db.commit()
        db.close()
        mon = self.monitor()
        with mon.lock:
            self.assertEqual(mon.db.execute("PRAGMA auto_vacuum").fetchone()[0], 2)
        self.assertEqual(mon.count(), 2, "24시간 밖 원본 3건 삭제")
        self.assertEqual(mon.count("agg_5m"), 5, "삭제 전 모두 5분 집계로 이관")
        self.assertEqual(mon.source, "history")


class PrivacyAndTelemetryTest(Base):
    def test_private_keys_never_stored(self):
        s = snap(datetime.now(timezone.utc))
        s["agents"][0].update(prompt="SECRET-PROMPT", email="a@example.com",
                              notes=[{"tool_input": {"cmd": "SECRET-TOOL"}, "content": "SECRET-CONTENT", "ok": 1}])
        path = self.dir / "snapshot.json"
        path.write_text(json.dumps(s))
        mon = server.Monitor(path, self.db_path)
        self.addCleanup(mon.close)
        self.assertTrue(mon.poll())
        with mon.lock:
            body = mon.db.execute("SELECT body FROM snapshots").fetchone()[0]
        for text in (body, json.dumps(mon.latest)):
            for secret in ("SECRET-PROMPT", "a@example.com", "SECRET-TOOL", "SECRET-CONTENT"):
                self.assertNotIn(secret, text)
        self.assertEqual(mon.latest["agents"][0]["notes"], [{"ok": 1}])

    def test_telemetry_modes_bridge_and_unsupported(self):
        t = server.telemetry(snap(NOW))
        self.assertEqual((t["codex"]["usage"], t["codex"]["quota"]), ("bridge", "bridge"))
        self.assertEqual((t["antigravity"]["usage"], t["antigravity"]["quota"]), ("unsupported", "unsupported"))


class McpPassThroughTest(Base):
    def test_mcp_block_survives_scrub_and_compact(self):
        mcp = {"common_servers": ["git", "github", "chrome-devtools"], "observed_at": "2026-10-31T08:00:00+00:00",
               "agents": [{"agent": "codex", "common_configured_count": 3, "servers": [
                   {"name": "github", "scope": "common", "configured": True, "enabled": True, "status": "connected",
                    "tool_count": 40, "checked_at": "2026-10-31T08:00:00+00:00", "note": "tools/list ok"}]}]}
        s = {**snap(NOW), "mcp": mcp}
        self.assertEqual(server.scrub(s)["mcp"], mcp, "MCP 계약 필드는 원문성 키가 아니므로 그대로 통과")
        self.assertEqual(server.compact(s)["mcp"], mcp, "이력 압축본도 MCP 요약 유지")


class NativeUsageTest(Base):
    def test_native_maps_labels_drops_zero_and_keeps_bridge(self):
        seen_queries = []

        def fetch(q):
            if "timestamp(" in q:
                seen_queries.append(q)
            if "timestamp(claude" in q:
                return {"data": {"result": [{"value": [0, "1793430000"]}]}}
            if "claude_code_token_usage" in q:
                return {"data": {"result": [{"metric": {"model": "claude-opus-5-5", "type": "input"}, "value": [0, "120"]},
                                            {"metric": {"model": "synthetic", "type": "input"}, "value": [0, "0"]}]}}
            if "codex_turn_token_usage_sum" in q:
                return {"data": {"result": [{"metric": {"model": "gpt-6-astra", "token_type": "output"}, "value": [0, "7"]}]}}
            return {"data": {"result": []}}
        out = server.native_usage("http://prom", fetch=fetch)
        self.assertEqual(out["claude"]["tokens"], {"claude-opus-5-5": {"input": 120.0}}, "증가분 0 시계열 제외")
        self.assertEqual(out["codex"]["tokens"], {"gpt-6-astra": {"output": 7.0}})
        self.assertIsNone(out["codex"]["last_received_at"])
        self.assertEqual(out["claude"]["window"], "24h")
        # 즉시 timestamp()는 마지막 스크랩 시각이거나(5분 뒤엔) 비어 있다. window 전체의 실제 표본 시각을 봐야 한다.
        self.assertTrue(seen_queries and all("[24h:" in q for q in seen_queries), seen_queries)
        mon = self.monitor()
        mon.latest = snap(datetime.now(timezone.utc))
        mon._native = (__import__("time").monotonic(), out)
        tel = mon.state()["telemetry"]
        self.assertEqual(tel["codex"]["usage"], "bridge", "세션 누적은 bridge 유지(native로 대체하지 않음)")
        self.assertEqual(tel["codex"]["native_usage"]["tokens"]["gpt-6-astra"]["output"], 7.0)
        self.assertNotIn("native_usage", tel["antigravity"])

    def test_native_unavailable_returns_none(self):
        def boom(_q):
            raise OSError("down")
        self.assertIsNone(server.native_usage("http://prom", fetch=boom))
        self.assertIsNone(server.native_usage(None))


if __name__ == "__main__":
    unittest.main()
