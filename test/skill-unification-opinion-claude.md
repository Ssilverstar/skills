# 공통 스킬 통일 의견 (Claude, 읽기 전용 교차 검토, 2026-10-31)

근거: `distribution/profiles/codex-general-sw.json` `enabled` 35개 ↔ 이 Claude 세션에 실제 노출된 스킬 이름(세션 시작 시 스킬 목록). 전역 설정은 수정하지 않았고, 다른 에이전트는 실측하지 않았다(Codex 감사 범위).

## 35개 분류

| 분류 | 개수 | 항목 | Claude 현황 |
|---|---|---|---|
| 이식 가능 · 이미 노출 | 28 | archify, graft, herdr, ponytail×6, humanize-korean, prefer-gh-for-github, skill-creator, docx, pdf, ecc: accessibility·api-design·architecture-decision-records·browser-qa·codebase-onboarding·coding-standards·database-migrations·deployment-patterns·docker-patterns·error-handling·git-workflow·github-ops·security-review | 노출됨. 단 docx/pdf는 `anthropic-skills:` 접두, humanize-korean은 `humanize-korean:` 접두라 **이름이 에이전트마다 다름** |
| 이식 가능 · 미노출 | 3 | superpowers: systematic-debugging, test-driven-development, verification-before-completion | Claude 목록에 없음. 일반 SKILL.md라 사용자 스킬로 복사 가능(도구 전제 확인 필요) |
| 플랫폼 전용 | 5 | imagegen, openai-docs, review-agent, skill-installer, visualize:visualize | Codex 도구·문서를 전제. 그대로 복사하면 실행 불가 또는 오동작. Claude 대응물: claude-api(문서), code-review(리뷰), skill-creator(설치·작성), dataviz/artifact(시각화), 이미지 생성 대응 없음 |

## 권장: "공통 30 + 플랫폼 native 매핑" (portable adapter보다 우선)

1. **공통 목록 = 이식 가능 31개**(28 + superpowers 3). 네 에이전트 모두 같은 *기능 ID*로 노출을 맞춘다. LIST에 `common_id → 에이전트별 실제 이름`(접두 차이) 열을 둔다.
2. **플랫폼 전용 5개는 "native 대응" 열**로 표시만 한다(예: review-agent ↔ Claude `code-review`, OpenCode/Antigravity는 해당 시 기재, 없으면 `n/a`). 복사·래핑하지 않는다.
3. portable adapter(공통 래퍼 SKILL.md가 도구 차이를 흡수)는 **도구 자체가 없는 경우(이미지 생성 등) 해결 불가**하고, 래퍼 유지 비용이 생긴다. 필요해지는 특정 항목에만 한정 적용.
4. 필수(graft, archify, Ponytail 6)는 공통 목록에 고정.

## Claude "활성 스킬 과다"의 원인과 정리 방향

- 원인: 기존 정책의 **ECC 전체 노출 예외**(`skillOverrides`가 플러그인 스킬에 적용되지 않아 ECC를 끄면 훅도 꺼짐). 이 세션에서도 `ecc:*` 수백 개가 노출됨.
- 검토 중인 **ECC filtered local plugin**(skills는 공통 선별분만, hooks/agents/MCP는 보존)은 방향이 맞다. 주의점:
  - 원본 ECC 플러그인을 **비활성화**하고 filtered 플러그인만 활성화해야 훅·에이전트가 **중복 실행되지 않는다**.
  - hooks/MCP 설정이 `${CLAUDE_PLUGIN_ROOT}` 기준 경로를 쓰면 filtered 플러그인 안에 해당 스크립트가 있어야 한다(심볼릭 링크 시 업데이트 추적, 복사 시 재동기화 스크립트 필요).
  - 원본 캐시는 삭제하지 않고 버전 고정·재생성 절차를 LIST 옆에 기록.
  - 적용 후 확인: 새 세션 스킬 목록 수, 훅 1회 실행(중복 없음), 필수 8개 호출 가능.
- 전역 설정은 Codex 단일 writer로 두고(OTel 설정과 충돌 방지), Claude는 적용 후 새 세션에서 노출 목록만 독립 확인한다.
