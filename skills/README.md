# 스킬 등록부

[합의된 전체 사용 목록](../distribution/skill-list.md)과 [공통 정책](../distribution/skill-policy.md)을 기준으로 관리합니다. 직접 작성한 스킬은 `skills/<name>/SKILL.md`에 두고, 아래 외부 스킬은 원본을 복제·수정하지 않고 출처와 설치 상태를 기록합니다.

## 사용자 필수 8개

| 이름 | 용도 | 원본 / 확인 버전 | Codex · Claude · Gemini · OpenCode |
| --- | --- | --- | --- |
| `graft` | 코드 그래프 검색·호출 관계·영향 범위 | `@nanonets/graft` 0.21.1의 `dist/claude/skill-template.js` | 네 로더 모두 발견 확인 |
| `archify` | 아키텍처·워크플로·시퀀스·데이터 흐름 다이어그램 | [tt-a1i/archify](https://github.com/tt-a1i/archify), 패키지 3.0.1 | 네 로더 모두 발견 확인 |
| `ponytail` | 과잉 설계 방지, YAGNI | 기존 Ponytail 플러그인 | 네 로더 모두 발견 확인 |
| `ponytail-audit` | 저장소 전체 과잉 설계 점검 | 동일 | 동일 |
| `ponytail-debt` | 의도적 타협·부채 추적 | 동일 | 동일 |
| `ponytail-gain` | 벤치마크 효과 안내 | 동일 | 동일 |
| `ponytail-help` | 사용법 안내 | 동일 | 동일 |
| `ponytail-review` | 변경 사항 과잉 설계 리뷰 | 동일 | 동일 |

Ponytail은 Claude 플러그인 4.10.3과 Codex import 1.0.0의 여섯 `SKILL.md`가 바이트 단위로 동일합니다. import 버전과 upstream 버전을 동일 버전 번호로 취급하지 않습니다. 플러그인 설정의 `ponytail@ponytail` / `ponytail@claude-import`를 유지합니다.

`graft` 설치 패키지의 repository 필드는 [NanoNets/context-graph-engine](https://github.com/NanoNets/context-graph-engine)이며 확인 시 [trailhq/Trail-Code](https://github.com/trailhq/Trail-Code)로 리다이렉트됐습니다. 이번 작업에서 Trail로 업그레이드하지 않고 이미 설치된 0.21.1 템플릿을 그대로 사용했습니다. 동명의 다른 Graft 제품과 구분합니다.

## 설치 위치

| 에이전트 | graft | archify | Ponytail 6개 |
| --- | --- | --- | --- |
| Codex | `~/.codex/skills/graft` | 기존 `~/.codex/skills/archify` | 기존 import 플러그인 |
| Claude | `~/.claude/skills/graft` | 기존 `~/.claude/skills/archify` | 기존 Claude 플러그인 |
| Gemini | `~/.gemini/skills/graft` | 같은 루트의 `archify` 링크 | 같은 루트의 각 이름 링크 |
| OpenCode | `~/.config/opencode/skills/graft` | 같은 루트의 `archify` 링크 | 같은 루트의 각 이름 링크 |

`graft` 링크 대상은 `~/.local/share/agent-skills/graft-0.21.1`입니다. archify는 보조 파일을 포함한 기존 Codex 패키지 전체를, Ponytail은 기존 Claude 플러그인의 각 디렉터리를 참조합니다. [설치·복구·링크 갱신 절차](../distribution/README.md#필수-스킬-보완-설치)를 따릅니다.

발견 확인은 워크플로 전체 실행 검증을 뜻하지 않습니다. graft 색인 전제는 [공통 지침](../instructions/common.md#전역-스킬-실행-조건), 플랫폼별 차이는 [정책](../distribution/skill-policy.md)에 기록합니다.

## 직접 작성할 때

| 저장소 스킬 | 용도 | 상태 |
| --- | --- | --- |
| [herdr-orchestrate](herdr-orchestrate/SKILL.md) | 지정된 총괄을 통한 계약 기반 위임, 3열 작업자 그룹, 실제 결과 검증·정리 | 저장소 원본 작성·형식 검사 완료. 공급업체 Herdr 스킬을 덮어쓰지 않는 보완 스킬 |

실제 운영 근거와 개선점은 [시험 기록](../test/monitor-study.md), 적용 절차는 [Herdr 워크플로](../herdr/workflows/claude-workers.md)에 남깁니다. 새 원본 추가가 기존 전역 활성화 프로필의 자동 변경을 뜻하지는 않습니다.

`name`, `description`을 포함하고 목적·적용 조건·실행 절차·검증 방법을 작성합니다. 보조 파일은 같은 디렉터리의 `references/`, `scripts/`, `assets/`에 둡니다. [템플릿](../templates/skill/SKILL.md.template)과 [작성 가이드](../docs/authoring.md)를 참고합니다.
