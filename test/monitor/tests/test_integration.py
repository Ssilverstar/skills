"""통합 회귀(Claude 소유): 비유한 숫자, 정적 파일 부재, 엄격한 JSON 응답."""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import server  # noqa: E402

SNAP = ('{"collected_at":"2026-10-31T00:00:00+00:00",'
        '"hardware":{"cpu_percent":NaN,"gpu":[{"utilization_percent":Infinity,"temperature_c":50}]}}')


def strict(_constant):
    raise AssertionError("응답 JSON에 NaN/Infinity가 있음")


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        snap = Path(tmp.name, "snapshot.json")
        snap.write_text(SNAP)
        self.monitor = server.Monitor(snap, Path(tmp.name, "db.sqlite3"))
        self.addCleanup(self.monitor.close)
        self.assertTrue(self.monitor.poll())
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        httpd.monitor = self.monitor
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        self.base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode()

    def test_nonfinite_numbers_become_unknown(self):
        hw = self.monitor.latest["hardware"]
        self.assertIsNone(hw["cpu_percent"])
        self.assertIsNone(server.num(float("nan")))
        self.assertIsNone(server.num(float("inf")))
        names = {n for n, _, _ in server.metric_points(self.monitor.latest)}
        self.assertNotIn("observatory.host.cpu.utilization", names)
        self.assertIn("observatory.gpu.temperature", names)
        self.assertNotIn("observatory.gpu.utilization", names)

    def test_api_responses_are_strict_json(self):
        for path in ("/api/snapshot", "/api/history?hours=1", "/health"):
            code, body = self.get(path)
            self.assertEqual(code, 200, path)
            json.loads(body, parse_constant=strict)

    def test_history_rejects_nonfinite_hours(self):
        for hours in ("nan", "NaN", "inf", "-inf", "1e999", "x"):
            self.assertEqual(self.get(f"/api/history?hours={hours}")[0], 400, hours)
        self.assertEqual(self.get("/api/history?hours=24")[0], 200)

    def test_missing_static_file_is_404_not_empty_response(self):
        original = server.STATIC
        server.STATIC = Path(tempfile.mkdtemp())
        self.addCleanup(setattr, server, "STATIC", original)
        self.assertEqual(self.get("/")[0], 404)
        self.assertEqual(self.get("/static/app.js")[0], 404)


if __name__ == "__main__":
    unittest.main()
