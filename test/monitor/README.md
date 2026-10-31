# Agent Observatory

DGX Spark 한 대에서 에이전트 사용량·구독 한도, GPU·추론 서버, 스킬 설치·활성·호출 증거를 보여 주는 로컬 모니터링 웹 서버입니다. 한국어 UI이며 외부로 데이터를 보내지 않습니다.

```text
host_probe.py (호스트, 읽기 전용, 표준 라이브러리)  ──►  test/.local/monitor/snapshot.json
                                                              │ (읽기 전용 마운트 /data/host)
app (Python stdlib HTTP + OTel SDK) ── SQLite(named volume monitor-db)
   │ OTLP HTTP (지표 + 트레이스)
otel-collector 0.164.0 ──► :8889 Prometheus exporter ◄── prometheus v3.15.1 (127.0.0.1:9090)
```

| 파일 | 소유 |
|---|---|
| `host_probe.py`, `test_host_probe.py`, `install_host_service.py`, `claude_statusline.py`, `install_claude_statusline.py`, `agy_statusline.py`, `install_agy_statusline.py`, `e2e_check.py`, `measure_run.py` | Codex |
| `app/server.py`, `Dockerfile`, `compose.yaml`, `otel-collector.yaml`, `prometheus.yml`, `contracts/` | Claude(통합) |
| `app/static/*`, `tests/ui/*` | FE-001~004 작업자(Gemini). 완료 후 `style.css` 1줄은 Claude가 통합 수정 |
| `tests/test_server.py`, `tests/fixtures/*` | QA-001 작업자(Qwen). 완료 후 연결 정리(addCleanup) 1곳은 Claude가 통합 수정 |
| `tests/test_integration.py` | Claude(통합 회귀) |

API·의미 규칙은 [contracts/api.md](contracts/api.md)에 있습니다.

## 실행

호스트 수집기는 systemd **사용자** 서비스 `agent-observatory-probe.service`로 독립 실행합니다(15초 주기). 컨테이너와 별개로 시작·중지합니다.

```bash
cd test/monitor
python3 install_host_service.py --apply                    # 수집기 사용자 서비스 설치·활성화(최초 1회)
systemctl --user status agent-observatory-probe.service    # 상태 확인
docker compose up -d --build                               # 앱·collector·Prometheus
```

- 수집기는 사용자 로그인 시 기동합니다. linger를 켜지 않았으므로 재부팅 후 로그인 전에는 수집이 멈추고 UI는 `stale`을 표시합니다.
- 일회성 수동 수집: `python3 host_probe.py --once`

### 구독 한도 관측용 상태줄(선택, 최초 1회)

두 스크립트 모두 인자 없이 실행하면 변경 미리보기만 하고, `--apply`일 때 `statusLine` 항목만 바꿉니다. 기존 설정은 처음 한 번 `settings.json.before-observatory`로 백업하고 다른 설정은 유지합니다.

```bash
python3 install_claude_statusline.py --apply   # ~/.claude/settings.json: 기존 상태줄 출력을 유지하는 래퍼(claude_statusline.py)가 rate_limits만 기록
python3 install_agy_statusline.py --apply      # ~/.gemini/antigravity-cli/settings.json: 기본 UI 위에 쌓는(stack_with_default) agy_statusline.py
```

- 기록 위치: `test/.local/monitor/claude-plan.json`, `test/.local/monitor/antigravity-sessions/*.json`(세션 해시·모델·토큰 합계만).
- 이미 실행 중인 세션은 새 설정을 읽지 않을 수 있습니다. Antigravity는 세션에서 `/statusline`을 입력해 `Statusline on.`을 확인합니다(토글이므로 다시 입력하면 꺼짐). Claude는 새 세션 또는 상태줄 갱신 시 반영됩니다.
- 되돌리기: 백업 파일 `settings.json.before-observatory`를 원래 이름으로 복원합니다.

- UI: <http://127.0.0.1:8787> · `/health` · `/api/snapshot` · `/api/history?hours=24`
- Prometheus: <http://127.0.0.1:9090> (예: `observatory_gpu_utilization_percent`)
- 스냅샷 디렉터리 `test/.local/monitor`가 없으면 compose가 실패합니다(`create_host_path: false`). 수집기를 먼저 한 번 실행하세요.
- 포트·바인딩: `MONITOR_PORT`, `MONITOR_BIND`(기본 127.0.0.1), `PROMETHEUS_PORT`. 컨테이너는 `MONITOR_UID/GID`(기본 1000)로 실행되어 0600 스냅샷도 읽습니다.

## 같은 공유기(LAN)에서 접속

기본 `compose.yaml`은 `127.0.0.1`에만 엽니다. LAN의 다른 PC(예: Windows 브라우저)에서 보려면 **앱(UI·API)만** 이 호스트의 LAN IP에 추가로 여는 override를 씁니다. Prometheus(9090)와 collector는 계속 외부에 열지 않습니다.

```bash
cd test/monitor
cp lan.env.example ../.local/monitor-lan.env          # 최초 1회. test/.local/은 git 제외
# ../.local/monitor-lan.env 의 MONITOR_LAN_IP를 이 호스트 주소로 수정 (확인: ip -4 -o addr show)
docker compose -f compose.yaml -f compose.lan.yaml --env-file ../.local/monitor-lan.env up -d
```

- 결과 바인딩: `127.0.0.1:8787`과 `<LAN IP>:8787` 두 곳. `0.0.0.0`으로 열지 않으므로 Docker 브리지 등 다른 인터페이스에는 노출되지 않습니다.
- 접속 주소: `http://<LAN IP>:8787` (이 환경: `http://192.168.0.65:8787`).
- 이후 `stop`/`start`/`down`도 같은 `-f … --env-file …` 인자를 붙여야 LAN 바인딩이 유지됩니다. 인자 없이 `up -d`를 다시 하면 localhost 전용으로 돌아갑니다(되돌리기 방법이기도 함).
- LAN IP가 DHCP로 바뀌면 컨테이너가 `cannot assign requested address`로 시작하지 못합니다. 공유기에서 이 호스트에 주소를 예약하거나 env 파일을 고칩니다.
- **인증이 없습니다.** 같은 LAN의 누구나 에이전트 사용량·한도·스킬 경로·호스트 정보를 읽을 수 있습니다(읽기 전용 GET만 제공). 신뢰하는 집 LAN에서만 쓰고, 공유기 포트포워딩·방화벽 전체 해제는 하지 않습니다.
- 호스트 방화벽: firewalld 비활성, `ufw status` = inactive(Codex 독립 확인, 2026-10-31). Docker가 게시한 포트는 Docker의 iptables 규칙으로 처리됩니다. ufw를 켤 경우 Docker 게시 포트는 ufw 규칙을 우회할 수 있으므로 LAN 범위 제한이 필요하면 `DOCKER-USER` 체인 규칙을 별도로 검토합니다.
- 검증 범위(2026-10-31): 이 호스트에서 `http://192.168.0.65:8787/health` 200, `127.0.0.1:8787` 200, `192.168.0.65:9090` 연결 불가를 확인했습니다. **이는 호스트 자기 접속 결과이며, Windows 등 다른 기기에서의 실제 접속은 별도 확인이 필요합니다.**

## 중지·재개·초기화

```bash
systemctl --user stop agent-observatory-probe.service    # 수집 중지(UI는 마지막 값을 stale로 표시)
systemctl --user start agent-observatory-probe.service   # 수집 재개
docker compose stop          # 중지(데이터 유지)
docker compose start         # 재개 — 재시작 직후 화면은 DB의 마지막 압축본(이력 복원)으로 시작
docker compose down          # 컨테이너 제거(볼륨 유지)
docker compose down -v       # SQLite·Prometheus 볼륨까지 삭제
```

## 저장과 보존

DB에 쌓이는 "원본(raw)"은 대화 원문이 아니라 **호스트 프로브가 정제한 집계 스냅샷**(토큰 합계·한도 사용률·GPU 수치·스킬 개수 등)입니다. 프롬프트·도구 입력·응답 본문은 수집·저장하지 않으며, 앱도 `prompt`·`tool_input`·`content`·`email` 등 원문성 키가 섞여 들어오면 메모리·DB에 넣기 전에 지웁니다.

| 계층 | 해상도 | 보존 | 상한 | 설정 |
|---|---|---|---|---|
| 정제 스냅샷 원본 | 수집 주기(약 15초) | 24시간 | 10,000행 | `RAW_RETENTION_HOURS`, `RAW_MAX_ROWS` |
| 5분 집계 | 5분 버킷 | 30일 | 10,000행 | `AGG_RETENTION_DAYS`, `AGG_MAX_ROWS` |
| Prometheus | 15초 스크레이프 | 15일 | 2GB | compose `--storage.tsdb.retention.*` |
| 컨테이너 로그 | — | — | 서비스당 10MB×3 | compose `x-logging` |

- 원본: `POLL_SECONDS`(15초)마다 파일 mtime이 바뀔 때만 읽고 `collected_at` UNIQUE로 같은 스냅샷은 한 행만 저장. DB에는 에이전트별 스킬 목록(약 360KB)을 뺀 압축본(약 6KB)만 두고 최신 전체본은 메모리에 둡니다.
- 5분 집계: 끝난 버킷만, 원본에서 다시 계산(멱등). 게이지(CPU·메모리·GPU 사용률/온도/전력/메모리)는 **평균**과 `min/max/last/n/unknown`, 누적 토큰과 도달 여부는 **버킷 마지막 관측값**(합산 안 함). 표본이 모두 null이면 null. 원본은 버킷 경계에서 지워 버킷이 반쯤 남지 않습니다.
- `/api/history`: 24시간 이하는 `resolution: "raw"`, 그보다 길면 `resolution: "5m"`. UI는 해상도와 집계 방식을 표시합니다.
- 공간: SQLite WAL, incremental auto_vacuum. 1시간마다 `wal_checkpoint(TRUNCATE)`와 `incremental_vacuum`. 기존 DB는 앱 시작 시 한 번 VACUUM·집계 이관·24시간 밖 원본 정리를 자동 수행합니다(되돌릴 수 없으므로 필요하면 시작 전 볼륨을 백업).
- `STALE_SECONDS`(180초)보다 오래된 스냅샷은 `stale`로 표시합니다.

## 수집 방식 구분

`/api/snapshot`의 `telemetry`와 UI 배지는 에이전트별 사용량·한도 신호가 **브리지**(호스트 프로브가 로컬 기록·statusLine·계정 API에서 변환), **네이티브 OTel**(에이전트가 공식 OTel로 직접 전송), **미지원**(값 없음) 중 무엇인지 보여 줍니다. 세션 누적 사용량은 모두 브리지입니다. 네이티브 OTel은 collector가 **호스트 loopback `127.0.0.1:4318`**(LAN 미게시)로 받아 지표 이름·라벨 allowlist(`model`, `type`, `token_type`)만 통과시키고, 로그·스팬은 받기만 하고 폐기합니다. 앱은 이를 `telemetry[agent].native_usage`(최근 24시간 증가분과 마지막 수신 시각)로 **별도 표시**하며, 기간이 다른 브리지 누적값과 더하거나 대체하지 않습니다. 세션 식별자를 지운 뒤에도 여러 세션이 덮어쓰지 않도록 `cumulative_to_delta` → 라벨 정리 → `delta_to_cumulative` 순서로 같은 model/type 시계열에 누적하며, 표본 시각은 collector 수신 시각입니다(`send_timestamps`). 증가분은 Prometheus `increase()` 외삽 추정이고 첫 표본(단발 실행, 5분 넘게 쉰 뒤 첫 값)은 빠질 수 있습니다. 파이프라인 검증: `python3 tests/native_pipeline_check.py`(도커, 임시 포트 14320/18889). 설계·검증·권장 에이전트 설정은 [native-otel-design.md](native-otel-design.md).

## OpenTelemetry

- 지표: 최신 스냅샷의 값을 observable gauge로 내보냅니다(`OTEL_METRIC_EXPORT_INTERVAL` 15초). **값이 없으면(null) 시계열을 만들지 않습니다** — 0으로 채우지 않습니다.
- 트레이스: HTTP 요청과 `snapshot.poll` 스팬. collector의 `span_metrics` 커넥터가 `traces_span_metrics_calls_total`·`traces_span_metrics_duration_milliseconds_*`로 바꿔 Prometheus에서 전달을 확인할 수 있고, 원본 스팬은 `docker compose logs otel-collector`(debug)에 보입니다. 별도 트레이스 저장소는 없습니다.

| Prometheus 지표 | 주요 라벨 | 주의 |
|---|---|---|
| `observatory_gpu_{utilization_percent,temperature_celsius,power_watts}` | `gpu_name`, `gpu_index` | GB10 전용 메모리 지표는 보고되지 않아 없음 |
| `observatory_host_memory_{used_bytes,utilization_percent}`, `observatory_host_cpu_utilization_percent` | `host` | 호스트(통합) 메모리. CPU는 프로브가 줄 때만 |
| `observatory_inference_{reachable_ratio,models}` | `endpoint` | |
| `observatory_agent_tokens` | `agent`, `type` | **type 간 합산 금지**: input⊇cached_input·cache_write_input, output⊇reasoning |
| `observatory_agent_model_tokens` | `agent`, `model`, `type` | agent_tokens와 합산 금지(같은 양의 모델별 분해) |
| `observatory_agent_sessions`, `observatory_agent_plan_used_percent` | `agent`, `plan`, `limit` | 플랜 사용률은 공식/관측값만 |
| `observatory_skills_{installed,enabled,repository}` | `agent` | |
| `observatory_snapshot_{age_seconds,errors}` | | |

토큰 값은 로컬 이력의 **누적 스냅샷**이므로 `rate()`나 시계열 간 `sum`으로 사용량을 만들지 않습니다.

앱을 재시작하면 OTel `service.instance.id`가 바뀌어 collector의 Prometheus exporter에 이전 인스턴스 시계열이 만료(기본 5분)될 때까지 함께 남습니다. 이 구간에는 같은 `agent`·`limit`에 값이 둘 이상 보일 수 있으며, `max by`로 접으면 한도 초기화 직후 이전의 높은 값이 최대 5분 남으므로 **최신값의 대체가 아닙니다**. 최신값은 UI·`/api/snapshot`(관측 시각 포함)을 기준으로 보고, 인스턴스 라벨 고정과 관측 시각 기준 신선도 판정은 [미구현·개선 계획](../monitor-gaps.md)에 정리했습니다.

## 수집 제약

- 컨테이너에는 `test/.local/monitor`만 읽기 전용으로 마운트합니다. 홈 디렉터리, 공급자 로그, Docker 소켓, 자격증명은 마운트하지 않습니다. 앱 컨테이너는 읽기 전용 루트, `cap_drop: ALL`, `no-new-privileges`로 실행합니다.
- GPU·추론 서버·에이전트 사용량은 호스트 프로브(사용자 서비스)가 읽습니다. 프로브가 멈추면 180초 뒤 UI는 `stale`을 표시합니다.
- 플랜 한도는 공식 계정 API·공식 CLI 조회 또는 기록된 UI 관측값만 표시합니다(과거 관측은 이력으로 표시).
  - Codex: 계정 API 실시간 한도. Claude: 공식 statusLine 콜백의 `rate_limits`를 기존 상태줄 출력을 유지하는 래퍼로 기록한 **마지막 관측값**(Claude Code 세션이 상태줄을 갱신할 때만 새로워짐, `test/.local/monitor/claude-plan.json`).
  - Antigravity: 공식 `agy --output-format json --print /usage`(모델 호출 없음)로 약 5분마다 실시간 한도를 조회합니다. 토큰은 공식 statusLine 콜백이 관측한 세션 누적값이며, 그 콜백 연결 이전 이력과 모델별 분해는 없습니다.
  - 로컬 토큰 합계를 플랜 사용률로 환산하지 않습니다.
- 스킬 `invocations`는 호출 **요청** 증거이며 성공 여부가 아닙니다. 계측되지 않은 값은 "미계측"이지 "미사용"이 아닙니다.

## 테스트

```bash
cd test
python3 -m venv .local/monitor-venv && .local/monitor-venv/bin/pip install -r monitor/requirements.txt
.local/monitor-venv/bin/python -m unittest discover -s monitor/tests -p 'test_*.py' -v   # API·DB·OTel
node --test monitor/tests/ui/*.test.js                                                 # UI 순수 함수·XSS·정렬·i18n·축 계산
node monitor/tests/ui/index.js                                                         # 같은 하위 테스트를 직접 실행해 개별 결과 확인
```
