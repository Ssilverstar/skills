# CONTRACT-001: Agent Observatory API (소유: Claude/Opus, 변경 시 Opus 승인)

원천: `test/monitor-brief.md`, 서버 구현 `test/monitor/app/server.py`(Claude 소유, 작업자 수정 금지).
실제 입력 예: `test/.local/monitor/snapshot.json`(Codex `host_probe.py` 산출, 읽기만).

## 엔드포인트 (모두 GET, JSON, `Cache-Control: no-store`, CSP `script-src 'self'; style-src 'self'`)

| 경로 | 응답 |
|---|---|
| `/` | `app/static/index.html` |
| `/static/app.js`, `/static/style.css` | 허용 목록 파일만. 다른 이름은 404 |
| `/health` | `{status:"ok", snapshot:"waiting\|ok\|stale", snapshot_age_seconds, snapshot_error, db_rows, collector, prometheus}` — collector/prometheus는 `ok\|unreachable\|not_configured\|http_NNN` |
| `/api/snapshot` | `{status:"waiting\|ok\|stale", source:null\|"file"\|"history", age_seconds, stale_after_seconds, error, snapshot}` |
| `/api/history?hours=24&limit=500` | `{hours, matched, stored_total, step, retention_days, max_rows, points:[Point]}` · hours가 유한한 숫자가 아니거나(`nan`, `inf`, 문자) limit가 정수가 아니면 400. 범위 밖 값은 hours 0.1~8760, limit 10~5000으로 조정 |

- `status:"waiting"` → `snapshot:null`(아직 스냅샷 없음). `stale` → 마지막 값은 있으나 `stale_after_seconds`(기본 180초) 초과.
- `source:"history"` → 재시작 후 DB에서 복원한 **압축본**: `snapshot.skills.compacted:true`이고 `skills.agents[].skills` 목록이 없다(개수만). 다음 폴링(≤15초)에 전체본으로 바뀐다.
- `error` → 최신 파일을 읽지 못함(이전 정상 스냅샷은 유지).

`Point = {collected_at, cpu_percent, memory_used_percent, inference_reachable, gpu:[{name, utilization_percent, temperature_c, power_watts, memory_used_bytes}], agents:{<id>: total_tokens}, errors}` — 오름차순, 마지막 점은 항상 최신. 모르는 값은 `null`.

## snapshot 의미 규칙 (UI·테스트 공통, 위반 = 결함)

1. `null`/누락 = **미확인**. 스냅샷의 `NaN`/`Infinity`도 수집 시 `null`로 읽는다(API 응답은 항상 엄격한 JSON). 0과 다르게 표시. GB10 `memory_used_bytes:null` + `memory_note` → "N/A(통합 메모리)"로, 0이나 GPU 전용 사용량으로 표시 금지. 호스트 `memory_*`는 시스템(통합) 메모리이지 GPU 전용 사용량이 아님.
2. 토큰: `input_tokens`는 캐시 읽기(`cached_input_tokens`)·캐시 쓰기(`cache_write_input_tokens`)를 **포함**, `reasoning_tokens`는 `output_tokens`의 **일부**. `total_tokens`는 공급자/프로브 값 그대로. 이 필드들을 서로 더하지 않는다.
3. `usage`는 이미 모델 합산 결과. `usage`와 `models[]`를 더하지 않는다. `models[].sessions`를 합산해 세션 수로 쓰지 않는다(세션 수는 `usage.sessions`).
4. 플랜 사용률은 `plan.limits[].used_percent`만. 로컬 토큰으로 환산 금지. 값 옆에 `plan.source`와 `plan.observed_at` 표시. `source`에 `preflight` 또는 `historical`이 있거나 `observed_at`이 24시간 넘게 지났으면 "과거 관측(이력)"으로 명시. `limits:[]` → "한도 정보 없음".
5. `agent.status`: `observed`=관측됨, `partial`=부분 관측(예: 한도만 관측, 토큰 일부/미지원), `unavailable`=미지원/미확인, 그 외 문자열은 그대로(이스케이프).
6. 스킬: `enabled` true/false/null = 활성/비활성/미확인. `invocations`는 **호출 요청 증거**(성공 아님). `null` → "미계측"(+`usage_evidence`), **미사용 아님**. `installed_count`/`enabled_count` null → 미확인. `skills.notes`는 그대로 보여준다. `repository:[]`는 "저장소 원본 스킬 없음".
7. 추론 서버 `hardware.inference`: `engine`=실제 실행 런타임(현재 `llama.cpp`), `version`=런타임 버전, `runtime_executable`=실행 파일(예: llama-server), `container_image`=컨테이너 이미지, `installed_vllm_version`=이미지에 **설치만 된** vLLM 배포 패키지(dist) 버전(실행 런타임 아님, 모듈 `__version__`과 다를 수 있음). 라벨: 실행 런타임/런타임 버전/실행 파일/컨테이너 이미지/이미지 내 vLLM(미사용) — **같은 칸에 합치지 말 것**. 그 밖의 추가 스칼라 필드도 키 이름과 함께 별도 행으로 표시.
8. 바이트는 1024 기준이므로 KiB/MiB/GiB/TiB로 표기(GB/MB 금지).
9. 모든 외부 문자열은 textContent/텍스트 노드로만 삽입(innerHTML 금지). 외부 CDN·폰트·네트워크 요청 금지(`connect-src 'self'`).

## OpenTelemetry (참고, UI 무관)

게이지 `observatory.*`(server.py `METRICS`)를 OTLP HTTP → Collector → Prometheus로 내보냄. null 값은 내보내지 않음. `observatory.agent.tokens{type=...}`는 포함관계라 type 간 합산 금지.

## v2 추가 (2026-10-31, Claude 승인)

### `/api/snapshot`에 `telemetry` 추가
`telemetry: {<agent_id>: {usage: Mode, quota: Mode, usage_source, quota_source}}`, `Mode = "native" | "bridge" | "unsupported"`.
- `bridge`: 호스트 프로브가 로컬 기록·statusLine·계정 API 등에서 **변환해 가져온 값**(현재 모든 관측값).
- `native`: 에이전트가 공식 OpenTelemetry로 직접 보낸 값(수신 경로 설계 단계, 현재 없음).
- `unsupported`: 해당 신호 값이 없음(`usage.total_tokens` null 또는 `plan.limits` 비어 있음).
- 같은 신호에 native와 bridge가 함께 있으면 **native만 표시**하고 둘을 더하지 않는다.

### `/api/history` 해상도
- `hours ≤ 24` → `resolution: "raw"`(정제 스냅샷 원본, 15초 주기, 보존 24시간).
- `hours > 24` → `resolution: "5m"`(5분 집계, 보존 30일). Point 모양은 같고 값의 의미가 다름:
  - 게이지(cpu/memory %, GPU 사용률·온도·전력·메모리) = 버킷 **평균**, `stats["<경로>"] = {min, max, last, n, unknown}`(경로 예: `cpu_percent`, `gpu.0.utilization_percent`).
  - 누적 토큰 `agents{}` = 버킷 **마지막 값**(합산하지 않음). `inference_reachable` = 마지막 값.
  - `samples` = 버킷의 원본 스냅샷 수. 모든 표본이 null이면 값 null(`unknown = n`).
- 응답 공통 필드: `raw_retention_hours`, `agg_retention_days`, `agg_bucket_seconds`.
- "raw"는 대화 원문이 아니라 **프로브가 정제한 집계 스냅샷**이다(프롬프트·도구 입력은 수집·저장하지 않음).

### v2.1 `telemetry[agent].native_usage` (2026-10-31)
native OTel이 실제로 수신된 에이전트(현재 Claude·Codex 대상)에만 붙는 **별도 관측**:
`{window: "24h", tokens: {<model>: {<type|token_type>: 증가량}}, last_received_at: ISO|null, source}`.
- 기간이 다르다: `usage`(bridge)는 보존된 로컬 세션 **누적**, `native_usage`는 collector가 받은 counter의 **최근 24시간 증가분**. 서로 대체·합산하지 않으며 `telemetry.usage`는 계속 `bridge`.
- 증가분 0인 시계열은 제외. Prometheus 장애 시 필드 없음. Claude `type`=input/output/cacheRead/cacheCreation, Codex `token_type`은 공급자 원문 값(의미는 Codex 문서 기준, 확인 전에는 원문 라벨 그대로 표시).

### v2.2 native 파이프라인 정정 (2026-10-31, 독립 리뷰 반영)
- `last_received_at` = **collector 수신 시각**. collector가 native 표본 시각을 수신 시각으로 바꾸고 exporter `send_timestamps:true`로 Prometheus에 싣는다. 서버는 `max(max_over_time(timestamp(m)[24h:1m]))`로 window 전체의 가장 늦은 표본 시각을 찾는다(최대 1분 지연). 이전 `max(timestamp(m))`는 마지막 스크랩 시각이라 송신이 멈춰도 최근처럼 보였다.
- 세션 합산: `cumulative_to_delta`(원래 식별자 유지) → 허용 라벨만 남김 → `delta_to_cumulative`로 같은 model/type 시계열에 누적. 식별자를 지운 cumulative끼리 덮어쓰던 문제를 막는다. 검증: `python3 tests/native_pipeline_check.py`(2세션 cumulative+reset, delta 순서 역전, 한 요청 2세션, Codex histogram, 허용 목록 밖 송신자, 식별자 미노출).
- 한계(UI 표시): `increase()`는 외삽 추정이며 시계열의 첫 표본(단발 실행, 5분 넘게 쉰 뒤 첫 값)은 빠질 수 있어 적게 보일 수 있다.

### v2.3 표시 규칙 추가 (2026-10-31, 프로브 필드 반영)
- `skills.agents[].common_selected_count` / `common_installed_count` = 공통 선택 목록(36) 기준 선택·설치 수. `installed_count`(등록 전체)·`enabled_count`(활성)와 **별도 줄**로 표시하고 서로 더하거나 대체하지 않는다. null → 미확인.
- `hardware.gpu[].process_memory_used_bytes`, `compute_processes[{name, memory_used_bytes}]` = nvidia-smi compute-apps의 프로세스별 GPU 메모리. GB10 전용 VRAM(`memory_used_bytes:null`, N/A)과 **별개 지표**: 합계와 프로세스 이름·크기만 보여 주고 전용 VRAM 비율로 환산하지 않는다. 누락 → 미확인, `[]` → 없음.

### v2.4 `snapshot.mcp` (2026-10-31, 루트 host_probe 구현 · Claude 승인)
`mcp = {common_servers: ["git","github","chrome-devtools"], agents: [{agent, common_configured_count, servers: [{name, scope: "common"|"platform", configured: bool, enabled: bool, status: "connected"|"configured"|"error"|"unverified", tool_count: int|null, checked_at: ISO|null, note: 영어 문자열}]}], observed_at: ISO}`
- 서버는 그대로 전달한다(원문성 키 제거 `scrub` 대상 아님, 이력 압축본에도 유지 — `McpPassThroughTest`).
- `connected` = 해당 에이전트 설정 그대로 MCP initialize·tools/list·읽기 호출이 성공한 증거. `configured` = 설정만 확인, `unverified` = 확인 안 함(미확인), `error` = 시도 실패. 상태색은 아이콘·라벨과 함께.
- `scope:"platform"` = 앱 전용 OAuth 연결 등 공통 설정으로 이식하지 않는 플랫폼 추가분. 공통 수(`common_configured_count`/공통 서버 3)와 **별도 계수**하고 더하지 않는다.
- `mcp` 또는 에이전트 항목이 없으면 UI는 "MCP 미확인"으로 명시(0으로 표시 금지). `tool_count:null` = 미확인.

### v2.5 프로브 계수 필드 (2026-10-31, 루트 host_probe)
- `skills.agents[].common_enabled_count` = 공통 36 중 활성 확인 수, `platform_extra_count` = 공통 밖에서 활성인 플랫폼 추가분(내장·앱·플러그인 보조, 예: Claude humanize 보조 3). UI는 **프로브 값을 우선** 쓰고(압축본에서도 유지됨), 없을 때만 `skills[]` 목록으로 계산, 둘 다 없으면 미확인. 공통 수와 더하지 않는다.
- MCP `status:"connected"`는 디스커버리(initialize·tools/list) 성공일 뿐 실제 도구 호출 성공을 뜻하지 않을 수 있다(예: chrome-devtools 목록 30개 발견, `list_pages` Target closed). UI 문구는 "연결 확인"까지만 쓰고 "사용 가능"으로 단정하지 않는다. 실제 호출 실패는 프로브가 `error`·note로 알려 준다.
- (추가) Codex native 송신자는 `codex_exec`와 `codex-app-server`(App/TUI 백엔드) 둘 다 허용. `native_usage.codex`는 두 송신자를 `model`·`token_type`별로 합친 값이다(같은 기간 증가분이라 합산이 맞음).
