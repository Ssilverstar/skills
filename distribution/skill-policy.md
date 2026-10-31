# 공통 스킬 사용 정책

2026-10-31, Codex와 오른쪽 Herdr 패널의 Claude **Opus 5.5 / high**가 합의한 범용 SW 개발 기준입니다. [전체 사용 목록](skill-list.md)은 JSON 프로필에서 생성하며, 공급업체 캐시를 삭제하거나 수정하지 않습니다.

## 선정 기준

1. **필수:** 사용자 지정 `graft`, `archify`, Ponytail 6개는 네 에이전트 모두 설치·보존합니다. 개수 감축을 위해 제외하지 않습니다.
2. **기본 유지:** API·설계·코드 탐색·디버깅·테스트·보안·Git·배포와 이미 사용하는 범용 기능을 유지합니다. 현재 목록도 일부 본문과 설명에 근거한 운영안이지 전체 호환성 인증은 아닙니다.
3. **프로젝트별 사용:** 언어·프레임워크·DB·인프라 전문 스킬은 해당 작업에서 켭니다. Python도 같은 기준입니다. 본문 확인 전 스택은 목록에서 `needs-review`로 남기고, 프로젝트에서 필요와 호환성을 확인해 켤 때 `on-demand`로 옮깁니다. 일반 DB 마이그레이션·배포·Docker 워크플로는 현재 기본 예외로 유지합니다.
4. **호환성/중복 제외:** 실제 도구·하네스 전제가 맞지 않거나 목적이 겹치는 흐름을 상시 노출에서 제외합니다. 특정 MCP가 정적 설정에 없다는 사실만으로 부재를 단정하지 않습니다.
5. **검토 보류:** 본문·사용 필요를 확인하지 못한 항목은 불필요하다고 단정하지 않습니다. 이전 일괄 제외 상태를 승계하되, 필요한 프로젝트에서 재검토·복구합니다. 의료·물류·영업 등 비개발 도메인도 사용자 작업과 관계가 확인되면 재평가합니다.

고정된 20~30개 목표는 폐기했습니다. 예산 부족은 목록 메타데이터와 실제 렌더링으로 판단합니다. TDD 기능 중복과 달리 `verification-loop`는 증거 확인 스킬의 보완 후보입니다. `pptx`, `xlsx`, `web-slides`, 벤치마크, 계획/리뷰 계열도 보류 상태이지 불필요 확정이 아닙니다.

## 네 에이전트에 적용하는 차이

| 대상 | 이번 적용 | 예외와 검증 범위 |
| --- | --- | --- |
| Codex 0.166.0 | [프로필](profiles/codex-general-sw.json): 35 활성 / 329 비활성. `graft` 추가, `ecc:skill-stocktake` 제외 | 파일·플러그인·훅 보존. 로컬 364개 기준이며 App 원격 카탈로그는 별도. 전체 본문 검토 완료 아님 |
| Claude Code 2.1.314 | 필수 8개 유지/보완 설치. 기존 플러그인과 앱 동기화 스킬 보존 | `skillOverrides`는 플러그인 스킬에 적용되지 않음. ECC 전체를 끄면 훅도 사라지므로 **ECC 전체 노출 예외**. `skill-stocktake` 등 Claude 전용 스킬은 이 환경에서 호환 가능 |
| Gemini CLI 0.66.0 | 기존 3개 유지 + 필수 8개 추가 = 11개 발견 | 기존 과다 목록 없음. 다른 에이전트의 모든 기본 스킬을 새로 복제하지 않음. 프로젝트 신뢰 설정은 변경하지 않음 |
| OpenCode 2.2.5 | 필수 8개 발견. [프로필](profiles/opencode-general-sw.json)로 Superpowers 11개만 차단 | 등록 39개, `build` 권한 평가상 27개 허용. 이번 차단 11개 외에 내장 `browser`는 기존 자체 규칙으로 차단. 앱 동기화 원본은 보존 |

같은 선정 기준과 필수 목록을 적용하며, 에이전트별 내장 기능·플러그인 제약 때문에 전체 개수가 같지는 않습니다. 미설치된 모든 Codex 기본 스킬을 다른 에이전트에 일괄 신규 설치하는 정책은 아닙니다.

OpenCode에서 차단하는 Superpowers 11개는 Codex에서 제외된 동일 항목입니다. `systematic-debugging`, `test-driven-development`, `verification-before-completion`은 유지합니다. 계획·리뷰 스킬의 차단은 보류 운영안이며, 각각이 불필요하다는 결론이 아닙니다.

## 필수 스킬의 예외와 실행 조건

Ponytail은 과잉 설계 방지·YAGNI·리뷰·감사·부채·도움말·효과 안내 기능입니다. 앞서 자동화 중복으로 분류한 것은 잘못된 판단이었습니다. `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`를 모두 보존합니다.

`graft`의 강한 전역 트리거는 사용자 필수 예외입니다. 외부 원본을 수정하지 않고, [공통 실행 조건](../instructions/common.md#전역-스킬-실행-조건)을 네 전역 지침에 배포합니다. CLI가 설치됐다는 사실과 각 저장소에 색인이 있다는 사실을 구분합니다. 이번 작업은 스킬 파일 설치이며 `graft init`, 색인 생성, 훅·MCP·statusline 변경을 수행하지 않습니다.

`browser-qa`는 실제 브라우저 도구가 있는 Codex 환경에서 유지하지만 개별 API 호환성은 미검증입니다. `imagegen`, `review-agent`, `visualize` 등 플랫폼 전용 항목을 다른 에이전트에 그대로 복사하지 않습니다. 필수 항목은 네 로더에서 발견됐지만 모든 워크플로의 실행까지 시험한 것은 아닙니다.

## 목록을 바꾸는 방법

- Codex 목록의 원본은 [JSON 프로필](profiles/codex-general-sw.json)입니다. `enabled`/`disabled`, `classification`, `user_required`를 함께 갱신합니다.
- 분류는 `required`, `core-partially-reviewed`, `on-demand`, `excluded-compat-codex`, `excluded-overlap-or-trigger`, `needs-review`입니다.
- `python3 distribution/render_skill_list.py`로 읽기용 목록을 생성하고 `--check`로 일치 여부를 확인합니다.
- [적용·복구 절차](README.md)를 따라 미리보기 후 적용하고 각 로더에서 확인합니다. OpenCode 규칙도 해당 이름과 함께 갱신합니다.
- 새 스킬 이름은 자동 차단하지 않습니다. 사용자 필수 항목 제거는 사용자 지시가 바뀌었을 때만 합니다.
- 프로젝트별 활성화는 각 도구가 지원하는 범위·우선순위를 확인합니다. 특히 Codex 전역 이름 차단은 같은 이름의 프로젝트 스킬에도 영향을 줄 수 있으므로, 단순히 프로젝트에 복사한 것으로 활성화를 가정하지 않습니다.

## 확인 근거

- [최종 적용·검증 기록](../docs/skill-set-agreement-2026-10-31.md)
- [초기 정리와 Opus의 반론](../docs/opus-skill-review-2026-10-31.md)
- [Claude 스킬 관리](https://code.claude.com/docs/en/skills), [Gemini 스킬 관리](https://geminicli.com/docs/cli/skills/), [OpenCode V2 스킬 관리](https://dev.opencode.ai/v2/docs/skills/)
