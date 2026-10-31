# 사내 제안과 집 환경 비교

> 아래는 본 시험 전 환경 비교입니다. 이후 공통 스킬 36개·MCP 3개를 적용하고 모니터링 웹앱을 검증했습니다. 최종 상태·잔여 제약·패널 정리는 [최종 보고](final-report.md)를 기준으로 봅니다.

2026-10-31 점검. 사내 조건은 사용자가 제공한 `user-guide/Codex_MultiAgent_Development_Guide.md`의 **제안 전제**이며 회사 시스템에서 확인한 값은 아닙니다. 집 환경은 로컬 CLI·API·패널로 확인했습니다. 성능 비교 시험은 아직 시작하지 않았습니다.

| 항목 | 사내 제안 | 현재 집 | 시험에 미치는 차이 |
| --- | --- | --- | --- |
| Claude | Opus 5.5, 월 $466 할당 | Claude Code 2.1.314, Opus 5.5 high, Claude Pro OAuth | 회사 달러 할당과 구독 사용 한도를 임의 환산할 수 없음 |
| Google 작업자 | Gemini CLI 3.8 계열, 일 2,000 모델 요청 | Gemini CLI 개인 인증 경로 지원 종료 확인 → 사용자 요청으로 제거, Antigravity CLI 1.4.12 설치 | 클라이언트·도구·인증·과금 단위가 달라짐. 사내에서도 Antigravity가 승인됐다고 가정하지 않음 |
| Google 모델 | 정확한 모델 ID 미정 | Antigravity의 `gemini-3.8-flash-medium`, Google AI Pro. 파일 읽기·산술 응답 확인 | 같은 이름/세대라도 실제 공급 모델을 별도 확인해야 함 |
| OpenCode | v2 + 사내 vLLM + GLM-5.3 Flash | OpenCode 2.2.5 + 로컬 `llm-server/Qwen3.8-Flash-Next-IQ3_S` | 모델·양자화·컨텍스트·추론 엔진이 다름. 집 결과로 사내 GLM 성능을 예측하지 않음 |
| Codex | 회사 3,000크레딧 | ChatGPT 로그인, account/read 및 rateLimits API의 플랜 식별자 `prolite`, 주간 창 사용률 7% 관측 | 내부 플랜 식별자를 청구 상품명·가격으로 단정하지 않음. 회사 크레딧과 환산 불가 |
| 추론 장비 | GPU·양자화·동시 처리량 미확인 | Linux ARM64, CPU 20개, RAM 약 119.6GiB, NVIDIA GB10. Qwen은 localhost:8000의 OpenAI 호환 공급자 | 로컬 호출에 외부 토큰 청구가 없어도 전력·GPU 점유·대기 시간은 비용 |
| 병렬 실행 | Opus 1 + Gemini 최대 2 + GLM 최대 1 | 네 에이전트 점검 후 사용자 요청으로 Codex 패널 하나만 유지 | 본 시험 때 신규 세션과 병렬 수를 맞춰야 함 |
| 스킬·MCP | 실제 설치/사내 승인 범위 미확인 | 사용자 필수 8개 보존. 도구별 내장·앱 카탈로그와 MCP 구성이 다름 | 동일 이름 수가 아니라 필요한 기능·권한·실제 호출 성공을 비교 |

## 현재 판정

- **Claude:** 응답, 공개 파일 읽기, ponytail-help 로드, git MCP 호출 성공. Pro 플랜 및 세션18%·주간3% 사용 관측. Bash 1회는 기존 GateGuard 훅에 막혔고 Read 도구로 완료. graft 전역 지침은 신규 세션에서 적용 확인 필요.
- **Codex:** 이 세션에서 모델·셸·git MCP 동작 확인. 로더는 394개 중 65개 활성, 필수 8개 누락 없음. 기존 합의 프로필 35개 외에 앱/템플릿 스킬 30개가 추가 노출된 상태이며 임의 삭제하지 않았습니다. 사용자가 skill budget 경고 해소를 확인했습니다.
- **OpenCode/Qwen:** 파일 읽기 1회와 응답 성공. 필수 8개가 카탈로그에 표시됨. MCP 서버는 미설정이며 연결 실패와 구분합니다. 패널 표시 35.4초·18.5 tok/s는 단 한 번의 smoke 관측으로 벤치마크가 아닙니다.
- **Antigravity:** Google AI Pro 로그인, Gemini 3.8 Flash (Medium) 선택, 실제 파일·산술 응답과 ponytail-help 원문 읽기 성공. 필수 8개 인식 확인. MCP 미설정, 잔여 한도 미확인. 비대화형 실행은 파일 읽기 승인 정책을 별도로 준비해야 합니다.

## 본 시험 전에 맞출 조건

1. Antigravity 잔여 한도와 시험 파일의 비대화형 읽기 권한 확인. 로그인·모델·플랜은 확인 완료.
2. 각 실행은 신규 세션에서 시작하고, 시작 커밋·공개 합성 과제·품질 게이트를 고정.
3. 스킬·MCP·규칙·캐시의 차이를 실행 기록에 남김. 제어하지 못한 서버 캐시를 제거했다고 주장하지 않음.
4. 작업당 완료 시간·수정 횟수·품질 통과·실제 사용량을 기록. 회사의 $466/3,000크레딧/2,000요청과 집 지표를 임의 환산하지 않음.

근거: [Claude 점검](claude-preflight.md), [Codex 비식별 API 결과](results/codex.json), [Antigravity 전환 기록](antigravity-migration.md).

계정 조회 정정: 처음 기록한 Codex RPC timeout은 점검기의 `select()`와 Python 텍스트 버퍼 조합에서 발생했습니다. 큐 기반 수신으로 수정 후 계정 조회가 즉시 성공했으며, Codex 인증 장애로 판정하지 않습니다.
