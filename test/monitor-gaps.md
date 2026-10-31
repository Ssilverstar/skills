# Agent Observatory 미구현·부분 구현과 개선 실행안

작성: Claude Opus 5.5(구현 총괄), 2026-10-31. 기준: [`monitor-brief.md`](monitor-brief.md) 요구 ↔ `test/monitor/` 현행 코드·실측.
범위: 이번 차수에 구현한 것은 **LAN 접속(§0)뿐**이다. §2 이하는 근거가 있는 실행안이며 아직 구현하지 않았다.

표기: ✅ 구현·검증 / ◐ 부분 / ✗ 미구현. 근거 종류: **[코드]** 저장소 파일·행, **[실측]** 이 호스트에서 실행한 결과, **[공식]** 공급자 문서, **[미확인]** 근거 없음(추정 금지).

## 0. 이번 차수 구현: LAN 접속

| 항목 | 상태 | 근거 |
|---|---|---|
| localhost 유지 + LAN IP 추가 바인딩(앱만) | ✅ 호스트 자기 접속 | [코드] `monitor/compose.lan.yaml`, `monitor/lan.env.example`, 로컬 값 `test/.local/monitor-lan.env`(git 제외). [실측] `ss`: `127.0.0.1:8787`, `192.168.0.65:8787`, `127.0.0.1:9090`만 LISTEN. `http://192.168.0.65:8787/health` 200, `192.168.0.65:9090` 연결 불가 |
| Prometheus·collector 비노출 | ✅ | [실측] collector 포트 미게시, Prometheus는 127.0.0.1만 |
| Windows 브라우저 실접속 | **미확인** | 사용자 응답 대기. Codex LAN E2E(`test/results/monitor-lan-e2e.json`)는 같은 호스트에서 LAN 주소로 접속한 결과이며 다른 기기 접속의 증거가 아니다 |
| 인증 | ✗(의도적 보류) | 읽기 전용이지만 같은 LAN의 누구나 사용량·스킬 경로를 볼 수 있음. §2-H |

## 1. 요구 대조표

| 브리프 요구 | 상태 | 근거·현황 |
|---|---|---|
| 한국어 다크 UI, 좌측 3메뉴, 모바일 | ✅ | Codex Playwright 6시나리오 PASS(`test/results/monitor-e2e.json`) |
| 에이전트별 모델·토큰(모델별 표) | ◐ | Codex·Claude·OpenCode는 로컬 기록에서 모델별 집계 [코드] `host_probe.py` 81–112행. **Antigravity는 세션 누적 입력/출력 합계만**, 모델별·캐시 없음([코드] 487–490행에서 캐시 null) |
| 추론(reasoning) 토큰·비용·기간별 모델 사용량 | ✗ | 모든 에이전트 `reasoning_tokens=None`, `cost_usd=None` 고정([코드] 111행). 미확인을 0으로 두지 않은 것은 의도대로. 모델별 표는 전체 누적 한 구간뿐(§2-J) |
| 구독 한도(공식/관측값만) | ◐ | Codex 계정 API 실시간 / Claude statusLine `rate_limits` 마지막 관측 / Antigravity 공식 `/usage` 5분 주기. **신선도 기준·한도 이력 그래프 없음**(§2-D) |
| GPU 그래프 | ✅ | 사용률·온도·전력·호스트 메모리 4개 |
| GB10 메모리(0 변환 금지) | ◐ | 전용 VRAM 총량은 N/A로 정확히 표시. **프로세스별 GPU 메모리는 수집 가능하나 미수집**(§2-B) |
| 추론 서버 상태 | ◐ | 엔드포인트·모델·런타임/이미지 vLLM 구분 ✅. 처리량·대기열 등 서버 지표 없음(§2-G). `version`은 서버가 `b0-unknown`을 보고(빌드 메타 없음) |
| 스킬 설치/활성/사용 증거 구분 | ◐ | 설치 수 ✅. 활성은 Codex·Claude만 확정, OpenCode·Antigravity `enabled_count=null`. 호출은 **요청 증거만**: 현재 Claude 2건·OpenCode 1건, Codex·Antigravity 0건 계측. **성공 여부 미계측**(§2-C) |
| DB 이력·보존 | ◐ | collected_at UNIQUE, 압축 저장, 14일/2만 행. 15초 주기면 실제 약 3.5일(§2-F) |
| `/health`, `/api/snapshot`, `/api/history`, 대기·이스케이프 | ✅ | QA 24 + 통합 4 테스트, FE 14 테스트 |
| OTel 지표 → Collector → Prometheus | ◐ | 18종 지표 ✅. **재시작 시 인스턴스 시계열 중복**(§2-D) |
| 앱 트레이스 OTLP | ◐ | collector까지 전송, span_metrics로 확인. **트레이스 저장·조회 없음**(§2-E) |
| 고정 버전·ARM64·헬스 | ✅ | collector 0.164.0, Prometheus v3.15.1, python 3.13.18-slim. collector는 distroless라 Docker 헬스체크 없음, 앱 `/health`가 대신 확인 |
| 재부팅 후 운영 | ◐ | 컨테이너 `unless-stopped`. 수집기는 **사용자 로그인 후에만** 기동(linger 미설정)(§2-I) |

## 2. 개선 실행안

우선순위: **P1** 정확성·오해 방지, 작은 변경 / **P2** 가치 큼, 권한·설계 결정 필요 / **P3** 선택.

### A. Antigravity 모델별·캐시 토큰 — P2
- 현황: statusLine 콜백이 세션 누적 `input/output/total`만 저장([실측] `test/.local/monitor/antigravity-sessions/*.json`).
- 근거: [공식] [Antigravity statusline](https://antigravity.google/docs/cli/statusline/) — `context_window.total_input_tokens/total_output_tokens`(세션 누적), `current_usage.{input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens}`(직전 응답), `model.id`, `session_id`, `transcript_path`. 문서 예시는 "sanitized" 표기.
- 위험: `current_usage`는 **직전 응답 하나**의 값이다. 누적값이 바뀔 때마다 latest를 더하면 ① 콜백 사이에 응답이 여러 개 끝난 경우(중간 콜백 누락) 일부만 더해지고, ② 스트리밍 중 갱신이 반복되면 중복되며, ③ 응답 사이 모델 전환 시 다른 모델로 잘못 귀속된다.
- 방법(보수적 귀속):
  1. 세션별로 이전 누적값(`total_input_tokens`, `total_output_tokens`)을 보관하고 누적 delta를 계산한다.
  2. **누적 delta가 `current_usage`(input/output)와 정확히 일치할 때만** 그 응답을 하나로 보고 `cache_read_input_tokens`·`cache_creation_input_tokens`를 귀속한다. 모델은 별도로 제한한다: [공식] `model.id`는 **현재 선택된 모델**이고 현 스풀의 `current_model`은 `display_name` 우선 값이라, 둘 다 그 응답을 실제로 생성한 모델의 증거가 아니다. 따라서 모델 귀속은 `transcript_path`에서 응답 ID와 응답별 모델·usage가 확인될 때만 확정하고(필드 존재는 표본 확인 전까지 **[미확인]**), 그 전에는 "선택 모델 기준(추정)"으로 라벨을 분리하거나 `unattributed`에 둔다.
  3. 일치하지 않는 delta는 모델·캐시를 추정하지 않고 세션의 **`unattributed` 버킷**에 input/output만 보존한다.
  4. 커버리지 = 귀속 토큰 / 누적 delta 합. UI는 모델별 행과 함께 "미귀속 N 토큰(커버리지 X%)"을 표시한다.
  5. 누적값이 줄어들면(세션 재시작·새 대화) 새 기준선으로 보고 음수 delta를 만들지 않는다.
- 정확도·한계: 콜백이 불릴 때만 관측. **콜백 연결 이전 과거 이력은 복원 불가로 간주**(transcript 필드가 확인되기 전까지 가능하다고 가정하지 않음).
- 권한: 사용자 홈 `~/.gemini` 읽기(이미 콜백 설치됨), transcript 읽기는 대화 원문 접근이므로 **usage 필드만 추출, 원문 저장 금지**.
- 완료조건(합성 콜백 시퀀스 단위 테스트):
  - 정상: delta = latest → 모델·캐시 귀속, 커버리지 100%.
  - 중복: 같은 누적값 콜백 반복 → 추가 0.
  - 누락: 응답 2개 뒤 콜백 1회(delta ≠ latest) → 전량 `unattributed`, 모델 귀속 없음.
  - 모델 전환: 전환 직후 불일치 delta → `unattributed`, 이전 모델로 귀속하지 않음. delta가 일치해도 응답별 모델 증거가 없으면 "선택 모델 기준(추정)"으로만 표시.
  - 재시작: 누적값 감소 → 기준선 재설정, 음수 없음.
  - 모든 경우 귀속 + 미귀속 합 = 누적 delta 합.
  - UI·E2E: Antigravity 모델별 행에 "콜백 연결 이후 · 커버리지 X%" 표기.

### B. GB10 프로세스별 GPU 메모리 — **P1(우선)**
- 근거: [공식] [DGX Spark known issues](https://docs.nvidia.com/dgx/dgx-spark/known-issues.html) — iGPU는 전용 프레임버퍼가 없어 `Memory-Usage: Not Supported`가 정상이며, **프로세스별 GPU 메모리는 계속 표시됨**. 할당 가능량은 `cudaMemGetInfo`만 믿지 말고 `/proc/meminfo`의 `MemAvailable`·`SwapFree`·HugePages도 고려하라고 안내. [실측] `nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits` → llama-server 72213 MiB = 70.52 GiB(Codex 실측; GAP-HOST에서 `/src/build/bin/llama-server` 동일 값 재현). 같은 실측에서 `nvidia-smi -q -d MEMORY`의 FB·BAR1 Memory는 전부 N/A.
- 방법: 프로브(Codex 소유)에 `gpu[].processes=[{process_name, used_gpu_memory_bytes}]`(pid는 선택) 추가 → 서버 `observatory.gpu.process.memory.used{process_name}` 게이지 → UI GPU 카드에 "프로세스별 GPU 메모리(NVIDIA 보고)" 목록.
- 표시 원칙: 라벨은 **"프로세스별 GPU 메모리(NVIDIA 보고값)"**로 하고, 할당량·상주량 등 NVIDIA 보고값 이상의 의미를 추정해 붙이지 않는다. "GPU 전용 VRAM 사용률"이나 "전체 GPU 메모리 사용량"으로 합산·표시하지 않으며, 호스트 통합 메모리(MemTotal 대비) 행과 별도로 둔다. 백분율은 만들지 않는다(분모가 공식적으로 정의되지 않음).
- 권한: 사용자 권한 `nvidia-smi`로 충분([실측]). 다른 사용자의 프로세스 이름이 보일 수 있으므로 이름만 노출하고 명령행은 수집하지 않는다.
- 완료조건: 프로브 단위 테스트(정상/`[N/A]`/프로세스 없음), 계약 `api.md` 갱신, UI·E2E에서 실측 프로세스 값(예: 70.52 GiB)이 "프로세스별 GPU 메모리(NVIDIA 보고값)"로 표시되고 전용 VRAM 칸은 N/A 유지.

### C. 스킬 호출 성공 계측 — P2
- 현황: Claude는 로컬 transcript의 `tool_use name=Skill`(요청)만 집계([코드] `host_probe.py` 165행), 성공 여부 없음.
- Claude 근거: [공식] [Claude Code monitoring](https://code.claude.com/docs/en/monitoring-usage) — `CLAUDE_CODE_ENABLE_TELEMETRY=1` + `OTEL_LOGS_EXPORTER=otlp`이면 `claude_code.tool_result` 이벤트에 `tool_name`, `success`, `duration_ms`, `error_type`가 있고, Skill 도구의 `skill_name`은 `OTEL_LOG_TOOL_DETAILS=1`일 때 `tool_parameters`에만 포함. 지표 `claude_code.token.usage{type=input|output|cacheRead|cacheCreation, model}`, `claude_code.cost.usage{skill.name}`도 제공.
- 방법: Claude Code를 기존 collector OTLP(4318, 현재 컨테이너 내부 전용)로 보내려면 collector에 **로컬 전용** 수신 포트 게시(127.0.0.1)와 logs 파이프라인이 필요. collector `attributes`/`transform` 처리기로 `tool_parameters`에서 `skill_name`만 남기고 나머지(입력·내용)는 삭제 → 스킬별 `success` 카운트. (collector 설정 파일은 이번 차수에 수정하지 않음.)
- 다른 에이전트: Codex·OpenCode·Antigravity의 공식 텔레메트리에 도구 성공 필드가 있는지 **[미확인]**. 확인 전에는 "요청 증거"만 유지.
- 정확도: `success`는 도구 실행 결과이지 사용자가 의도한 워크플로 완주가 아님. 거부된 호출은 `tool_result` 미발생(`tool_decision`으로 별도 집계).
- 권한·위험: `OTEL_LOG_TOOL_DETAILS=1`은 도구 입력을 내보내므로 collector 단계 필터가 **필수**. 사용자 전역 환경변수 변경이 필요(사용자 결정).
- 완료조건: 합성 OTLP 로그로 collector 필터가 `skill_name`·`success`만 남기는 테스트, UI 스킬 표에 "요청 N · 성공 M(Claude OTel)" 분리 표시.

### D. 구독 한도 신선도·이력과 인스턴스 라벨 — **P1**
- 현황: 한도는 스냅샷마다 저장되지만 UI에 이력 그래프 없음. Prometheus는 재시작마다 `service.instance.id`가 바뀌어 이전 시계열이 최대 5분 공존. `max by`로 접으면 초기화 직후 이전 높은 값이 남아 **최신값의 대체가 아님**.
- 방법:
  1. 인스턴스 라벨 고정(단일 인스턴스 배포 전제). [실측] 현재 Prometheus 시계열의 `service_instance_id`/`exported_instance`가 재시작마다 다른 UUID(예: `ce4259a7-…`, `13f54529-…`)로, SDK가 자동 생성한 값이다. 후보: compose에 `OTEL_RESOURCE_ATTRIBUTES=service.instance.id=agent-observatory-app`. **환경변수만으로 SDK 자동 UUID를 실제로 덮어쓰는지는 [미확인]**이므로, 안 되면 `server.py`의 `Resource.create({...})`에 `service.instance.id`를 명시해 override한다. 다중 인스턴스가 생기면 재검토.
  2. 한도마다 관측 시각 기반 게이지 `observatory.agent.plan.age{agent,limit}`(초) 추가. 알림·대시보드는 `age < 기준`인 값만 최신으로 사용.
  3. 신선도 기준(제안): Codex API 10분, Antigravity `/usage` 15분(5분 주기×3), Claude statusLine은 세션 활동 의존이므로 기준 초과 시 "마지막 관측 N분 전"을 강조하고 사용률 막대를 흐리게. `reset_at`이 지났는데 새 관측이 없으면 **"초기화 예정 시각 경과 · 재관측 대기"**로 표시하고 이전 사용률은 흐리게 둔다. 서버 재관측 없이 실제 초기화(0%)로 단정하지 않는다.
  4. `/api/history`에 플랜 한도 시계열(관측 시각 기준 중복 제거) 추가 → UI 한도 이력 차트.
- 완료조건:
  - 단위 테스트: `setup_otel`이 만든 Resource의 `service.instance.id`가 설정값과 같음(환경변수 경로와 코드 override 경로 각각).
  - 실측: 앱 2회 재시작 후 5분 이내 Prometheus `count by (agent, limit) (observatory_agent_plan_used_percent)` = 1. `plan` 라벨 값이 바뀌어도 시계열이 갈리므로 `plan`은 라벨에서 빼고 `target_info`류 정보 지표로 분리 검토.
  - 단위 테스트: `reset_at` 경과·재관측 없음 → "예정 시각 경과 · 재관측 대기", 재관측 후 정상 표시.
  - UI stale 표시 E2E.

### E. 트레이스 저장·조회 — P3
- 현황: collector `debug` 로그 + `span_metrics`(호출 수·지연)만.
- 방법: Jaeger(all-in-one, OTLP 수신) 또는 Grafana Tempo를 compose에 추가하고 collector traces 파이프라인에 `otlp` exporter 추가. ARM64 이미지·고정 버전 확인 필요 **[미확인: 이번 차수 미조사]**.
- 판단: 단일 앱의 요청 2~3종이라 현재 span_metrics로 운영 판단 충분. 외부 에이전트 트레이스(§C의 Claude beta traces)를 받기로 할 때 함께 도입.
- 완료조건: UI 없이도 `GET /health` 스팬을 저장소에서 trace ID로 조회.

### F. 이력 보존 — P3
- 현황: 15초 × 2만 행 ≈ 3.5일. 14일 설정이 사실상 적용되지 않음.
- 방법: 최근 48시간은 원본, 이후는 5분 대표값만 남기는 다운샘플(삭제 시점에 `collected_at` 버킷당 1행 유지) 또는 `MAX_ROWS` 상향(압축본 약 6KB/행 → 14일 약 80,640행 ≈ 480MB).
- 완료조건: 보존 테스트(버킷 대표값 유지), README 보존 문구와 실제 일치.

### G. 추론 서버 지표 — P2
- [실측: GAP-HOST]: `GET :8000/metrics` → HTTP 501 `"This server does not support metrics endpoint. Start it with --metrics"`(Claude 재확인 501). `/slots` 정상: 슬롯 1개, `n_ctx` 131072, `is_processing`, `n_prompt_tokens*` 등. `/props` 정상.
- 방법: (a) **재시작 없이** 프로브가 `/slots`를 읽어 `is_processing`(처리 중 슬롯 수)·`n_ctx`를 게이지로 추가 — 순간 상태라 처리량(토큰/초)은 얻지 못함. (b) 처리량·대기열이 필요하면 llm-server를 `--metrics`로 재시작하고 Prometheus가 직접 scrape — **추론 서버 재시작은 사용자 결정**(현재 작업 중 세션 중단).
- 완료조건: 처리 토큰/초·대기 요청 수가 Prometheus와 UI 추론 카드에 표시.

### H. LAN 접근 통제 — P3
- 방법: (a) `DOCKER-USER` iptables 체인에 `192.168.0.0/16`만 허용(root 필요), (b) 앱 앞에 Basic 인증 리버스 프록시. 포트포워딩·방화벽 전체 해제는 하지 않는다.
- 완료조건: 허용 대역 밖에서 거부, 허용 대역에서 200(다른 기기에서 확인).

### I. 재부팅 운영 — P2
- 현황 [실측: GAP-HOST, Claude 재확인]: `Linger=no`, `agent-observatory-probe.service` enabled(사용자 유닛), `docker` enabled, 앱·Prometheus·collector·llm-server 모두 `unless-stopped`. 즉 컨테이너는 부팅 시 복귀하지만 수집기는 로그인 후에만 기동 → 그 사이 UI는 stale.
- 방법: `loginctl enable-linger $USER`(사용자 결정, 시스템 상태 변경)로 로그인 없이 기동. 또는 현 상태 유지 + UI의 stale 표시로 공백을 명확히(현재 동작).
- 완료조건: 재부팅 후 로그인 전 snapshot 갱신 확인(실제 재부팅 시험 필요, 일정 협의).

### J. 추론 토큰·비용·기간별 모델 사용량 — P2
- 현황: `reasoning_tokens`·`cost_usd`는 모두 null 고정([코드] `host_probe.py` 111행). 모델별 표는 "보존된 로컬 이력 전체" 누적 한 구간뿐이라 기간(오늘/7일 등)별 조회 불가.
- 추론 토큰: 출처가 **명시적으로 제공할 때만** 채운다. Codex 로컬 `token_count` 이벤트의 reasoning 필드 존재 여부를 표본 확인 후 사용(**[미확인]**). 값은 항상 `output_tokens`의 **부분집합**으로 표시(합계에 다시 더하지 않음). 제공되지 않는 에이전트는 null 유지.
- 비용: 두 종류를 분리한다.
  1. **API 정가 추정**: 공급자가 계산해 주는 값만 사용 — [공식] Claude OTel `claude_code.cost.usage`(USD), [공식] Antigravity statusLine `cost.total_usd`(문서상 "list-price estimates, not billed amounts"). 라벨 "API 정가 추정(청구액 아님)".
  2. **구독 청구**: 정액 구독이므로 토큰 단가 환산 금지. 플랜명·한도 사용률만 표시.
  자체 단가표로 추정하는 방식은 단가 출처·갱신 부담 때문에 하지 않는다.
- 기간별 모델 사용량: 현재 누적 스냅샷의 차분은 세션 재계산·로그 회전 시 음수·오차가 생긴다. 대신 프로브가 **이벤트(응답) 단위 레코드**(시각, 에이전트, 모델, input/cache/output/reasoning, 출처, 중복 제거 키=세션+메시지/응답 ID)를 별도 테이블에 적재하고 `/api/usage?from&to&group=model`로 집계한다. 응답 ID로 중복을 못 거르는 출처(예: Antigravity 미귀속분)는 `unattributed`로 분리.
- 커버리지 표시: 기간 조회 결과마다 "관측 시작 시각(출처별), 미귀속 토큰, 수집 공백 구간"을 함께 반환·표시해, 0과 미관측을 구분한다.
- 완료조건: 이벤트 적재 중복 제거 테스트(같은 응답 2회 → 1건), 기간 경계 테스트, 출처 관측 시작 이전 구간은 "미관측"으로 반환, UI 기간 선택(오늘/7일/전체) E2E, 비용 칸 라벨이 "API 정가 추정"으로만 표시.

## 3. 다음 차수 권장 순서

1. **D-1·D-2** 인스턴스 라벨 고정·한도 관측 나이(앱/compose, Claude 소유, 작음)
2. **B** 프로세스별 GPU 메모리(프로브는 Codex, 서버·UI·계약은 Claude/작업자)
3. **D-3·D-4** 신선도 UI·한도 이력, **A** Antigravity 보수적 delta 귀속, **J** 이벤트 단위 사용량·기간 조회
4. **C** Claude OTel 기반 스킬 성공 계측(사용자 환경변수 결정 후), **G**, **I**
5. **E·F·H** 선택

## 4. 작업자 근거 수집(이번 차수)과 통합 검토

| 작업 | 작업자·모델 | 산출 | 통합 판정 |
|---|---|---|---|
| GAP-HOST | OpenCode · Qwen3.8 Flash Next(로컬) | [`GAP-HOST.md`](monitor/contracts/results/GAP-HOST.md): 10개 명령·exit code·발췌 | 채택. `/metrics` 501·`Linger=no`·docker enabled는 Claude가 재실행해 일치 확인. 요약의 "점유" 표현은 해석이므로 본문에서는 "NVIDIA 보고값"으로만 사용 |
| GAP-AGY | Antigravity 1.4.12 · Gemini 3.8 Flash | [`GAP-AGY.md`](monitor/contracts/results/GAP-AGY.md): `agy --help/--version`, 스풀 실제 필드, 공식 필드 대조 | 부분 채택. 실측(버전 1.4.12, 스풀 필드 `session_hash/current_model/plan/usage{input,output,total}`)은 채택. 원문의 세션 해시는 `<session-hash>`로 치환함(Claude 통합 시). 다음 해석은 정정: ① `current_usage`를 "delta"라 했으나 공식 문서상 **직전 응답 사용량**이며 delta가 아님(§2-A 보수적 귀속의 이유) ② "토큰·쿼터 직접 조회 CLI 플래그 없음"은 플래그 목록 기준으로만 맞고, `agy --output-format json --print /usage`(모델 호출 없음)로 쿼터 조회는 가능(Codex 실측) ③ `quota`(버킷별 잔여 비율·초기화 시각)와 `plan_tier`(플랜 등급)는 별개 필드이며, 스풀의 `plan: "Google AI Pro"`는 `quota` 필드의 실측 증거가 아님(쿼터 실측은 `/usage` 경로) ⑥ 스풀 `current_model`은 선택 모델의 표시명이라 응답 모델 증거가 아님(§2-A) ④ "세션별 이력 실측 확인"은 세션별 **최신 누적값**만 있다는 뜻이지 시간별 이력이 아님 ⑤ "delta 기록으로 모델별·캐시 집계 구현 가능"은 §2-A 조건(누적 delta=latest 일치 시에만 캐시 귀속, 응답별 모델 증거가 있을 때만 모델 확정, 나머지는 `unattributed`·커버리지로 보존, 중복·누락·전환·재시작 테스트 통과)으로 한정 |

- 범위 통제: Gemini가 범위 밖 `ls test/scripts`를 요청해 취소하고 결과 작성으로 좁혔다. 승인 요청 4건(`agy --help`, `agy --version`, 스풀 `ls`, `find`)은 화면 확인 후 1회씩 허용.
