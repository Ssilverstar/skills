# 수집 및 OpenTelemetry 근거

2026-10-31 확인. 실제 환경에서 확인한 결과를 우선하고, 아래 공식 문서는 계측 경로의 근거로 사용했습니다.

- [OpenTelemetry Collector 구성](https://opentelemetry.io/docs/collector/configuration/): OTLP 수신과 지표·트레이스 파이프라인의 연결. 이 앱은 OTel SDK로 수집한 집계값을 로컬 Collector에 전달하고 Prometheus로 조회합니다.
- [Claude Code 모니터링](https://code.claude.com/docs/en/monitoring-usage): Claude의 네이티브 OTel 계측은 별도 설정으로 활성화할 수 있습니다. 이번 구현은 기존 세션까지 포함하기 위해 로컬 로그를 집계해 OTel로 내보내는 브리지를 사용하며, 모든 에이전트의 네이티브 텔레메트리를 켰다고 주장하지 않습니다. 캐시 읽기·쓰기가 API 입력 카운트와 별개라는 의미 규칙을 확인했습니다.
- Codex: 설치된 0.166.0의 app-server `account/read`, `account/rateLimits/read`, `skills/list`를 읽기 전용으로 조회. 토큰은 현재 로컬 `token_usage_record`의 응답 ID별 집계. 공급업체가 반환하지 않는 달러 가격은 추정하지 않습니다.
- OpenCode: 설치된 V2의 `/api/skill` 등록 목록과 SQLite `session_message` 사용량을 읽음. 등록 목록이 최종 에이전트 권한상 허용 목록과 같은 것은 아닙니다.
- [Antigravity /usage](https://antigravity.google/docs/cli/commands/usage) 및 [1.4.x 변경 이력](https://github.com/google-antigravity/antigravity-cli/blob/main/CHANGELOG.md): 설치된 1.4.12에서 `agy --output-format json --print /usage`의 구조화된 quota 그룹 조회를 확인했습니다. 실제 응답은 num_turns=0이며 모델 호출 없이 잔여 한도를 제공합니다.
- [Antigravity 상태줄](https://antigravity.google/docs/cli/statusline/): 공식 입력/출력 세션 누적 필드를 선별 저장합니다. 이메일·제목·본문·원문 페이로드는 저장하지 않습니다. 누적 캐시와 과거 모델별 사용량 분해는 지원하지 않습니다.
- [Claude 상태줄](https://code.claude.com/docs/en/statusline): `rate_limits`의 실제 5시간/7일 사용률과 갱신 시각을 받습니다. 기존 사용자의 상태줄 명령과 출력은 래퍼 안에서 그대로 보존합니다. 관측된 한도는 사용자 활동 시 갱신되므로 항상 관측 시각과 함께 표시합니다.
- GPU: 호스트 `nvidia-smi --query-gpu=... --format=csv,noheader,nounits`에서 GB10 전력·온도·이용률을 읽었습니다. 전용 메모리 `[N/A]`는 null로 유지하고 `/proc/meminfo` 시스템 메모리와 구분합니다.
- 추론: `docker inspect llm-server`의 실행 파일은 `/src/build/bin/llama-server`, 이미지는 `nvcr.io/nvidia/vllm:26.09-py3`. `/v1/models`, `/props`로 실제 모델과 빌드를 확인합니다. `installed_vllm_version`은 컨테이너에 설치된 패키지 버전이며 현재 실행 엔진 버전이 아닙니다.
