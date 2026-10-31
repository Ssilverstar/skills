# Claude 총괄 + Gemini/OpenCode 작업자

2026-10-31 Herdr 0.9.5에서 확인한 로컬 운영 절차입니다. 사용자 요청이 이 구조일 때 사용하며 모든 개발 작업의 기본값으로 강제하지 않습니다.

```text
Codex                 | Claude / Opus        | Agents
독립 검증·운영 계측    | 설계·계약·위임·통합  | OpenCode / Qwen: TC·검증
                      |                      | Antigravity / Gemini: 구현
```

1. `HERDR_ENV=1`과 현재 작업 공간·패널을 확인합니다. 설치된 Herdr 스킬과 [보완 스킬](../../skills/herdr-orchestrate/SKILL.md)을 읽습니다.
2. [검증된 배치 방법](../../skills/herdr-orchestrate/references/layout.md)으로 3열을 만들고, 오른쪽만 위아래로 나눕니다. 사용자 포커스는 원래 패널에 유지합니다.
3. Claude를 총괄로 명시하고 작업자 ID·실제 모델·소유 파일을 전달합니다. Codex가 패널을 준비했어도 Gemini/OpenCode의 구현 프롬프트는 Claude가 직접 발행합니다.
4. Claude가 [작업 계약](../../skills/herdr-orchestrate/references/contracts.md)을 정하고, 독립된 구현과 검증을 병렬 위임합니다. 공통 API는 Claude가 소유합니다. 충돌 파일이 생기면 소유권부터 재조정합니다.
5. Claude는 상태 전환·승인·결과 도착을 관찰합니다. `idle`만으로 완료라고 판정하지 않고 실제 화면/결과를 확인합니다. 원래 사용자 승인 범위 안의 좁은 권한만 처리합니다.
6. 작업자 결과의 실제 파일과 테스트 증거를 확인하고, 통합 후 독립 AC/E2E 검증을 수행합니다. 실패를 숨기거나 테스트를 약하게 바꾸지 않습니다.
7. 사용자 요청에 따라 패널을 유지하거나 명시한 패널만 종료하고 최종 배치를 확인합니다. 실행한 서버와 종료한 작업자 프로세스를 구분해 보고합니다.

이번 시험의 구체 계약은 [monitor/contracts/](../../test/monitor/contracts/)에 있습니다. 이는 같은 작업 디렉터리에서 파일 소유권을 나눈 실행이며, 격리 worktree 비교 시험을 완료한 것은 아닙니다.

회사 제안의 Gemini CLI·GLM은 집에서 사용자 결정에 따라 Antigravity/Gemini 3.8 Flash·OpenCode/Qwen3.8으로 대체했습니다. 이 대체를 회사 승인이나 모델 성능 동등성으로 일반화하지 않습니다. 실제 로컬 추론 엔진은 vLLM 이미지 안의 `llama-server`입니다.

상태·토큰·재시도·사용자 수정 지시는 `test/`에 비식별 기록합니다. 결과가 있는 현재 실행과 실행하지 않은 단독/다른 총괄 방식을 나누어 비교하며, 기준 실행 없이 절감률을 주장하지 않습니다.
