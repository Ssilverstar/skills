# 공통 스킬 프로필 검토 (Claude, 리뷰 전용)

작성: Claude Opus 5.5, 2026-10-31. **전역 설정·플러그인 캐시는 읽기만 했고 변경하지 않았다**(적용은 루트 Codex 단일 writer).
기준: 사용자 의도 = **4개 에이전트(Codex·Claude·OpenCode·Antigravity) 동일한 선택 목록**. 기준 목록 = `distribution/profiles/codex-general-sw.json` `enabled` 35개 + 저장소 `skills/herdr-orchestrate` = **36개**.
근거: 이 Claude 세션 시작 시 노출된 스킬 목록, `~/.claude/plugins/cache/ecc/ecc/2.2.3/`(plugin.json, hooks/hooks.json, hooks.metadata.json, .mcp.json) 읽기. 다른 에이전트의 실제 로더는 실측하지 않았다(Codex 감사 범위).

## 1. 36개를 "공통 ID + 에이전트별 실제 이름 + 전제조건"으로 관리

같은 선택 목록이라도 **노출 이름(접두)이 에이전트마다 다르다**. LIST에 `common_id` 열을 두고 에이전트별 실제 이름을 매핑해야 "동일 목록"을 기계적으로 검증할 수 있다.

| common_id | Claude에서 관찰된 이름 | 전제조건(없으면 동작 안 함) | 대체 경로·비고 |
|---|---|---|---|
| graft, archify, ponytail×6 (필수 8) | 동일 이름(`ponytail:*`) | graft: CLI 설치 + **저장소에 `graft/` 색인**(공통 실행 조건 이미 배포) | 필수 고정 |
| herdr | `herdr` | `HERDR_ENV=1`(Herdr 패널 안) | 패널 밖에서는 호출돼도 중단이 정상 |
| herdr-orchestrate | **이 세션에 미노출** | 위와 동일 + 저장소 스킬 배포 | 4개 에이전트 배포 필요(현재 Claude 누락) |
| ecc 13종(accessibility, api-design, architecture-decision-records, browser-qa, codebase-onboarding, coding-standards, database-migrations, deployment-patterns, docker-patterns, error-handling, git-workflow, github-ops, security-review) | `ecc:<name>` 노출됨 | browser-qa: **실제 브라우저 도구**(이 호스트에 Chrome 없음, Playwright chromium-1243 있음). github-ops: `gh` 인증 | browser-qa는 Playwright 경로를 대체로 명시 |
| docx, pdf | `anthropic-skills:docx`, `anthropic-skills:pdf` | Python 문서 라이브러리 | 접두 차이만 |
| humanize-korean | `humanize-korean:humanize-korean`(+ 전용 서브에이전트 다수) | 서브에이전트 지원(Claude) | 다른 에이전트는 단일 호출(monolith) 모드만 가능할 수 있음 — 확인 필요 |
| prefer-gh-for-github | 동일(hh-claude-kit 플러그인) | `gh` CLI | — |
| skill-creator | `skill-creator`(claude-plugins-official) | — | 에이전트별 스킬 형식 차이 주의 |
| superpowers 3종(systematic-debugging, test-driven-development, verification-before-completion) | **미노출** | 일반 SKILL.md | 사용자 스킬로 배포하면 공통화 가능(도구 전제 확인 후) |
| imagegen | 없음 | **이미지 생성 도구**(Codex 내장) | Claude·OpenCode·Antigravity 동등 도구 없음 → "전제 미충족·비활성" 표시. 래퍼로 흉내 내지 않음 |
| openai-docs | 없음 | OpenAI 문서 도구/MCP | 웹 조회 가능한 에이전트는 공식 문서 URL 조회로 대체 가능. `claude-api`는 다른 공급자 문서라 **대체물 아님** |
| review-agent | 없음 | Codex 리뷰 서브에이전트 | Claude: 내장 `code-review`/`ecc:code-review`(ECC 선택 13 밖) — 대체 경로로만 표기 |
| skill-installer | 없음 | Codex 스킬 설치 경로 | 다른 에이전트에서는 `distribution/` 적용 스크립트가 같은 역할. 그대로 복사하면 **Codex 경로에 쓰는 위험** |
| visualize:visualize | 없음 | Codex visualize 플러그인 | Claude: dataviz/Artifact. OpenCode·Antigravity: 확인 필요 |

권장: **목록은 36개로 동일하게 유지**하고, 플랫폼 종속 5개(imagegen, openai-docs, review-agent, skill-installer, visualize)는 각 에이전트에 `available | prerequisite-missing | native-alternative(<이름>)` 상태로 기록한다. "동일 목록"은 *같은 common_id 집합과 같은 상태 표기*로 정의하고, 존재하지 않는 도구를 래퍼로 가장하지 않는다.

## 2. Claude ECC filtered local plugin 검토

현 상태(관찰): ECC 2.2.3 = skills 293, commands(legacy shim) 94, agents 68, hooks 24, MCP `chrome-devtools` 1. 정책상 "ECC 전체 노출 예외" 때문에 이 세션에도 `ecc:*` 스킬·명령·에이전트가 대량 노출된다.

방향(선택 13 스킬만 노출 + 보안·수명주기 hooks 보존 + upstream/cache 비삭제)에 **동의**한다. 적용 시 확인할 점:

1. **원본 ECC 비활성화가 필수**: 원본과 filtered를 함께 켜면 24개 hook이 **두 번** 실행된다(GateGuard 차단·cost tracker·session 기록 중복). `enabledPlugins`에서 원본 off, filtered on.
2. **hook 실행 의존성**: 모든 hook이 `node -e`로 plugin root를 찾아 `scripts/hooks/*.js`를 require하고, 그 스크립트는 `scripts/lib/*` 등을 다시 require한다(예: `gateguard-fact-force.js` → `../lib/powershell-destructive-command`, `../lib/shell-substitution`). filtered 플러그인에 `hooks/`, `scripts/`(lib 포함), `package.json`과 필요한 의존성을 **통째로** 두어야 한다. 심볼릭 링크면 upstream 버전 갱신을 따라가고, 복사면 재동기화 스크립트가 필요.
3. **manifest 경로**: `plugin.json`이 `skills: ["./skills/"]`, `commands: ["./commands/"]`를 선언한다. filtered는 `skills/`에 선택 13개만 두고, **commands 94개(legacy shim)도 노출 목록에 포함되므로** 비우거나 선택분만 둔다. agents 68개는 스킬과 별개 노출이므로 유지/선별을 명시적으로 결정해야 "동일 목록" 의도와 충돌하지 않는다(권장: 스킬 정합 범위 밖으로 문서화하고 일단 유지하거나, 사용 중인 것만).
4. **hook과 스킬의 결합 확인**: `post:skill:track`(Skill 실패 텔레메트리), `pre:observe:continuous-learning`(도구 사용 관찰 기록), `stop:evaluate-session`은 비선택 스킬·명령 존재를 전제로 하지 않는지 실행 로그로 확인. 특히 continuous-learning 관찰 기록은 **도구 입력을 로컬에 저장할 수 있으므로** 보존 여부를 프라이버시 기준(관측 서버의 원문 비저장 원칙)과 함께 결정.
5. **userConfig 보존**: `hooks_enabled`, `hook_profile` 값을 filtered 플러그인 설정으로 그대로 옮긴다.
6. **MCP**: `.mcp.json`의 `chrome-devtools`는 이 호스트에 Chrome 실행 파일이 없어(Codex 확인) 동작하지 않는다. `pre:mcp-health-check`가 unhealthy로 막을 수 있으니 유지 시 의도를 명시하거나 filtered에서 제외.
7. **업데이트 경로**: marketplace 업데이트가 원본을 다시 활성화하거나 새 버전 캐시를 만들 수 있다. 버전 고정(2.2.3)과 "새 버전 → filtered 재생성 → 검증" 절차를 LIST 옆에 기록. 비선택 upstream/cache는 삭제하지 않는다.
8. **Claude Code 내장 스킬**(`code-review`, `security-review`, `simplify`, `init`, `loop` 등)과 다른 플러그인(anthropic-skills, web-slides 등)은 ECC filter로 줄지 않는다. "동일 목록" 비교에서 **플랫폼 내장/기타 플러그인** 범주로 분리 표기.

## 3. 적용 후 검증 체크리스트(새 Claude 세션)

- 노출 스킬 중 common_id 매핑 36개 상태가 LIST와 일치(누락: herdr-orchestrate, superpowers 3 해소 여부).
- `ecc:*` 노출이 선택 13개(+유지 결정한 commands/agents)뿐.
- hook 1회 실행: 예) 첫 Write 시 GateGuard 안내가 **한 번만** 출력, Stop 시 cost tracker 기록 1건.
- 필수 8개 호출 가능(`ponytail-help` 로드 등), graft 실행 조건 지침 유지.
- 원본 ECC 캐시·다른 플러그인 파일 변경 없음(`ls -la` mtime 비교).
