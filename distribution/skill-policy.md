# 공통 스킬 사용 정책

2026-10-31, Codex와 오른쪽 Herdr 패널의 Claude **Opus 5.5 / high**가 합의한 범용 SW 개발 기준입니다. [전체 사용 목록](skill-list.md)은 JSON 프로필에서 생성하며, 공급업체 캐시를 삭제하거나 수정하지 않습니다.

## 선정 기준

1. **필수:** 사용자 지정 `graft`, `archify`, Ponytail 6개는 네 에이전트 모두 설치·보존합니다. 개수 감축을 위해 제외하지 않습니다.
2. **기본 유지:** API·설계·코드 탐색·디버깅·테스트·보안·Git·배포와 이미 사용하는 범용 기능을 유지합니다. 현재 목록도 일부 본문과 설명에 근거한 운영안이지 전체 호환성 인증은 아닙니다.
3. **프로젝트별 사용:** 언어·프레임워크·DB·인프라 전문 스킬은 해당 작업에서 켭니다. Python도 같은 기준입니다. 본문 확인 전 스택은 목록에서 `needs-review`로 남기고, 프로젝트에서 필요와 호환성을 확인해 켤 때 `on-demand`로 옮깁니다. 일반 DB 마이그레이션·배포·Docker 워크플로는 현재 기본 예외로 유지합니다.
4. **호환성/중복 제외:** 실제 도구·하네스 전제가 맞지 않거나 목적이 겹치는 흐름을 상시 노출에서 제외합니다. 특정 MCP가 정적 설정에 없다는 사실만으로 부재를 단정하지 않습니다.
5. **검토 보류:** 본문·사용 필요를 확인하지 못한 항목은 불필요하다고 단정하지 않습니다. 이전 일괄 제외 상태를 승계하되, 필요한 프로젝트에서 재검토·복구합니다. 의료·물류·영업 등 비개발 도메인도 사용자 작업과 관계가 확인되면 재평가합니다.

고정된 20~30개 목표는 폐기했습니다. 예산 부족은 목록 메타데이터와 실제 렌더링으로 판단합니다. TDD 기능 중복과 달리 `verification-loop`는 증거 확인 스킬의 보완 후보입니다. `pptx`, `xlsx`, `web-slides`, 벤치마크, 계획/리뷰 계열도 보류 상태이지 불필요 확정이 아닙니다.

## 네 에이전트 공통 적용

사용자의 동일 적용 요구에 따라 **공통 36개**를 [common-general-sw.json](profiles/common-general-sw.json)에서 관리합니다. 이전의 Claude ECC 전체 노출 예외는 폐기했습니다. [Opus 재검토](../test/monitor/common-skill-review.md)에 근거해 선택 목록, 실제 호출 이름, 도구 전제조건을 구분합니다.

| 대상 | 공통 선택 | 실제 적용 |
| --- | --- | --- |
| Codex | 36개 | 기존 35개 + herdr-orchestrate. 원본 캐시 보존, 비선택 목록은 비활성 |
| Claude | 36개 | ECC 13개는 `ecc-common:*` 로컬 플러그인. 원본 ECC off, 훅·스크립트·보조 파일·에이전트 보존. docx/pdf 등은 기존 호스트 구현에 매핑 |
| OpenCode | 36개 | 동일 디렉터리 배포 + 명시 allowlist. 내장 opencode/report는 별도. 로컬 Qwen을 기본 모델로 설정 |
| Antigravity | 36개 | `~/.gemini/antigravity-cli/skills/`에 동일 선택 목록 배포. Gemini CLI는 제거된 이전 시험 대상 |

공통 목록과 플랫폼 내장·앱·보조 명령의 개수를 섞지 않습니다. Codex 앱이 추가하는 템플릿·페이지 스킬, Claude의 내장/플러그인 보조 명령은 공통 선택 수가 아닙니다. 대시보드는 공통 선택·발견·활성 확인·추가 항목·미확인을 분리합니다. 등록·설정·실행 성공은 각각 다른 증거입니다.

MCP도 [공통 3개 프로필](profiles/common-mcp.json)(Git, GitHub, Chrome DevTools)을 네 에이전트에 동일하게 적용합니다. 제품 내부의 앱 OAuth·렌더링·원격제어 연결은 외부 도구로 복제할 수 없으므로 플랫폼 기능으로 따로 표시합니다. 새 프로세스가 설정을 읽었는지와 실제 읽기 도구 호출을 구분해 검증합니다.

## 필수 스킬의 예외와 실행 조건

Ponytail은 과잉 설계 방지·YAGNI·리뷰·감사·부채·도움말·효과 안내 기능입니다. 앞서 자동화 중복으로 분류한 것은 잘못된 판단이었습니다. `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`를 모두 보존합니다.

`graft`의 강한 전역 트리거는 사용자 필수 예외입니다. 외부 원본을 수정하지 않고, [공통 실행 조건](../instructions/common.md#전역-스킬-실행-조건)을 네 전역 지침에 배포합니다. CLI가 설치됐다는 사실과 각 저장소에 색인이 있다는 사실을 구분합니다. `graft init`과 색인 생성은 수행하지 않습니다. 모니터링 시험의 MCP·statusline 변경은 별도 설치기와 백업으로 관리합니다.

`browser-qa`는 실제 브라우저 도구가 있는 Codex 환경에서 유지하지만 개별 API 호환성은 미검증입니다. `imagegen`·`visualize`는 실제 생성 도구/인라인 표면이 없으면 실행 불가로 취급합니다. `skill-installer`는 현재 호스트의 명시적 `--dest`가 필요합니다. [공통 실행 조건](../instructions/common.md)을 함께 배포합니다. 필수 항목은 네 로더에서 발견됐지만 모든 워크플로의 실행까지 시험한 것은 아닙니다.

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
