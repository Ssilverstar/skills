# 스킬셋 최종 합의와 적용 기록

## 합의

범용 SW 엔지니어 기준으로 Codex와 오른쪽 Herdr 패널의 **Claude Opus 5.5 / high**가 정책과 저장소 구성을 검토했습니다. 이전 29개 화이트리스트를 정답으로 승인한 것이 아니라, 아래처럼 바로잡은 운영안에 합의했습니다.

- 필수: Ponytail 6개, archify, graft. 없으면 네 에이전트에 보완 설치.
- 고정된 20~30개 목표 폐기. 메타데이터 예산·필수 기능·호환성 중심으로 판단.
- Python 전역 복구 제안은 Opus가 철회. 언어 스택은 프로젝트별로 선택.
- `ecc:skill-stocktake`는 Claude 하네스 전제로 Codex 기본 목록에서 제외.
- 검토하지 않은 항목은 `needs-review`. 보류와 불필요 판정을 구분.
- Claude ECC 전체 노출은 훅 보존을 위한 명시적 예외.
- README의 에이전트별 최대/권장 개수 표는 사용자 요청대로 유지. 상세 정책은 한 문서, 사용 목록은 JSON과 생성 Markdown으로 관리.
- 외부 스킬 원본·공급업체 캐시를 수정하지 않고 출처·버전·설치 위치만 저장소에 등록.

원본 목록은 [Codex JSON](../distribution/profiles/codex-general-sw.json), 읽기용 [전체 LIST](../distribution/skill-list.md), [공통 정책](../distribution/skill-policy.md), [OpenCode 규칙](../distribution/profiles/opencode-general-sw.json)입니다. 이전 기록 세 개는 당시 이력으로 남깁니다.

## 실제 변경

1. 초기 363개에서 graft 1개를 추가해 Codex 로컬 설치 목록은 364개입니다. 기존 35개 유지 상태에서 graft를 추가하고 skill-stocktake를 제외해 **35 활성 / 329 비활성**이 됐습니다.
2. Codex/Claude에 이미 있던 archify 3.0.1을 보존하고 Gemini/OpenCode에 전체 패키지 링크를 추가했습니다.
3. graft 0.21.1 upstream 템플릿 출력 그대로 네 스킬 루트에 연결했습니다. SHA-256은 `bc338fab9fd85c2531f8e06a7f72d835b67428f29b4a5afe8b26f2814e877cf4`입니다.
4. Gemini/OpenCode에 Ponytail 6개 링크를 추가했습니다. 기존 Codex/Claude 플러그인은 유지했습니다.
5. graft 색인이 없는 저장소에서 원본 설명을 사실로 받아들이지 않도록 `instructions/common.md`의 실행 조건을 네 전역 사용자 지침에 배포했습니다. 네 대상 파일은 기존에 없었습니다.
6. OpenCode는 같은 기준으로 Superpowers 11개를 `skill` 권한에서 차단했습니다. 파일은 유지합니다. 나머지 앱 동기화 파일과 공급업체 설정은 보존했습니다.

파일 삭제는 하지 않았습니다. Codex 변경 전 설정 백업과 링크/파일 생성 기록은 사용자 홈에 보관하며 커밋하지 않습니다. 이전 정리 이후 추가로 비활성화한 Codex 스킬은 **ecc:skill-stocktake 1개**입니다.

## 확인 결과와 한계

| 확인 | 결과 | 한계 |
| --- | --- | --- |
| Codex app-server `skills/list`, forceReload | 설치 364 / 활성 35 / 파싱 오류 0 / stderr 비어 있음 | 목록 로더 검증이며 App 화면의 budget 경고 검증과 다름 |
| 새 Codex CLI 읽기 전용 실행 | 도구 호출 없이 `OK` 완료, stderr에 budget 경고 없음 | ephemeral 실행이므로 영속 로그에 이 실행의 렌더 수치 없음. 기존 App 세션 경고 소멸을 증명하지 않음 |
| Claude Code 새 프로세스 SDK initialize (Opus 수행) | 명령 목록 461개 중 필수 8개 모두 발견 | **461은 스킬 수가 아닌 명령+스킬 목록 수**. 모델 호출 없이 확인했으나 SessionStart 훅 실행. 설명 예산 내 전체 노출 여부는 미검증 |
| Gemini `skills list --all` | 필수 8개 + herdr + 내장 2개 = 11, 모두 Enabled | 프로젝트 신뢰 관련 메시지는 기존 상태. 신뢰 설정을 변경하지 않음 |
| OpenCode 서비스 `/api/skill` | 등록 39개, 필수 8개 모두 존재 | 초기화 직후 빈 목록에 주의. 조회 위치는 서비스 기본 사용자 홈 범위 |
| OpenCode `/api/config`, `debug agents` | 11개 규칙 반영, build 권한 평가상 27개 허용 | 기존 내장 browser deny 1개가 별도로 있음. 등록 수와 모델 허용 수를 구분 |
| 패키지 보존 | archify 기존 두 SKILL 파일 동일, Ponytail 6개 원본 동일 | 모든 기능의 실제 실행을 시험한 것은 아님 |

남아 있던 경고의 정체는 **skill budget 초과**입니다. 기존 App 세션 로그는 `budget_limit=5440`, `total_skills=372`, `included_skills=312`, `omitted_skills=60`, `truncated_description_chars_per_skill=290`을 기록했습니다. 설정 변경 후 기존 세션의 중간 압축에서도 이전 372개 목록이 재사용됐습니다. 따라서 새 CLI 결과만으로 기존 탭의 경고가 사라졌다고 보고하지 않습니다. 새 App 세션에서 현재 로컬 목록과 원격 카탈로그를 함께 확인해야 합니다.

Opus가 직접 본문을 확인한 비활성 스킬은 일부(초기 검토 약 20개)입니다. 329개 전체의 불필요성이 검증됐다는 주장은 하지 않습니다. 전체 명단은 향후 재검토할 수 있게 보존합니다.

## 커밋 전 최종 검토

Opus 5.5 high가 정책·목록·README·적용 결과에 동의했으며, 직접 테스트 3개 통과, LIST 일치, Codex `changed=false`, 필수 항목 보존, OpenCode 11개 대응, graft 원본 해시, 상대 링크·앵커를 확인했습니다. README 구조 트리와 아래 후속안 기록을 보완하는 조건을 반영했습니다. Gemini/OpenCode 수치와 Codex 새 CLI 결과는 Codex가 확인한 증거를 검토했고 Opus가 별도로 재실행한 것은 아닙니다.

## 미적용 후속안 — graft MCP와 기존 statusline 병행

오른쪽 Opus 패널에서 논의한 후속 방향은 graft MCP를 활용하고, **기존 statusline과 graft 표시를 함께 사용하는 방식**입니다. 이번 커밋은 스킬 사용 목록·설치·정책을 다루며 MCP/훅/statusline 설정은 변경하지 않았습니다.

검토한 방식은 전역 statusline 래퍼가 stdin JSON을 한 번 받아 기존 명령에 전달하고, 작업 저장소에 `.claude/helpers/graft-statusline.cjs`가 있을 때만 graft 출력도 합치는 것입니다. graft 스크립트가 없는 저장소에서는 기존 표시를 유지합니다. 각 저장소에서 별도로 색인 설치를 요청할 때는 `graft init --no-statusline`으로 프로젝트 설정이 기존 statusline을 가리지 않도록 하는 안입니다. 실제 적용 전 기존 명령 경로, 래퍼 보관 위치, 패키지의 텔레메트리 설정, ECC 훅과의 동시 동작을 확인합니다. 이 단락은 실행·호환성 검증 완료를 뜻하지 않습니다.
