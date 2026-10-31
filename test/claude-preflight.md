# Claude 사전 점검 (2026-10-31)

대상: 기존 Claude Code 2.1.314 세션(Herdr 패널). 읽기 전용 점검이며 설정·로그인·구독을 변경하지 않았습니다. 계정 식별자와 비밀 값은 기록하지 않습니다.

**종합: 기본 동작 PASS, 훅·스킬 목록 예산 주의사항 있음.**

| 항목 | 결과 | 근거 |
| --- | --- | --- |
| 인증 | PASS | `claude auth status`: 로그인됨, `authMethod=claude.ai`, `apiProvider=firstParty`. API 키·Bedrock·Vertex 환경변수 없음 |
| 구독 | PASS | `subscriptionType=pro`, SDK `initialize` 응답 `Claude Pro` |
| 모델 | PASS | 세션 모델 ID `claude-opus-5-5`. 추론 수준 high는 사용자 설정 기준이며 세션 내부에서 별도 확인하지 않음 |
| 사용량·한도 | 확인 | 컨트롤러가 `/usage` UI에서 세션 18%, 주간 3% 사용을 확인. 세션 초기화 14:49 KST, 주간 초기화 11/2 01:59 KST 표시. 시점에 따라 변함. 비용 $5.19 표시는 세션 추정치이며 청구액 아님 |
| 필수 스킬 8개 | PASS | 현재 세션 카탈로그와 새 프로세스 SDK `initialize`(명령+스킬 461개) 모두에서 `graft`, `archify`, Ponytail 6개 발견 |
| MCP 연결 | PASS | `claude mcp list` 실패 0: Claude Docs, Google Drive, Gmail, Google Calendar, `plugin:ecc:chrome-devtools`, `git` 연결됨. graft MCP는 미설정(미적용 후속안) |
| 업무 인증 차이 | 참고 | Gmail·Drive·Calendar는 전송 연결만 됐고 이 세션에는 인증 도구만 노출됨. 로그인하지 않음. chrome-devtools는 브라우저 실행 가능성 때문에 ping 생략 |
| MCP smoke | PASS | `git_status` 읽기 전용 호출 성공: `main`, `origin/main`과 동기화 |
| 파일 smoke | PASS | `smoke.txt` 표식 `AGENT_PREFLIGHT_2026_10_31`, 2 + 2 = 4 일치. 파일 변경 없음 |

## 한계

- 이 세션은 전역 `~/.claude/CLAUDE.md`(graft 실행 조건) 배포 전에 시작돼 해당 지침이 컨텍스트에 없습니다. 시작 시점의 지침이 유지되므로 graft 조건 적용은 새 세션에서 시험해야 합니다.
- 스킬 발견은 목록 확인이며 설명 예산 내 노출이나 워크플로 실행을 검증하지 않았습니다.
- 사내 월 $466 할당과 집 Pro 구독은 과금 단위가 달라 서로 환산하지 않습니다. 비교는 작업당 토큰 같은 원시 지표로만 합니다.

## 후속

- Gemini CLI 제거와 Antigravity CLI 대체는 **사용자 결정**에 따른 변경입니다. Claude 점검 범위에서는 다루지 않습니다.

## 추가 실제 호출 검증

- `Skill(ponytail:ponytail-help)` 성공. 실제 호출한 것은 대표 스킬 하나이며 다른 7개 전체 워크플로 검증을 뜻하지 않습니다.
- 공개 파일의 표식·산술값 재확인, git MCP `git_status` 재호출 성공.
- 처음 Bash 호출은 `PreToolUse:Bash`의 기존 `Fact-Forcing Gate` 훅이 차단했습니다. Read 도구로 완료했으며 훅을 끄거나 우회하지 않았습니다. 셸 중심 자동화 시험에서는 이 동작을 별도로 기록해야 합니다.
- `/usage`는 ECC 스킬 설명 92개 약 5,044 tok/turn, 총 목록 예산 약 2,000 tok/turn cap을 표시했습니다. 목록 발견과 모든 설명의 모델 노출은 다릅니다. 기존 합의대로 ECC 훅은 보존했습니다.
