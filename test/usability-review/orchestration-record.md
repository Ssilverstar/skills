# UX-001 오케스트레이션 기록 (Claude 통합)

관측 시각 2026-10-31T12:45Z · 기준 main 913b5a8 · 브랜치 feat/observatory-usability-review(미커밋, 커밋/푸시는 root)

## 역할
| 역할 | 주체 | 비고 |
|---|---|---|
| 총괄·계약·리뷰·통합·배포·기록 | Claude Opus 5.5 high (w3:pC) | |
| 구현 | argon-ui (w3:pD), Antigravity CLI, Gemini 4 Argon · medium (`gemini-4-argon-medium`, root 확인) | static 3파일 + `tests/ui/usability.test.js` |
| 실화면 기준선·독립 최종 E2E·커밋 | root (Codex) | `independent_check.py`, `visual_check.py`, `before-checks.json`, `baseline.json`, `test/README.md` 수정 소유 |

계약: [contract.md](contract.md). 범위 A~F + root 보충(common 중복 우선순위, AGY 미확인 유지, `--test-isolation=none`).

## 진행
| 시각(UTC) | 사건 |
|---|---|
| 11:52 | UX-001 지시 전송 |
| 11:53 | 승인: `node --test --test-isolation=none test/monitor/tests/ui/*.test.js` (전체 명령 확인 후 이 대화 한정 옵션 2) |
| 11:56 | 첫 산출물(index.html), 10분 확인 시점 이전 |
| ~11:59 | 결과 없이 `Interrupted · What should Antigravity CLI do instead?`(원인 화면에 없음, 단정 안 함). 상태 idle, app.js 미수정 |
| 12:00 | 재개 지시 1회(실측 근거 묶음 전달) |
| 12:07 | 승인: `node --check test/monitor/app/static/app.js` (이 대화 한정 옵션 2) |
| 12:08:53 | 작업자 마지막 파일 변경. RESULT 수신(형식 편차: passed/partial 표기 없음, `pass=50 fail=0` 주장) |
| 12:3x | 소유권 회수(작업자 파일 해시 불변 확인 후). 통합 수정 아래 |
| 12:41 | LAN override 배포(app만 재빌드) |

감시기 오탐 2회(제 프롬프트 문구에 매칭) → 패턴을 실제 결과/중단 문구로 좁힘. 사람 개입: root 보충 지시 3회(계약 보충, 재개 요청, I-1 제안).

## 통합 수정 (Claude, 회수 후)
1. 연결 끊김 배너: live region(`#error-msg`)엔 고정 문구, 경과 시간은 `aria-hidden` `#error-elapsed`에 매 실패 폴링마다 갱신(A2 경과 표시 + D3 반복 낭독 방지 동시 충족). `resolveConnectionStatus`에 `errorBannerLive` 필드 추가.
2. 차트 aria 요약 값 소수 1자리 반올림.
3. 스크롤 보존: 실제 스크롤러는 `<body>`(기존 CSS `html, body {height:100%; overflow-x:hidden}`)라 `window.scrollY` 기반 복원이 무효 → `document.body.scrollTop/Left`도 캡처·복원.
4. I-1: Antigravity 프로필 모델 태그를 "설정 모델 / Configured model"로 표기(probe `configured_model` = 설정값). probe에 출처 필드가 없어 id로 분기(`ponytail:` 주석). 모델별 사용량 분해 가능 주장 없음.
5. `usability.test.js`에 통합 테스트 1개 추가.

## 정정
- 제가 RED 단계에서 보고한 "새로고침 시 scrollY 0 리셋"은 **유효한 증거가 아님**: Playwright `click()`이 헤더 버튼을 화면에 넣으려 스크롤러를 맨 위로 옮긴 테스트 부작용 + window 대신 body가 스크롤러. 변경 전 실제 스크롤 동작은 판정하지 않음(not_run). 변경 후는 프로그램 클릭(폴링과 같은 재렌더 경로)으로 보존 확인.
- 기존 테스트 수: 처음엔 monitor 범위만 세어 96(Python 41 + host_probe 10 + node 45)으로 기록했으나, `test/results/final-verification.json`의 저장소 프로필 테스트 5개(`python3 -m unittest discover -s tests`, 저장소 루트)를 빠뜨린 것이었다. 기존 101 = 5 + 10 + 41 + 45. 변경 후 5개도 재실행 OK(2026-10-31, exit 0). 변경 후 합계 107 = 5 + 10 + 41 + 51.

## 검증 (변경 후, 배포본)
| 명령 | exit | 결과 |
|---|---|---|
| `node --check test/monitor/app/static/app.js` | 0 | |
| `node --test --test-isolation=none test/monitor/tests/ui/*.test.js` | 0 | tests 51 / pass 51 (기존 45 + 작업자 5 + 통합 1) |
| `.local/monitor-venv/bin/python -m unittest discover -s monitor/tests -p 'test_*.py'` | 0 | 41 OK (서버 무변경) |
| `python -m unittest test_host_probe` (monitor/) | 0 | 10 OK |
| `uv run --offline --no-project --with playwright python test/monitor/e2e_check.py --output test/usability-review/e2e-after.json ...` | 0 | PASS 12 checks, browser_errors [] |
| `uv run ... python test/usability-review/regression_check.py` | 0 | UX-001 시점 PASS 7/7, UX-002 후 넘침 검사 4개 추가해 PASS 11/11 → [regression-results.json](regression-results.json) (변경 전: [regression-before.json](regression-before.json) 7 FAIL) |
| root `independent_check.py --output <scratchpad>` (미리보기, root 산출물 미기록) | 0 | PASS 7/7 @ LAN URL. 최종 판정은 root 재실행 |

regression 주요 실측: 기본 common 145행 / 전체 836행(실행 중 probe 데이터 갱신으로 812→836), 에이전트별 common 36행·Claude 중복 0, AGY 미확인 36·활성 0, 바로가기 hash `#skills` 유지·제목 포커스, 스크롤 900/가로 80 유지, 390/768/1440 muted 최소 12px·대비 dark 7.39 / light 5.77(이전 light 1.79), 390px 컨트롤 42px.
스크린샷(git 제외): `test/.local/usability-review/after/`. 직접 확인: agents-390-dark, skills-1440-light-en.

## 배포
`docker compose -f compose.yaml -f compose.lan.yaml --env-file ../.local/monitor-lan.env up -d --build app` → healthy, `127.0.0.1:8787`·`192.168.0.65:8787` 200, Prometheus/collector 무변경. LAN 제공 파일 해시 = 소스: app.js `7d6a5593ec32`, style.css `19b72a6b601d`, index.html(`/`) `991c3ddafa8b`.

## UX-002 (Claude 직접, 13:0xZ) — 768px 헤더 넘침
- 발견(root 강화 검사): `body.scrollWidth` 기준 768px 3뷰×2테마 6 FAIL. 테마 버튼 잘림, 헤더 날짜 과다 줄바꿈. 기존 `documentElement.scrollWidth` 검사(e2e·내 검사 포함)는 body가 스크롤러라 이를 놓침.
- 원인: 761–1100px은 사이드바(240px)가 남아 헤더 폭 약 500px인데 `.top-header`가 높이 64px 고정·줄바꿈 없음.
- 수정(style.css만): `@media (max-width:1100px)`에서 `.top-header` 높이 auto·`flex-wrap`, `.header-right` wrap, `.timestamp-value` nowrap. KPI 토큰 값(`.kpi-label-stack + .kpi-metric-val`) nowrap으로 "99.3 / M" 분리 해소. app.js·index.html 무변경. 작업자 재위임 없음.
- 검증: node 51/51(exit 0). LAN 재배포 healthy. `regression_check.py`에 body+document scrollWidth·헤더/메뉴 잘림 검사(390/768/1024/1440 × dark/light × 3뷰) 추가 → 전체 11/11 PASS. 768 light-en 스크린샷 직접 확인(`test/.local/usability-review/after/agents-768-light-en.png`).
- 새 해시(LAN 제공 = 소스): app.js `7d6a5593ec32`, style.css `0da65504ba37`, index.html(`/`) `991c3ddafa8b`.

## 종료 매니페스트
| 항목 | 값 |
|---|---|
| UX-001 / argon-ui | 작업 완료(통합 회수), **프로세스 유지**(idle, 입력 프롬프트, 대화상자·대기 프롬프트 없음 12:44:49Z) |
| 산출물 해시(UX-002 후) | app.js 7d6a5593…, style.css 0da65504…, index.html 991c3dda…, usability.test.js 4252375f… |
| 배경 감시기 | 모두 종료 |
| root 최종 | 강화 visual_check에서 768 6 FAIL → UX-002로 수정·재배포. visual18 재실행은 root 예정(이 기록 시점 결과 미수신) |
| 미해결 | root visual18 재실행 결과, 커밋/푸시 |

## 남은 제약
- 스크롤러가 body인 기존 레이아웃은 유지(재설계 범위 밖). root·e2e의 `documentElement.scrollWidth` 가로 넘침 검사는 body 스크롤러 기준으로도 유효한지 별도 검토 여지.
- I-1은 id 분기. probe가 모델 출처 필드를 내면 그 필드로 대체.
- 차트 호버 값은 마우스 전용(키보드 탐색 없음), aria 요약으로 대체.
