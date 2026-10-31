# Agent Observatory 구현 계약

사용자 요청: Herdr `Codex | Claude | Agents`에서 Claude 주도로 독립 컨테이너 모니터링 웹 서버 구현. 왼쪽 메뉴 세 개: 에이전트 사용량/모델/구독 한도, DGX Spark GPU·하드웨어·추론 서버, 저장소/로컬 에이전트 스킬 설치·활성·사용 증거. 한국어 UI, 실제 데이터, 읽기 쉬운 완성도 있는 시각 디자인. OpenTelemetry 필수.

## 분담

- Claude: Architect/Integrator. user-guide의 역할·작업 계약·품질 게이트를 적용해 Gemini에 독립 구현, OpenCode에 TC/검증을 **직접 Herdr로 위임**하고 결과를 회수·통합. 이미 작성한 서버와 공통 API 계약을 소유. Docker Compose/OTel/SQLite 통합·검증·README를 책임짐. 직접 반복 구현만으로 작업자를 대체하지 않음.
- Antigravity / Gemini 3.8: Claude가 소유 파일·허용 범위·AC를 지정한 구현 작업자. Google CLI는 앞선 사용자 결정으로 Antigravity를 사용.
- OpenCode / Qwen3.8: Claude가 지정하는 TC 설계·검증 작업자. 사내 GLM 대신 집의 Qwen 모델 사용.
- Codex: `test/monitor/host_probe.py`, `test/monitor/test_host_probe.py` 호스트 수집과 테스트, `.local/` 스풀, 독립 통합 검증, 저장소 문서와 Herdr 개선 스킬. 다른 에이전트는 이 두 파일을 편집하지 않음.
- `test/` 기존 점검 파일 보존. root README/skills/herdr는 Codex가 편집. 자동 커밋·푸시 없음.

## 수집 경계와 계약

호스트 프로브는 표준 Python 라이브러리만 사용하며 `/home/hori/AI/skills/test/.local/monitor/snapshot.json`을 원자적으로 갱신. 컨테이너에는 이 디렉터리만 읽기 전용 `/data/host`로 마운트하고 `SNAPSHOT_PATH=/data/host/snapshot.json` 사용. 앱이 주기적으로 읽고 SQLite 시계열을 저장하며, **실제 수집 지표를 OpenTelemetry SDK → Collector OTLP HTTP → Prometheus로 내보냄**. 앱 트레이스도 OTLP 전송. 공급자 로그·홈 전체·Docker 소켓·자격증명은 컨테이너에 마운트하지 않음. GPU는 호스트 nvidia-smi를 프로브가 읽음. DB는 별도 named volume. Web은 기본 127.0.0.1:8787 바인딩. 외부 데이터 전송 없음.

스냅샷 기본 구조(확장 가능, 누락/None은 미확인):

```json
{
  "schema_version": 1,
  "collected_at": "ISO8601 UTC",
  "agents": [
    {"id":"codex","name":"Codex","model":"gpt-6-astra","status":"observed","source":"local session usage","observed_at":"ISO8601 UTC","plan":{"name":"prolite","source":"account API","observed_at":"ISO8601 UTC","limits":[{"label":"weekly","used_percent":7,"reset_at":"ISO8601 UTC"}]},"usage":{"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"reasoning_tokens":null,"total_tokens":0,"cost_usd":null,"sessions":0,"window":"available local history"},"models":[{"model":"gpt-6-astra","input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"total_tokens":0,"sessions":1}],"notes":[]}
  ],
  "hardware":{"hostname":"local","cpu_count":20,"cpu_percent":null,"memory_total_bytes":128000000000,"memory_used_bytes":0,"memory_used_percent":0,"gpu":[{"name":"NVIDIA GB10","driver_version":"595.58.03","power_watts":14.62,"power_limit_watts":null,"memory_used_bytes":null,"memory_total_bytes":null,"utilization_percent":10,"temperature_c":54,"memory_note":"GB10 unified memory; dedicated VRAM counters unavailable"}],"inference":{"endpoint":"localhost:8000","reachable":true,"models":["Qwen3.8-Flash-Next-IQ3_S"],"engine":null,"version":null},"notes":[]},
  "skills":{"repository":[{"name":"herdr-workflows","path":"skills/herdr-workflows/SKILL.md","description":"..."}],"agents":[{"agent":"codex","installed_count":0,"enabled_count":null,"source":"...","observed_at":"ISO8601 UTC","skills":[{"name":"archify","path":"~/.codex/skills/archify/SKILL.md","enabled":true,"origin":"local","invocations":null,"last_used_at":null,"usage_evidence":"not instrumented"}]}],"notes":[]},
  "errors":[]
}
```

수집기는 위 필드를 유지합니다. `agents`는 codex/claude/opencode/antigravity 네 항목입니다. `models`별 토큰의 합계를 `usage`로 제공합니다. `input_tokens`는 캐시를 포함한 입력이며 캐시를 또 더하지 않습니다. 추론 토큰은 출력의 부분집합입니다. 모델을 바꾼 세션은 모델별로 나타날 수 있어 에이전트 전체 세션 수는 모델별 합계가 아닙니다. UI는 원문 JSON 대신 의미 있는 항목과 단위를 표시합니다.

## 品質要件

- 차분한 다크 UI와 한국어 왼쪽 메뉴 3개. 모델별 사용량 표, 실제 GPU 그래프, 스킬 검색/에이전트 필터. 모바일에서도 사용 가능.
- 미확인·미지원·오래된 값과 0을 구분. GB10 VRAM N/A를 0으로 변환하지 않으며 공유 메모리를 GPU 전용 사용량으로 표시하지 않음.
- 구독 이용률은 계정 API 또는 관측값만 사용. 로컬 토큰에서 구독 이용률을 계산하지 않음. 출처·시각 표시, 과거 preflight 값은 이력으로 명시.
- 설치·활성 설정·호출 증거를 구분. 미계측을 미사용으로 표시하지 않음.
- SQLite 시계열과 GPU 그래프 제공. 같은 스냅샷을 반복 삽입하지 않고 저장 기간/건수 제한. 누적 토큰 스냅샷을 시계열 간 합산하지 않음.
- `/health`, `/api/snapshot`, `/api/history` 제공. 스냅샷 미도착은 대기 상태. 외부 문자열은 HTML 이스케이프.
- OTel Collector/Prometheus ARM64 고정 버전, 실제 건강 상태 확인, 의존성 고정. README에 시작/종료/재시작과 수집 제약 설명.
- 코드와 의미 있는 테스트를 완성. 권한이 막히면 정확한 사유 보고. 공통 지침 준수, graft init/build 금지.
