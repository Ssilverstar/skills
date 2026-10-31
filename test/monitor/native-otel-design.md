# Native OTel 수신 설계 (초안, 미적용)

작성: Claude(통합 담당), 2026-10-31. 상태: **설계만**. 기존 `otel-collector.yaml`은 Codex의 native 설정 감사와 조율하기 전까지 수정하지 않는다.
에이전트별 공식 native OTel 지원 여부·설정은 Codex 감사 결과를 따른다. 이 문서에서 확인한 공식 근거는 Claude Code뿐이다([monitoring-usage](https://code.claude.com/docs/en/monitoring-usage)); 나머지는 **[미확인]**.

## 목표와 원칙

- 에이전트가 공식 OTel로 보내는 **지표·이벤트를 설정으로 취합**하되, 대화 원문(프롬프트·도구 입력·응답 본문)은 받더라도 **저장하지 않는다**.
- 같은 신호를 native와 bridge(프로브)가 함께 주면 **native만 표시**하고 더하지 않는다(`api.md` v2 `telemetry`).
- 외부 노출 없음: 수신 포트는 **loopback 전용**.

## 경로

```text
에이전트(호스트 프로세스) ──OTLP/HTTP──► 127.0.0.1:4318 (collector, loopback 게시)
   metrics ─► filter(지표 이름 allowlist) ─► attributes(라벨 allowlist, 식별자 삭제) ─► prometheus exporter
   logs    ─► filter(이벤트 이름 allowlist) ─► transform(속성 allowlist만 남김, skill_name만 추출)
           ─► count connector(logs→metrics) ─► prometheus exporter          (logs 자체는 어디에도 저장·출력 안 함)
앱 ─► Prometheus HTTP API(컨테이너 내부)로 native 지표 조회 ─► telemetry.mode = native, 해당 신호의 bridge 값은 숨김
```

1. **수신**: compose에서 collector `127.0.0.1:4318:4318`만 게시(LAN override에도 추가하지 않음). 앱용 내부 수신은 그대로.
2. **지표 allowlist**(예, Claude): `claude_code.token.usage`(type=input·output·cacheRead·cacheCreation, model), `claude_code.cost.usage`(API 정가 추정), `claude_code.session.count`. 그 외 지표는 drop.
3. **라벨 정리**: `user.id`, `user.email`, `user.account_uuid`, `organization.id`, `session.id`, `prompt.id` 등 식별·고카디널리티 속성 삭제. 남기는 라벨: `model`, `type`, `service.name`(에이전트 구분), `skill.name`(cost에 있을 때).
4. **이벤트 allowlist**: `claude_code.tool_result`(남길 속성: `tool_name`, `success`, `duration_ms`, `error_type`, `decision_type`), `claude_code.tool_decision`(`tool_name`, `decision`, `source`). `tool_parameters`가 있으면 **`skill_name`만 추출**하고 원 속성은 삭제. 이벤트 본문·`error` 메시지·`tool_input`은 삭제.
   - `skill_name`은 공식 문서상 `OTEL_LOG_TOOL_DETAILS=1`일 때만 온다. 이 설정은 도구 입력도 함께 내보내므로 위 삭제 단계가 **필수 전제**이고, 켤지는 사용자 결정.
5. **집계**: count connector로 `observatory_native_tool_results_total{agent, tool_name, skill_name, success}` 생성. 로그 exporter는 두지 않는다(debug exporter도 logs 파이프라인에서 제외).
6. **앱 표시**: 앱이 Prometheus에서 native 지표 존재를 확인하면 해당 에이전트·신호의 `telemetry` 모드를 `native`로 바꾸고 bridge 값은 비교용 툴팁으로만 둔다. 누적 카운터는 `increase()` 등 기간 질의로만 쓰고, bridge의 누적 스냅샷 게이지와 합치지 않는다.

## 검증 계획(적용 시 완료조건)

- 합성 OTLP/JSON 로그(프롬프트·`tool_input`·`email` 포함)를 `curl`로 `127.0.0.1:4318/v1/logs`에 보낸 뒤 Prometheus·collector 출력 어디에도 해당 문자열이 없고, 허용 라벨만 있는 카운터가 1 증가.
- LAN 주소 `:4318` 연결 불가, loopback만 성공.
- 같은 에이전트에 native와 bridge가 함께 있을 때 UI·API가 native만 표시(합계 증가 없음).
- 비허용 지표 이름은 Prometheus에 없음.

## 결정 필요(사용자)

- 에이전트별 `CLAUDE_CODE_ENABLE_TELEMETRY` 등 **전역 환경변수 설정**(Codex 단일 writer).
- `OTEL_LOG_TOOL_DETAILS=1` 사용 여부(스킬 성공 계측과 원문 유출 위험의 교환).

## 에이전트별 native 지원 현황 (Codex 감사 반영, 2026-10-31)

| 에이전트 | 공식 근거 | 상태 | 다음 단계 |
|---|---|---|---|
| Claude Code | [monitoring-usage](https://code.claude.com/docs/en/monitoring-usage): metrics + logs(events), traces beta | 공식 지원 | Codex 임시 sink로 송신·스키마 확인 후 allowlist 확정 |
| Codex CLI | `[otel]` log exporter·metrics exporter 공식 지원(Codex 감사: config-advanced, config-reference) | 공식 지원, **지표·이벤트 이름 미확인** | 임시 sink 수신 결과로 이름 allowlist 작성 |
| OpenCode 2.2.5 | 바이너리 안의 `OTEL_*` 문자열은 번들 SDK일 수 있음 | **미확인**(지원 증거 아님) | 실제 런타임 송신 시험 전까지 bridge 유지 |
| Antigravity | 설정의 telemetry는 Google 제품 개선용, 로컬 OTLP 경로 미확인 | **미지원으로 간주(근거 부족)** | bridge(statusLine·`/usage`) 유지 |

## 수신 스키마 계약(초안 v0, 임시 sink 결과로 확정)

- **엔드포인트**: `http://127.0.0.1:4318`(OTLP/HTTP, `http/protobuf` 기본, `http/json` 허용). gRPC 4317은 열지 않음. LAN·Docker 브리지 미게시.
- **에이전트 식별**: resource `service.name` → `agent` 매핑표(예: `claude-code`→`claude`, Codex 실제 값은 sink에서 확인). 매핑에 없는 `service.name`은 **drop**(알 수 없는 송신자 차단).
- **지표 allowlist**(이름 단위, 그 외 drop):
  - Claude: `claude_code.token.usage`{`type`∈input/output/cacheRead/cacheCreation, `model`}, `claude_code.cost.usage`{`model`}(API 정가 추정), `claude_code.session.count`.
  - Codex: sink 확인 후 추가(토큰 type이 cache를 input에 포함하는지 확인해 bridge와 같은 의미 규칙으로 매핑).
- **라벨 allowlist**: `agent`, `model`, `type`, `skill_name`, `tool_name`, `success`, `decision`. 그 외 resource·data point 속성(`user.*`, `organization.id`, `session.id`, `prompt.id`, `terminal.type` 등) 삭제.
- **이벤트 allowlist**: Claude `claude_code.tool_result`, `claude_code.tool_decision`(+ Codex 대응 이벤트는 sink 확인 후). 남기는 속성은 위 라벨 allowlist뿐이며, `tool_parameters`에서는 `skill_name`만 추출. 이벤트 본문·`prompt`·`tool_input`·`error` 메시지·`api_request_body`/`api_response_body`는 저장·전달하지 않음(logs exporter 없음, count connector로만 집계).
- **누적성**: native 토큰·비용은 counter(델타 또는 누적) → Prometheus `increase()`로 기간 집계. bridge 누적 스냅샷 게이지와 **합산 금지**, 같은 agent·신호에 native가 있으면 UI는 native만 표시.

## 진행 상태

- 설계·스키마 초안: 이 문서. **collector 설정·compose 게시는 아직 변경하지 않음**(Codex sink 결과 수신 후 조율하여 Claude가 `otel-collector.yaml`·`compose.yaml`에 적용).
- 앱 측: `telemetry` 모드 필드(`native|bridge|unsupported`)와 UI 배지는 v2에서 준비. native 판정 로직은 Prometheus 질의 연결 시 추가.

## 실제 송신 스키마 확인 (2026-10-31T04:48Z, 임시 sink `127.0.0.1:14318`)

근거: `test/results/native-otel-schema.json`(Codex sink — 키·이름·건수만, 값·본문 폐기). Claude가 headless smoke 2건을 별도 프로세스로 실행했다(기존 패널 세션 재시작 없음). 두 실행 모두 exit 0, stderr 0바이트, stdout은 `test/.local/ignored/`에만 저장.

- OpenCode: `opencode run --standalone --model llm-server/Qwen3.8-Flash-Next-IQ3_S --format json` + `OTEL_*`(http/protobuf, 1초 간격)
- Claude: `claude -p --model claude-opus-5-5 --output-format json` + 위 env + `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_LOG_USER_PROMPTS=0`, `OTEL_LOG_ASSISTANT_RESPONSES=0`, `OTEL_LOG_TOOL_DETAILS=0`, `OTEL_LOG_TOOL_CONTENT=0`. 응답 `OK`, 1턴.

| service.name | 신호 | 요청/항목 | 관찰 |
|---|---|---|---|
| `claude-code` | metrics | 2 / 4 | 이름: `claude_code.token.usage`, `claude_code.cost.usage`, `claude_code.session.count`, `claude_code.active_time.total`. 속성 키에 `user.email`·`user.id`·`user.account_uuid`·`user.account_id`·`organization.id`·`session.id`·`terminal.type` 포함 |
| `claude-code` | logs | 3 / 53 | 속성 키 70종. 토큰·비용(`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`, `cost_usd`, `model`)과 함께 **`prompt`·`prompt_text`·`prompt.id` 키가 `OTEL_LOG_USER_PROMPTS=0`에서도 존재**(값은 sink가 폐기해 마스킹 여부 미확인 → 민감으로 간주). 이벤트 이름은 sink가 기록하지 않음(`event.name` 키만 확인) |
| `opencode` | logs | 4 / 112 | Effect 런타임 HTTP 로그(`http.method`, `http.status`, `http.url`, `role`). **지표·토큰 사용량 없음** |

### 결론과 스키마 v1 조정

- **Claude**: 사용량은 metrics만으로 충분(`token.usage`의 `type`=input/output/cacheRead/cacheCreation, `model`). logs는 사용량 목적에는 쓰지 않는다. 스킬 성공 계측용 `tool_result`/`tool_decision`은 이번 smoke(도구 미사용)에서 관찰되지 않았으므로 도구 사용 smoke로 별도 확인 필요.
- **라벨 정리 필수**: Claude metrics 데이터 포인트에 사용자 식별 키가 실제로 실려 오므로 collector `attributes` 처리기로 `model`, `type` 외 전부 삭제(allowlist)한 뒤에만 Prometheus로 보낸다. `effort`·`query_source`는 필요 시 추가.
- **logs 파이프라인**: `prompt`/`prompt_text` 키가 설정과 무관하게 존재하므로 "민감 키 삭제(denylist)"가 아니라 **이벤트 이름 allowlist + 속성 allowlist**만 허용한다. 허용 이벤트 외 로그는 전량 drop, logs exporter 없음.
- **OpenCode**: native OTel은 런타임 HTTP 로그뿐이라 사용량 신호가 아니다. `telemetry.usage = bridge` 유지, native로 표시하지 않는다. `http.url`이 포함되므로 수신하더라도 drop.
- **Codex**: Codex smoke 결과(사용자 실행) 반영 후 이름·속성 allowlist 추가.
- 적용 순서: Codex smoke 확인 → `otel-collector.yaml`(Claude, Codex와 조율 후) 수정 → 합성 OTLP로 식별 키·`prompt` 키가 Prometheus에 없음을 검증 → 앱 native 판정 연결.

## 구현 상태 (2026-10-31, Claude) — collector 적용 완료, 전역 에이전트 설정은 루트 담당

- `otel-collector.yaml`(변경 전 사본: `test/.local/otel-collector.yaml.before-native`):
  - 수신 `otlp/native`(컨테이너 4320) ← compose `127.0.0.1:${NATIVE_OTLP_PORT:-4318}:4320`(loopback 전용, LAN override 미포함). 앱용 내부 `otlp` 4318은 그대로.
  - `metrics/native`: `filter/native_allowlist`(service.name × 지표 이름) → `transform/native_labels`(resource는 `service.name`만, scope 속성 삭제, data point는 `model`·`type`·`token_type`만) → Prometheus.
    - 허용: `claude-code` → `claude_code.token.usage`, `claude_code.cost.usage`, `claude_code.session.count` / `codex_exec` → `codex.turn.token_usage`, `codex.conversation.turn.count`.
  - `logs/native`, `traces/native`: 받기만 하고 `nop`으로 폐기(raw 로그·스팬 export 없음).
- 합성 OTLP 검증(실제 송신 전, `127.0.0.1:4318`): HTTP 200. 식별 속성(`user.email`, `session.id`, `conversation.id`, scope 속성, `host.name`)·비허용 지표(`claude_code.lines_of_code.count`, `codex.turn.tool.call`)·미등록 송신자(`evil-agent`)·로그 본문/`prompt` 모두 exporter 출력에서 **0건**(`SECRET` 문자열 0). 연속 구간 delta 10+20+30 → 60 누적 확인. LAN `192.168.0.65:4318` 연결 불가. 합성 시계열은 collector 재시작으로 exporter에서 제거, Prometheus에 남은 표본은 `increase()`=0이라 앱 native 표시에서 제외.
- 앱: `PROMETHEUS_URL`로 `increase(...[24h])`·마지막 수신 시각을 60초 캐시 조회 → `telemetry[agent].native_usage`(api.md v2.1). `usage`는 계속 bridge(기간이 달라 대체·합산하지 않음). 테스트 `NativeUsageTest` 2건.

- **독립 리뷰 반영(2026-10-31, 변경 전 사본 `test/.local/otel-collector.yaml.before-native-delta`)**:
  - 문제 1: `max(timestamp(m))`는 마지막 **스크랩** 시각이라 송신이 멈춰도 최근처럼 보였다. → transform이 native 표본 시각을 collector 수신 시각(`Now()`)으로 바꾸고 exporter `send_timestamps: true`. 앱은 `max(max_over_time(timestamp(m)[24h:1m]))`.
  - 문제 2: 식별자를 지운 cumulative가 같은 model/type에서 서로 덮어썼다. → `cumulative_to_delta/native`(원래 식별자로 delta 변환) → `transform/native_labels`(scope name/version도 비움) → `delta_to_cumulative/native`(허용 라벨 시계열에 누적).
  - 수신 시각으로 바꾸지 않은 대조 실행은 2세션 cumulative 41→36, delta 15→8로 **조용히 유실**(`ErrOlderStart`/순서 역전). 바꾼 구성은 41/15, Codex histogram sum 290·count 3, 경고 0.
  - 재현: `python3 tests/native_pipeline_check.py`(이전 구성으로 돌리면 실패). 실제 headless Claude 2회: input 2+2=4, output 4+4=8 누적, 라벨 `model`·`type`만, `last_received_at`=2회차 수신 시각.
  - 한계: `increase()`는 외삽 추정이고 첫 표본(단발 실행·5분 넘게 쉰 뒤 첫 값)은 빠진다(UI 블록 하단에 표시). collector 재시작이나 5분 무수신 뒤 누적이 0부터 다시 시작하며, 다음 값이 이전 누적보다 작으면 reset으로 정상 계산되지만 크거나 같으면 그만큼 적게 잡힌다.

- **codex-app-server 허용(2026-10-31, 루트 실측 `test/results/native-codex-app-schema.json`)**: Codex App/TUI 백엔드는 `service.name="codex-app-server"`로 보낸다. 같은 Codex 허용 지표(`codex.turn.token_usage`, `codex.conversation.turn.count`)만 통과하고, 실측된 시작·저장소 지표(`codex.process.start` 등 10종)와 미등록 송신자는 계속 버린다. Prometheus에서는 `job`(송신자)만 다른 별도 시계열이고, 앱 질의는 `sum by (model, token_type)`이라 exec와 합쳐 보인다. 변경 전 사본 `test/.local/otel-collector.yaml.before-codex-app-server`, 검증 `tests/native_pipeline_check.py` 통과.

### 루트(Codex)가 적용할 에이전트 설정 권장값
- 공통: `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318`, `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`, `OTEL_METRICS_EXPORTER=otlp`.
- logs/traces는 collector가 어차피 폐기하므로 **보내지 않는 것을 권장**(`OTEL_LOGS_EXPORTER=none`, `OTEL_TRACES_EXPORTER=none` 또는 Codex `[otel]`에서 metrics만).
- Claude: `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_LOG_USER_PROMPTS`·`OTEL_LOG_TOOL_DETAILS`·`OTEL_LOG_TOOL_CONTENT`·`OTEL_LOG_ASSISTANT_RESPONSES`는 0 유지.
- OpenCode·Antigravity: 사용량은 bridge 유지(native 사용량 신호 없음/미확인).
- 적용 후 확인: `curl -s localhost:9090/api/v1/query --data-urlencode 'query=claude_code_token_usage_tokens_total'`에 `model`·`type` 외 라벨이 없고, UI 카드에 "네이티브 OTel 최근 24시간" 블록이 나타남.
