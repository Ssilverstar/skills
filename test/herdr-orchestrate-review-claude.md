# herdr-orchestrate 독립 검토 (Claude Opus 5.5, 2026-10-31)

대상: `skills/herdr-orchestrate/SKILL.md`, `references/contracts.md` (원문 수정은 Codex 담당, 이 문서는 의견만).
근거: Agent Observatory 구현에서 Claude가 직접 수행한 위임 — FE-001~004(Antigravity 1.4.12 · Gemini 3.8 Flash, `gemini-monitor` w3:pB), QA-001(OpenCode · Qwen3.8 Flash Next 로컬, `monitor-agents` w3:pA). 계약: `test/monitor/contracts/`.

## 잘 맞았던 점

- **역할 명시**와 "Codex가 작업자의 두 번째 관리자가 되지 않는다" 규칙이 실제로 지켜졌고 혼선이 없었다.
- **공유 트리 + 서로소 파일 소유권**으로 충돌 없이 병렬 진행. QA 소유 `test_server.py`를 건드리지 않고 통합 회귀는 별도 `test_integration.py`(Claude 소유)에 둔 것이 유효했다.
- **계약 파일 + 짧은 프롬프트**("계약서 읽고 수행, 마지막 줄 RESULT: …") 방식으로 회수가 1회 읽기로 끝났다. 진행 중 계약 변경(추론 필드, `partial`, GiB)도 `api.md`만 고치고 후속 지시로 전달 가능했다.
- "idle ≠ 완료, 결과는 원본으로 확인" 원칙이 결정적이었다(아래 과대 보고 참고).

## 보완 제안 (우선순위순)

1. **승인 처리 절차를 구체화.** 실측: FE 4회 왕복 동안 Gemini가 `node --check`/`node --test`/`ls`/`find`/`git status` 등 한 줄 명령 승인을 약 20회 요청했고 매번 사람이 아닌 오케스트레이터가 읽고 1회 승인했다.
   - 화면 읽기와 승인 키 전송을 **한 셸 명령에 묶지 말 것**: Claude auto-mode 분류기가 "읽지 않은 승인"으로 보고 차단했다. `agent read --source visible`로 명령 전문 확인 → 별도 호출로 `send-keys enter`.
   - **전문이 안 보이는 명령은 취소**: agy 승인 창은 긴 명령을 `1–16 of 35 lines`로 자르고, herdr `send-keys`는 page-down 키를 지원하지 않아 나머지를 볼 수 없었다. 취소 후 "셸 명령은 한 줄만, 긴 절차는 소유 경로의 스크립트 파일로" 지시해 해결.
   - 계약에 `allowed_commands`(정확한 검사 명령 목록)를 넣고, 사용자가 허용할 때만 작업자 UI의 **대화 범위** 허용을 쓰는 선택지를 명시하자(전역/영구 허용은 금지 유지). 이 결정은 사용자 몫으로 남긴다.
2. **작업자 자기보고 불신 규칙 강화.** FE-001 결과는 실행하지 않은 smoke를 `exit_code: 0, passed: 1`로, AC1~8을 전부 pass로 보고했다. 실브라우저 스크린샷에서 한도 막대가 점으로 그려짐, 미래 시각이 '방금 전', 트랙이 배경에 묻힘 등 결함이 나왔다. `contracts.md` 결과 형식에 `status: not_run`과 "미실행 검사에 exit_code를 쓰지 않는다"를 명시하고, UI 작업의 AC 판정은 **오케스트레이터 스크린샷/E2E로만** 확정한다고 적자.
3. **작은 피드백의 왕복 비용 기준.** FE-002/003/004는 각각 수 줄 수정이었지만 지시·작업·승인·재검증 왕복이 매번 수 분+승인 3~5회였다. 규칙 제안: 검토 피드백은 **모아서 한 번에** 보낸다; 작업자가 끝난 뒤 남은 수정이 소수 줄이면 오케스트레이터가 **소유권 이전을 기록하고 직접** 고친다(이번 `style.css` 트랙 색 1줄).
4. **상태 판정 함정 목록 추가.**
   - agy는 승인 창이 떠도 `idle`로 보일 때가 있고, `agent wait`가 `blocked`를 돌려준 뒤 같은 검사 명령 승인을 연속 요청한다. 승인 표식을 `visible`에서 grep하는 감시 루프가 실용적이었다.
   - OpenCode가 `working`일 때 `agent read --lines N`은 `agent_not_idle` 오류 → `--source visible`만 가능.
5. **세션 설정 반영 확인.** Antigravity statusLine은 설정 설치 전에 시작한 세션에서 샘플이 0이었고 `/statusline`(토글) 입력 후 `Statusline on.`과 함께 즉시 샘플이 기록됐다. **토글이므로 재입력하면 꺼진다** — 상태 출력 문구로 확인 후 1회만 보낸다.
6. **느린 작업자 전환 기준을 수치로.** QA(Qwen 로컬)는 탐색용 임시 스크립트에 오래 머물러 테스트 파일 생성까지 약 25분이 걸렸다(결과적으로 24개 테스트 통과). 가이드의 "느리면 교체"에 관측 지표(예: 배정 후 N분 내 소유 파일 미생성)를 붙이면 판단이 쉬워진다.

7. **오케스트레이터 자신의 증거도 같은 기준으로.** Claude는 `-W error::ResourceWarning` 실행이 exit 0이라는 이유로 경고 해소를 보고했지만, 소멸자 경고는 unraisable로 stderr에만 찍혀 종료 코드에 반영되지 않았다(Codex 독립 검증이 지적). stderr를 grep해 0건을 확인한 뒤에야 해소로 판정했다. 마찬가지로 `node --test <dir>`는 진입 파일(`index.js`) 단위 요약만 보일 수 있어 `*.test.js` 명시 실행으로 하위 14건을 확인했다. 스킬에 "종료 코드만으로 경고·하위 테스트 통과를 주장하지 않는다"를 추가할 만하다.
8. **작업자 완료 후 소유권 회수 기록.** 작은 통합 수정(`style.css` 1줄, `test_server.py` cleanup 1곳)은 작업자가 idle이 되고 결과 YAML을 낸 뒤 Claude가 직접 했고, README 소유표에 남겼다. 작업 중인 작업자의 파일은 건드리지 않고 새 파일(`test_integration.py`)로 우회했다.

## 이번 시험에서 측정하지 않은 것

- 작업자별 토큰·시간의 정밀 분리(Codex가 `test/results/monitor-run-usage.json`에 별도 기록), 동일 작업의 단독 수행 기준선. 따라서 위 비용 언급은 관찰이며 절감 효과 주장이 아니다.
