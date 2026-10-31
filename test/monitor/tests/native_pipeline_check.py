"""native OTel 파이프라인 fixture 검증(도커 필요, unittest 대상 아님).

실제 otel-collector.yaml로 임시 collector를 127.0.0.1:14320(OTLP)/18889(metrics)에 띄우고
세션 식별자만 다른 counter를 보내 최종 Prometheus 노출값을 확인한다.

  python3 tests/native_pipeline_check.py   # 성공 시 exit 0
"""
import json
import pathlib
import re
import subprocess
import time
import urllib.request

CONFIG = pathlib.Path(__file__).resolve().parent.parent / "otel-collector.yaml"
IMAGE = "otel/opentelemetry-collector-contrib:0.164.0"
NAME = "native-pipeline-check"
OTLP, METRICS = "http://127.0.0.1:14320/v1/metrics", "http://127.0.0.1:18889/metrics"
NS = 10**9
CUM, DELTA = 2, 1


def attrs(**kv):
    return [{"key": k.replace("_", "."), "value": {"stringValue": v}} for k, v in kv.items()]


def send(service, metrics):
    body = {"resourceMetrics": [{
        "resource": {"attributes": attrs(service_name=service, session_id=sid, user_email="x@example.invalid")},
        "scopeMetrics": [{"scope": {"name": "fixture", "version": "9.9.9"}, "metrics": [m]}]}
        for sid, m in metrics]}
    req = urllib.request.Request(OTLP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()
    time.sleep(0.3)


def claude(sid, start, ts, value, model, temporality):
    dp = {"startTimeUnixNano": str(start), "timeUnixNano": str(ts), "asDouble": value,
          "attributes": attrs(model=model, type="input", session_id=sid)}
    return sid, {"name": "claude_code.token.usage", "unit": "tokens",
                 "sum": {"aggregationTemporality": temporality, "isMonotonic": True, "dataPoints": [dp]}}


def codex(sid, start, ts, total, count):
    dp = {"startTimeUnixNano": str(start), "timeUnixNano": str(ts), "sum": total, "count": str(count),
          "bucketCounts": [str(count)], "explicitBounds": [],
          "attributes": attrs(model="gpt-fixture", token_type="output", conversation_id=sid)}
    return sid, {"name": "codex.turn.token_usage", "histogram": {"aggregationTemporality": CUM, "dataPoints": [dp]}}


def main():
    subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    subprocess.run(["docker", "run", "-d", "--name", NAME, "-p", "127.0.0.1:14320:4320", "-p", "127.0.0.1:18889:8889",
                    "-v", f"{CONFIG}:/etc/otelcol-contrib/config.yaml:ro", IMAGE], check=True, capture_output=True)
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(METRICS, timeout=1)
                break
            except OSError:
                time.sleep(0.25)
        t = time.time_ns()
        sent_at = time.time()
        # cumulative 2세션(s2가 먼저 시작했지만 나중에 송신) + s1 재시작: 30 + 7 + 4 = 41
        send("claude-code", [claude("s1", t + NS, t + 2 * NS, 10, "cum", CUM)])
        send("claude-code", [claude("s2", t, t + 3 * NS, 5, "cum", CUM)])
        send("claude-code", [claude("s1", t + NS, t + 4 * NS, 30, "cum", CUM)])
        send("claude-code", [claude("s2", t, t + 5 * NS, 7, "cum", CUM)])
        send("claude-code", [claude("s1", t + 6 * NS, t + 7 * NS, 4, "cum", CUM)])
        # delta 2세션(Claude 기본), d2는 송신측 시각이 과거 + 한 요청에 두 세션: 3 + 2 + 1 + 4 + 5 = 15
        send("claude-code", [claude("d1", t + 2 * NS, t + 8 * NS, 3, "delta", DELTA)])
        send("claude-code", [claude("d2", t, t + NS, 2, "delta", DELTA)])
        send("claude-code", [claude("d1", t + 8 * NS, t + 9 * NS, 1, "delta", DELTA)])
        send("claude-code", [claude("d3", t + 9 * NS, t + 10 * NS, 4, "delta", DELTA),
                             claude("d4", t + 9 * NS, t + 10 * NS, 5, "delta", DELTA)])
        # Codex cumulative histogram 2세션: sum 250 + 40, count 2 + 1
        send("codex_exec", [codex("c1", t, t + NS, 100, 1)])
        send("codex_exec", [codex("c2", t, t + 2 * NS, 40, 1)])
        send("codex_exec", [codex("c1", t, t + 3 * NS, 250, 2)])
        # Codex App/TUI 백엔드(codex-app-server)는 송신자(job)만 다른 별도 시계열: count 1, sum 10. 앱은 model·token_type으로 합산
        send("codex-app-server", [codex("a1", t, t + 4 * NS, 10, 1)])
        # 허용 목록 밖 지표는 같은 송신자여도 버린다
        send("codex-app-server", [("a1", {"name": "codex.process.start", "sum": {"aggregationTemporality": DELTA,
              "isMonotonic": True, "dataPoints": [{"timeUnixNano": str(t + 5 * NS), "asDouble": 1,
              "attributes": attrs(model="blocked")}]}})])
        # 허용 목록 밖 송신자는 버린다
        send("unknown-agent", [claude("z", t, t + NS, 99, "blocked", DELTA)])
        time.sleep(1)
        text = urllib.request.urlopen(METRICS, timeout=5).read().decode()
    finally:
        logs = subprocess.run(["docker", "logs", NAME], capture_output=True, text=True)
        subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    samples = {}
    for line in text.splitlines():
        m = re.match(r'^(\w+)\{(.*)\} (\S+) (\d+)$', line)
        if m:
            labels = dict(re.findall(r'(\w+)="([^"]*)"', m[2]))
            samples[(m[1], labels.get("model"), labels.get("job"))] = (float(m[3]), int(m[4]) / 1000, labels)
    expect = {("claude_code_token_usage_tokens_total", "cum", "claude-code"): 41,
              ("claude_code_token_usage_tokens_total", "delta", "claude-code"): 15,
              ("codex_turn_token_usage_sum", "gpt-fixture", "codex_exec"): 290,
              ("codex_turn_token_usage_count", "gpt-fixture", "codex_exec"): 3,
              ("codex_turn_token_usage_sum", "gpt-fixture", "codex-app-server"): 10,
              ("codex_turn_token_usage_count", "gpt-fixture", "codex-app-server"): 1}
    for key, want in expect.items():
        value, ts, labels = samples[key]
        assert value == want, (key, value, want)
        assert sent_at - 1 <= ts <= time.time() + 1, ("표본 시각은 collector 수신 시각", key, ts, sent_at)
        extra = {k for k, v in labels.items() if v} - {"job", "model", "type", "token_type", "le"}
        assert not extra, ("허용 라벨 밖", key, extra)
    assert not any(k[1] == "blocked" for k in samples), "허용 목록 밖 송신자·지표"
    assert "codex_process_start" not in text, "허용 목록 밖 Codex 지표"
    for leak in ("session", "conversation", "user", "example.invalid"):
        assert leak not in text, ("식별자 노출", leak)
    bad = [l for l in logs.stderr.splitlines() if re.search(r"\t(warn|error)\t", l)]
    assert not bad, bad
    print(json.dumps({"/".join(k): v[0] for k, v in samples.items()}, ensure_ascii=False))
    print("native pipeline check: ok")


if __name__ == "__main__":
    main()
