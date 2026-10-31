# 2026-10-31 Codex 스킬 점검

범용 SW 개발을 기준으로 한 **활성 목록 정리**입니다. 모든 스킬의 품질·최신성·사용 빈도를 평가한 감사는 아닙니다. 언어·프레임워크를 특정하지 않는다는 사용자 선택을 반영했습니다.

후속 정정: 사용자는 **Ponytail 스킬을 모두 사용**한다고 명시했습니다. 6개를 복구해 현재 활성 35개·비활성 328개이며, 향후 프로필에서 사용자 필수로 보존합니다. 아래 29개/334개 수치는 최초 적용 이력입니다. 사용자는 남은 화면 경고가 **skill budget 초과**임을 확인했으며, 경고 조치보다 정리 기준의 타당성을 먼저 검토하도록 요청했습니다. 오른쪽 Herdr 패널의 [Opus 5.5 high 독립 검토](opus-skill-review-2026-10-31.md)를 완료했으며, 아래 최초 선정 근거 중 Ponytail 오분류·완료 검증의 완전 대체 주장·수량 목표는 수정됐습니다.

## 경고 확인

- 환경: Codex CLI 0.166.0, 새 세션 시작 2026-10-31 10:20:09 KST.
- 새 세션 시작 구간의 로그에서 기존 스킬 파싱·설정 오류는 발견되지 않았습니다.
- 10:21:07의 `codex_skills_extension::render` 로그에는 예산 5,440에서 후보 372개 중 312개 포함, **60개 누락**, 372개 설명 축소가 기록됐습니다. 이 기록의 레벨은 `INFO`입니다. WARN이 없다는 사실과 스킬 목록이 온전하다는 사실은 다릅니다.
- 별도로 로컬 `codex app-server`의 `skills/list(forceReload=true)`를 실행한 결과 **363개, 활성 363개, 파싱 오류 0개, stderr 빈 값**이었습니다. App 세션의 원격/통합 카탈로그와 별도 로컬 CLI의 발견 범위가 다르므로 372와 363을 같은 분모로 계산하지 않습니다.
- 점검 과정에서 보호된 `/tmp/systemd-private-*` 경로 접근에 따른 sandbox WARN과, 샌드박스 안의 CLI 실행에서 PATH 별칭 생성 경고가 발생했습니다. 샌드박스 밖에서 재실행한 로컬 스킬 로딩 검사에는 경고가 없었습니다. 과거 로그를 삭제하거나 시스템 보안 정책을 변경하지 않았습니다.

## 활성 목록 선정

로컬 발견 363개에서 **29개 유지, 334개 비활성화**하는 프로필입니다. 사람이 읽을 수 있는 [전체 변경 목록과 판단의 한계](skill-changes-2026-10-31.md), [JSON 프로필](../distribution/profiles/codex-general-sw.json)을 제공합니다. 파일 삭제·이동, 플러그인 제거, 플러그인 hooks/MCP 변경은 하지 않습니다. Codex 사용자 설정의 `[[skills.config]]`에 이름별 `enabled = false`만 기록합니다.

| 유지 그룹 | 스킬 |
| --- | --- |
| 설계·코드 이해 | `ecc:api-design`, `ecc:architecture-decision-records`, `ecc:codebase-onboarding`, `ecc:coding-standards` |
| UI 품질·보안 | `ecc:accessibility`, `ecc:browser-qa`, `ecc:security-review` |
| 운영·데이터·실패 처리 | `ecc:database-migrations`, `ecc:deployment-patterns`, `ecc:docker-patterns`, `ecc:error-handling` |
| Git·유지 관리 | `ecc:git-workflow`, `ecc:github-ops`, `ecc:skill-stocktake` |
| 디버깅·테스트·완료 검증 | `superpowers:systematic-debugging`, `superpowers:test-driven-development`, `superpowers:verification-before-completion` |
| 개인 기술 문서·도구 | `archify`, `docx`, `pdf`, `humanize-korean`, `herdr`, `prefer-gh-for-github` |
| 시스템·기본 플러그인 | `imagegen`, `openai-docs`, `review-agent`, `skill-creator`, `skill-installer`, `visualize:visualize` |

사용자 관리 스킬 23개와 시스템/기본 플러그인 6개입니다. 접근성·DB·배포 등도 실제 해당 작업에서만 적용하며, 기본 활성화 자체가 매 작업의 필수 절차라는 뜻은 아닙니다.

| 기본 비활성 사유 | 예시·대체 경로 |
| --- | --- |
| 현재 업무와 거리가 있는 분야 | 의료·임상·금융 거래·물류·영업·마케팅·소셜 게시·영상 제작은 해당 업무가 생길 때 다시 활성화 |
| 특정 기술 스택 | Python/Django, Java/Spring, React/Next, Kotlin, Rust 등의 전문 스킬은 프로젝트 스택을 확인한 뒤 활성화 |
| 절차 중복 | `ecc:tdd-workflow`, `ecc:verification-loop`는 이번 기본 구성에서 Superpowers의 TDD·완료 검증으로 대체 |
| 무거운 오케스트레이션·강제 트리거 | 다중 에이전트·상시 학습·자동 루프·`superpowers:using-superpowers`는 명시적으로 필요할 때 활성화. `herdr`는 유지 |
| 환경 의존 | `ecc:documentation-lookup`은 Context7, `ecc:security-scan`은 Claude 설정용 AgentShield에 특화되어 기본 목록에서 제외. 일반 문서 조사는 공식 검색, 코드 보안은 `ecc:security-review` 사용 |
| 선택적 산출물 | `pptx`, `xlsx`, `web-slides`는 발표·스프레드시트 작업 시 활성화. 기술 문서·PDF·아키텍처 시각화는 유지 |

## 범위와 재검증

이번 설정 변경은 **Codex**에 적용합니다. Claude/Gemini/OpenCode의 제한은 README에 비교했지만 해당 앱의 사용자 설정이나 공유 스킬 디렉터리는 변경하지 않습니다. 특히 Claude Code의 `skillOverrides`는 플러그인 스킬에 적용되지 않으므로, Codex 방식으로 ECC 개별 스킬을 끌 수 있다고 가정하지 않습니다. [Claude 공식 문서](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings)

2026-10-31 10:30 KST 적용 완료. 로컬 `skills/list(forceReload=true)` 재검증에서 **전체 363개, 활성 29개, 비활성 334개, 오류 0개, stderr 빈 값**을 확인했습니다. 활성 이름 집합도 JSON 프로필과 정확히 일치합니다. 설정의 모델·권한·플러그인 항목 보존, 재적용 미리보기의 변경 없음, 임시 디렉터리에서 적용→원본 바이트 그대로 복구까지 검증했습니다. 문서의 로컬 링크와 TOML/Python 구문도 확인했습니다.

이 머신의 백업은 `~/.codex/backups/skills-general-sw-20261031T013040.931048Z/`에 있습니다. 설정 백업은 저장소에 넣지 않습니다.

이미 시작한 대화의 스킬 지침은 소급 제거되지 않으며, Codex App의 원격/기본 스킬까지 포함한 최종 노출 목록은 새 세션에서 확인해야 합니다. 새 플러그인 버전에서 새로 생긴 이름은 이 스냅샷에 없으므로 다시 점검합니다.

적용과 복구 절차는 [배포 문서](../distribution/README.md#codex-범용-sw-개발-프로필)를 참고하세요.
