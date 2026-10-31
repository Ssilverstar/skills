# Agent Instructions & Skills

Codex, Claude, Gemini, OpenCode에 배포할 지침과 재사용 가능한 스킬을 관리하는 저장소입니다. herdr 사용 지침도 함께 관리합니다.

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
│   ├── profiles/                       # Codex 목록, OpenCode 권한 규칙
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

Codex와 **Opus 5.5 high**가 범용 SW 개발 기준에 합의했습니다. 필수 목록은 네 에이전트 공통이며, 다른 스킬은 실제 도구와 플러그인 제약에 맞춰 적용합니다.

- **필수 8개:** `graft`, `archify`, `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`.
- **Codex:** 설치 364개 중 활성 35개·비활성 329개. 파일은 보존하고 목록 노출만 정리했습니다.
- **Claude:** 필수 8개 발견 확인. ECC는 훅 보존을 위해 전체 노출 예외로 유지합니다.
- **Gemini:** 필수 8개와 기존 3개, 총 11개 발견 확인.
- **OpenCode:** 등록 39개, `build` 권한상 27개 허용. 이번 프로필에서 11개를 차단하며 내장 `browser` 차단은 기존 규칙입니다.

목록은 필수·기본 유지·프로젝트별 사용·호환성 제외·중복/강제 트리거 제외·검토 보류로 관리합니다. **검토 보류는 불필요 판정이 아닙니다.** 언어·프레임워크 스킬은 프로젝트별로 선택하며 Python도 동일합니다. [스킬 등록부](skills/README.md)에 출처·버전·설치 위치를 남겼습니다.

**남아 있던 Codex 경고는 skill budget 초과입니다.** 기존 세션은 이전 372개 카탈로그를 유지하며 60개를 누락한 로그가 확인됐습니다. 변경 후 새 CLI에서는 재현되지 않았지만, 기존 App 화면의 경고 소멸은 확인하지 않았습니다. 새 세션에서도 로컬 목록과 App 원격 카탈로그를 구분해 점검해야 합니다.

새 내용을 추가할 때는 [작성 가이드](docs/authoring.md)를 따릅니다. 범용 동기화 도구는 구현하지 않았고, 확인된 로컬 프로필과 절차만 관리합니다.

## 에이전트별 스킬 수 제한과 운영 가이드

2026-10-31 확인. 대상은 **Codex CLI/App의 로컬 스킬, Claude Code, Gemini CLI, OpenCode**입니다. 웹 챗 서비스와 API의 제한을 CLI 제한으로 섞지 않습니다. 아래에서 “개수 상한 미명시”는 무제한 보장이 아니라, 확인한 공식 자료에 고정된 최대 개수가 없다는 뜻입니다. 설치된 수와 모델에 실제로 노출되는 수는 다를 수 있습니다.

| 에이전트 | 최대 스킬 수 / 실제 제한 | 공식 권장 개수 | 이 저장소의 SW 엔지니어용 권장 |
| --- | --- | --- | --- |
| Codex 0.166.0 | 고정 개수 상한 미명시. 목록 메타데이터 기본 예산은 모델 컨텍스트의 **2%**. 컨텍스트 크기 미확인 시 **8,000자**, 명시적 토큰 예산 설정은 최대 **10,000토큰**. 초과하면 설명 제거·항목 누락 가능. [버전별 소스](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/ext/skills/src/render.rs) | 고정 개수 미명시 | 필수 기능을 보존하고 새 세션 렌더 로그의 목록 누락·설명 손실로 검증 |
| Claude Code 2.1.314 | 고정 개수 상한 미명시. 현재 공식 문서의 목록 예산은 컨텍스트의 **1%**이며, 초과하면 사용 빈도가 낮은 스킬의 설명부터 제외. `skillListingBudgetFraction` 또는 `SLASH_COMMAND_TOOL_CHAR_BUDGET`으로 조정. [공식 문서](https://code.claude.com/docs/en/skills#skill-descriptions-are-cut-short) | 고정 개수 미명시 | 필수 기능을 보존하고 `/doctor`, `/context`, `/skill-doctor`로 목록 비용·사용 여부 점검 |
| Gemini CLI 0.66.0 | 공식 문서에 고정 개수 상한 미명시. 이름·설명을 먼저 로딩하고 본문은 필요할 때 활성화. [공식 문서](https://geminicli.com/docs/cli/skills/) | 고정 개수 미명시 | 실제 작업에 필요한 항목을 유지하고 `/skills list`로 확인 |
| OpenCode 2.2.5 | V2 공식 문서에 고정 개수 상한 미명시. 허용된 스킬의 ID·이름·설명을 모델에 제공하며 본문은 호출 시 로딩. [V2 공식 문서](https://dev.opencode.ai/v2/docs/skills/) | 고정 개수 미명시 | 실제 작업에 필요한 항목을 유지하고 자동 노출 설정·권한·중복 ID 확인 |

고정 개수 목표를 두지 않습니다. 사용자 필수 기능, 설명 길이, 도구 호환성, 실제 목록 누락을 함께 확인합니다. 초기 20~30개 목표와 Ponytail 제외 판단을 철회한 근거는 [Opus 비교 검토](docs/opus-skill-review-2026-10-31.md)에, 최종 합의는 [공통 정책](distribution/skill-policy.md)에 기록했습니다.

## 로컬 참고 자료

`user-guide/`는 개인 작업용 참고 자료를 보관하는 디렉터리입니다. Git 추적과 배포 대상에서 제외하며, 저장소를 복제할 때 포함되지 않습니다. 공유할 지침은 `instructions/`, 스킬은 `skills/`, herdr 가이드는 `herdr/`에 작성합니다.
