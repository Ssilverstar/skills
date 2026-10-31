# 전체 에이전트 상태

> 후속 갱신(2026-10-31): 아래 표와 사용률은 **본 시험 전 점검 기록**입니다. 이후 네 호스트에 공통 선택 스킬 36개와 MCP 3개를 적용했고, 12개 MCP 연결·읽기 호출을 확인했습니다. Codex 65개 활성·Claude 전체 ECC·OpenCode/Antigravity MCP 미설정은 현재 상태가 아닙니다. [최종 보고](final-report.md), [공통 런타임 검사](results/common-runtime-claude.json), [MCP 검사](results/common-mcp.json), [배포 점검](results/monitor-deployment.json)을 최신 근거로 봅니다. 아래 패널 정리와 미확인 항목 역시 당시 기록입니다.

2026-10-31 점검. 기본 동작은 모델 응답, 공개 파일 읽기, 대표 스킬 로드 또는 MCP 읽기 호출로 검증했습니다. 모든 스킬 워크플로·모든 MCP 업무 기능을 시험한 것은 아닙니다.

| 에이전트 | 모델 / 플랜 | 기본 동작 | 스킬 | MCP |
| --- | --- | --- | --- | --- |
| Codex 0.166.0 | GPT-6 Astra high / ChatGPT 로그인, API 플랜 ID `prolite` | PASS: 현재 세션 응답·파일·산술·git MCP 성공 | 394개 발견, 65개 활성, 오류 0. 필수 8개 존재. ponytail-help 파일 직접 읽기 성공 | 8개 서버의 목록 조회에 discovery 오류 없음. 실제 git_status 호출 성공. runtimeStatus 미제공인 서버 전체의 실시간 건강 상태까지 보증하지 않음 |
| Claude Code 2.1.314 | Opus 5.5 high / Claude Pro | PASS: Read·대표 스킬·git MCP 성공. Bash 시도 1회 기존 훅 차단 | 필수 8개 발견, `ponytail:ponytail-help` 실제 Skill 도구 로드 성공 | git 실제 호출 성공. 나머지 연결 목록은 [상세 기록](claude-preflight.md) 참조. Gmail/Drive/Calendar는 추가 업무 인증 필요 |
| OpenCode 2.2.5 | `llm-server/Qwen3.8-Flash-Next-IQ3_S` / 로컬 추론 | PASS: Read·산술·응답, `skill(ponytail-help)` 성공 | 필수 8개 카탈로그 확인 및 원본 읽기 가능. 대표 1개 호출 성공 | 미설정. MCP가 없다는 사실은 연결 장애가 아님 |
| Antigravity CLI 1.4.12 | Gemini 3.8 Flash (Medium) / Google AI Pro | PASS: 대화형 세션에서 파일·산술·응답 성공 | 필수 8개 인식, Herdr 포함 9개 연결. `ponytail-help` 원문을 ReadFile로 읽음. 별도 Skill 도구 호출은 아님 | `agy mcp list`: 미설정 |

## 사용량과 주의점

- Codex: 계정 조회와 한도 조회 모두 `prolite`; 주간 창 사용률 7% 관측. 소매 상품명·가격으로 임의 환산하지 않습니다. 처음의 계정 조회 timeout은 점검 스크립트의 버퍼 처리 문제였고 수정 후 정상입니다.
- Claude: `/usage` 화면에서 세션 18%, 주간 3% 사용을 확인했습니다. ECC 설명은 92개 약 5,044 tok/turn, 전체 목록 약 2,000 tok/turn cap으로 표시됩니다. 설명 일부 제한을 전체 스킬 로드 실패와 혼동하지 않습니다.
- Claude의 Bash 첫 호출은 기존 Fact-Forcing Gate 훅에 차단됐으며 Read 도구로 완료했습니다. 훅을 해제하거나 우회하지 않았습니다. 셸 위주 무인 실행 시험에서는 별도 확인할 항목입니다.
- Qwen: 1차 smoke 35.4초/18.5 tok/s, 대표 스킬 포함 2차 smoke 12.6초/18.1 tok/s가 UI에 표시됐습니다. 두 관측은 통제된 성능 벤치마크가 아닙니다. 로컬 GPU 비용과 대기 시간은 존재합니다.
- Antigravity: 재확인 시 초기 설정이 완료되어 있었고 Google AI Pro가 표시됐습니다. `/model`에서 Gemini 3.8 Flash (Medium)을 선택해 실제 응답까지 확인했습니다. 데이터 수집 옵션의 최종 선택값은 확인하지 않았습니다. 구독 잔여 한도는 미확인입니다.
- Antigravity 비대화형 실행은 `read_file` 승인 불가로 자동 거절됐습니다. 종료 코드 0과 JSON `SUCCESS`가 있었지만 응답은 비어 있어 성공으로 세지 않았습니다. 대화형 재시험에서는 요청 범위인 `ponytail-help/SKILL.md` 파일 하나에 대한 읽기만 허용했고, 광범위한 상시 권한은 부여하지 않았습니다. [상세 결과](results/antigravity.json).
- 네 호스트의 필수 8개 `SKILL.md`가 모두 읽히고 각각의 해시가 서로 같습니다. [파일 검사 결과](results/skill-files.json). 파일 일치는 실제 워크플로 완주를 뜻하지 않습니다.
- 이전 합의의 Codex 35개 프로필 외에 앱/템플릿 스킬 30개가 추가 노출되어 현재 65개입니다. 새 항목을 자동 차단하지 않는 기존 정책에 따라 임의 변경하지 않았습니다. 사용자는 Codex 경고 해소를 확인했습니다.

## 패널 정리

2026-10-31 12:10 KST 무렵, 사용자 요청에 따라 점검 완료 후 Claude (`w3:p5`), OpenCode (`w3:p7`), Antigravity (`w3:p8`) 패널을 닫았습니다. 이전 Gemini 패널은 전환 작업에서 이미 제거했습니다.

`herdr pane list --workspace w3`와 `herdr pane layout --pane w3:p1`로 **Codex · GPT-6 Astra (`w3:p1`) 하나만 남고 분할이 없음**을 확인했습니다. 패널 종료이며 에이전트 설치·스킬·설정 삭제는 아닙니다. 다른 작업 공간은 변경하지 않았습니다.

## 시험 시작 판정

네 에이전트 모두 기본 응답과 파일 읽기를 확인했습니다. Antigravity도 요청한 Gemini 3.8 Flash로 검증을 마쳤습니다. 본 시험 전에는 Google 잔여 한도, 비대화형 읽기 권한, Claude 셸 훅과 신규 세션 조건을 맞춰야 합니다. 모든 스킬 워크플로와 모든 MCP 기능의 검증 완료를 뜻하지 않습니다. 시험 산출물은 모두 `test/`에만 관리하며 아직 커밋·푸시하지 않았습니다.
