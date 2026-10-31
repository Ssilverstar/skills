# Agent Instructions & Skills

Codex, Claude, Gemini, OpenCode에 배포할 지침과 재사용 가능한 스킬을 관리하는 저장소입니다. herdr 사용 지침도 함께 관리합니다.

## 로컬 운영 시험

[**최종 보고: 변경 전후·커스텀 Herdr 스킬·시험 결과**](test/final-report.md)

[Agent Observatory](test/monitor/README.md)는 에이전트 사용량·GPU/추론 서버·스킬 상태를 보여 주는 컨테이너 웹앱입니다. [작업 계약](test/monitor-brief.md)과 [운영 방식 비교 기록](test/monitor-study.md)은 `test/`에서 관리합니다. 집 환경의 Google 작업자는 Antigravity/Gemini 3.8이며, OpenCode는 로컬 Qwen3.8을 사용합니다. 기존 Gemini CLI 점검 수치는 전환 이전 이력입니다. 최신 상태는 [시험 기록](test/agent-status.md)을 기준으로 봅니다.

새 [herdr-orchestrate 스킬](skills/herdr-orchestrate/SKILL.md)은 사용자가 지정한 총괄 역할을 유지하고 계약 기반 위임·결과 검증·패널 정리를 안내합니다. `Codex | Claude | Agents`에서는 Claude가 오른쪽 Gemini·OpenCode 작업자를 직접 조정하며, Codex는 별도 소유 작업과 독립 검증을 수행합니다. [실제 운영 절차](herdr/workflows/claude-workers.md)를 참고하세요.

## 저장소 구조

```text
.
├── AGENTS.md / CLAUDE.md / GEMINI.md     # 에이전트별 진입점
├── instructions/
│   ├── common.md                       # 공통 규칙·전역 실행 조건
│   └── agents/                         # codex, opus, gemini, opencode
├── skills/README.md                    # 외부 필수 스킬 출처·버전·설치 위치
├── herdr/                             # 사용 지침과 workflows/
├── templates/skill/                    # 직접 작성하는 스킬 템플릿
├── distribution/
│   ├── README.md                       # 적용·검증·복구 절차
│   ├── skill-policy.md                 # 공통 기준·도구별 예외
│   ├── skill-list.md                   # 전체 이름·분류 LIST (생성물)
│   ├── profiles/                       # 공통 36개 스킬·3개 MCP, 이전 프로필
│   ├── common_profile.py / mcp_profile.py # 공통 목록·MCP 로컬 배포
│   ├── codex_profile.py                # 미리보기·적용·복구
│   └── render_skill_list.py            # LIST 생성·일치 검사
├── tests/test_profiles.py              # 설정 보존·복구·목록 일치 검증
└── docs/
    ├── authoring.md                    # 작성 절차
    ├── skill-audit-2026-10-31.md        # 최초 점검 이력
    ├── skill-changes-2026-10-31.md      # 최초 제외 명단과 복구 이력
    ├── opus-skill-review-2026-10-31.md  # 초기 판단에 대한 비교 검토
    └── skill-set-agreement-2026-10-31.md # 최종 합의·검증·후속안
```

## 읽는 순서

사용하는 대상에 맞는 진입점에서 시작합니다.

| 대상 | 진입점 | 대상별 지침 |
| --- | --- | --- |
| Codex | [AGENTS.md](AGENTS.md) | [codex.md](instructions/agents/codex.md) |
| Opus / Claude 환경 | [CLAUDE.md](CLAUDE.md) | [opus.md](instructions/agents/opus.md) |
| Gemini | [GEMINI.md](GEMINI.md) | [gemini.md](instructions/agents/gemini.md) |
| OpenCode | [AGENTS.md](AGENTS.md) | [opencode.md](instructions/agents/opencode.md) |

1. [공통 지침](instructions/common.md)을 읽습니다.
2. [대상별 지침](instructions/agents/)에서 현재 사용하는 대상의 파일을 읽습니다.
3. herdr를 사용하는 작업에서는 [herdr 가이드](herdr/README.md)를 읽습니다.
4. 작업에 필요한 [스킬](skills/README.md)을 선택해 해당 `SKILL.md`를 읽습니다.

이 저장소에서 Opus는 Claude 환경에서 사용하는 모델 대상으로 구분합니다. 다른 실행 환경을 사용한다면 해당 환경에 맞춰 진입점과 배포 규칙을 조정합니다.

## 합의된 스킬 사용 목록

[**전체 스킬 LIST**](distribution/skill-list.md) · [공통 선정 기준](distribution/skill-policy.md) · [적용·복구](distribution/README.md) · [최종 검증 기록](docs/skill-set-agreement-2026-10-31.md)

Codex와 **Opus 5.5 high**의 재검토를 거쳐 네 에이전트의 공통 선택을 **36개 스킬 + 3개 MCP**로 맞춥니다. 기존 Claude ECC 전체 노출 예외는 폐기했습니다. [공통 프로필](distribution/profiles/common-general-sw.json)에 실제 이름·원본 해시·실행 전제를, [MCP 프로필](distribution/profiles/common-mcp.json)에 동일 서버 구성을 기록합니다.

- **필수 8개 유지:** graft, archify, Ponytail 6개.
- **공통 스킬 36개:** 기존 범용 SW 개발 35개 + 커스텀 `herdr-orchestrate`. Claude ECC는 13개만 노출하고 기존 훅·보조 파일은 보존합니다.
- **공통 MCP 3개:** Git, 공식 GitHub, Chrome DevTools. 실제 연결·읽기 호출 결과는 시험 기록으로 확인합니다.
- **비교 방식:** 공통 선택/발견/활성과 제품 내장·앱 기능을 분리합니다. 이미지 생성·인라인 시각화 등의 도구 전제가 충족되지 않으면 실행 가능하다고 표시하지 않습니다.

목록은 필수·기본 유지·프로젝트별 사용·호환성 제외·중복/강제 트리거 제외·검토 보류로 관리합니다. **검토 보류는 불필요 판정이 아닙니다.** 언어·프레임워크 스킬은 프로젝트별로 선택하며 Python도 동일합니다. [스킬 등록부](skills/README.md)에 출처·버전·설치 위치를 남겼습니다.

**정리 당시 남아 있던 Codex 경고는 skill budget 초과였습니다.** 기존 세션은 이전 372개 카탈로그를 유지하며 60개를 누락한 로그가 확인됐습니다. 이후 사용자가 경고 해소를 확인했습니다. 앱/템플릿 추가로 최신 수는 최초 합의 프로필과 다를 수 있으므로 [최신 로더 점검](test/agent-status.md)과 구분합니다. 새 세션에서도 로컬 목록과 App 원격 카탈로그를 나누어 점검합니다.

새 내용을 추가할 때는 [작성 가이드](docs/authoring.md)를 따릅니다. 감사한 머신용 공통 배포기를 제공하며, 다른 머신은 소스 버전·경로·기존 설정부터 검토합니다.

## 에이전트별 스킬 수 제한과 운영 가이드

2026-10-31 확인. 대상은 **Codex CLI/App의 로컬 스킬, Claude Code, Gemini CLI, OpenCode**입니다. 웹 챗 서비스와 API의 제한을 CLI 제한으로 섞지 않습니다. 아래에서 “개수 상한 미명시”는 무제한 보장이 아니라, 확인한 공식 자료에 고정된 최대 개수가 없다는 뜻입니다. 설치된 수와 모델에 실제로 노출되는 수는 다를 수 있습니다.

| 에이전트 | 최대 스킬 수 / 실제 제한 | 공식 권장 개수 | 이 저장소의 SW 엔지니어용 권장 |
| --- | --- | --- | --- |
| Codex 0.166.0 | 고정 개수 상한 미명시. 목록 메타데이터 기본 예산은 모델 컨텍스트의 **2%**. 컨텍스트 크기 미확인 시 **8,000자**, 명시적 토큰 예산 설정은 최대 **10,000토큰**. 초과하면 설명 제거·항목 누락 가능. [버전별 소스](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/ext/skills/src/render.rs) | 고정 개수 미명시 | 필수 기능을 보존하고 새 세션 렌더 로그의 목록 누락·설명 손실로 검증 |
| Claude Code 2.1.314 | 고정 개수 상한 미명시. 현재 공식 문서의 목록 예산은 컨텍스트의 **1%**이며, 초과하면 사용 빈도가 낮은 스킬의 설명부터 제외. `skillListingBudgetFraction` 또는 `SLASH_COMMAND_TOOL_CHAR_BUDGET`으로 조정. [공식 문서](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short) | 고정 개수 미명시 | 필수 기능을 보존하고 `/doctor`, `/context`, `/skill-doctor`로 목록 비용·사용 여부 점검 |
| Gemini CLI 0.66.0 | 공식 문서에 고정 개수 상한 미명시. 이름·설명을 먼저 로딩하고 본문은 필요할 때 활성화. [공식 문서](https://geminicli.com/docs/cli/skills/) | 고정 개수 미명시 | 실제 작업에 필요한 항목을 유지하고 `/skills list`로 확인 |
| Antigravity CLI 1.4.12 | 공식 문서에 고정 개수 상한 미명시. 스킬 발견과 실제 실행 도구의 지원은 구분. [공식 문서](https://antigravity.google/docs/skills) | 고정 개수 미명시 | 공통 선택 36개와 실제 세션 목록 비교 |
| OpenCode 2.2.5 | V2 공식 문서에 고정 개수 상한 미명시. 허용된 스킬의 ID·이름·설명을 모델에 제공하며 본문은 호출 시 로딩. [V2 공식 문서](https://dev.opencode.ai/v2/docs/skills/) | 고정 개수 미명시 | 실제 작업에 필요한 항목을 유지하고 자동 노출 설정·권한·중복 ID 확인 |

고정 개수 목표를 두지 않습니다. 사용자 필수 기능, 설명 길이, 도구 호환성, 실제 목록 누락을 함께 확인합니다. 초기 20~30개 목표와 Ponytail 제외 판단을 철회한 근거는 [Opus 비교 검토](docs/opus-skill-review-2026-10-31.md)에, 최종 합의는 [공통 정책](distribution/skill-policy.md)에 기록했습니다.

## 로컬 참고 자료

`user-guide/`는 개인 작업용 참고 자료를 보관하는 디렉터리입니다. Git 추적과 배포 대상에서 제외하며, 저장소를 복제할 때 포함되지 않습니다. 공유할 지침은 `instructions/`, 스킬은 `skills/`, herdr 가이드는 `herdr/`에 작성합니다.
