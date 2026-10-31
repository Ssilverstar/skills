# UX-001 계약: Agent Observatory 사용성·정확성·접근성 개선

```yaml
task: UX-001
orchestrator: claude (Opus 5.5 high, pane w3:pC)
worker: argon-ui (pane w3:pD, Antigravity CLI, model gemini-4-argon-medium — UI 표시 "Gemini 4 Argon · medium")
base: main 913b5a8, 공유 브랜치 feat/observatory-usability-review
write:
  - test/monitor/app/static/app.js
  - test/monitor/app/static/style.css
  - test/monitor/app/static/index.html
  - test/monitor/tests/ui/usability.test.js   # 신규
do_not_edit: 위 4개 외 전부 (server.py, host_probe.py, contracts/, compose*, e2e_check.py, 기존 tests/ui/*.test.js, tests/*.py, test/usability-review/*)
read_only_refs:
  - test/monitor/README.md, test/monitor/contracts/api.md
  - test/monitor/e2e_check.py   # 기존 e2e가 쓰는 id·동작 유지 필요
  - test/usability-review/baseline.json   # root 실측 정리본
  - test/usability-review/independent_check.py   # root 소유 독립 검사. 수정 금지
first_artifact_checkpoint: 10분 (app.js 또는 usability.test.js 첫 변경)
```

## 제약
- 서버·DB·API·하드웨어/네이티브 OTel/보존(retention) 의미 계약은 바꾸지 않는다. 새 DB, 외부 CDN·라이브러리, 전역 설정 변경 금지.
- 기존 id·표·`data-i18n` 키 유지. 기존 e2e(`e2e_check.py`)가 쓰는 선택자: `#agent-tokens-tbody`, `#agent-kpi-container .kpi-tile`, `#nav-*`, `#view-*`, `#gpu-details`, `#inference-details`, `#chart-svg-gpu-util svg`, `#snapshot-history-tbody`, `#skills-summary-cards .skill-summary-card`, `#mcp-container .kpi-tile`, `#mcp-status-tbody`, `#input-skill-search`, `#filter-skill-agent`(값 `ALL`, 에이전트 id, `__repository__`), `#skills-tbody`, `#btn-toggle-lang`, `#btn-toggle-theme`, `th button`, `th[aria-sort]`, `details`.
- 알 수 없는 값은 "미확인/Unknown"으로 두고 0으로 바꾸지 않는다.
- 영어 모드에서는 화면·옵션·title·aria-label·placeholder가 모두 영어여야 한다. 언어 버튼 문구는 현행(`English`/`Korean`)을 유지한다.
- 15초 폴링과 해시 라우팅(`#agents|#hardware|#skills`)은 유지한다. 페이지 안 이동 때문에 `location.hash`를 바꾸지 않는다.
- 최소 변경을 우선한다. 새 프레임워크·가상 스크롤·대규모 재구성은 하지 않는다.

## 수용 기준

### A. 연결 실패 표시
1. `/api/snapshot` 요청이 실패하면(네트워크 오류 또는 non-2xx) 상태 배지와 사이드바를 "연결 끊김 / Disconnected"(경고 이상 색)로 바꾼다. 마지막으로 성공한 데이터는 화면에 그대로 둔다.
2. 오류 배너에는 마지막 성공 시각과 경과 시간을 표시한다. 상대 시간("n초 전")은 폴링과 무관하게 실제 경과를 반영한다. 클라이언트에서 계산해도 된다.
3. 다음 요청이 성공하면 오류 배너를 숨기고 배지를 서버 `status`(ok/stale/waiting)로 되돌린다. 복구 사실은 한 번 알린다. 예: 상태 영역에 "연결 복구됨"을 다음 폴링까지 표시.

### B. 만료된 한도
1. `reset_at`이 현재 시각보다 과거인 한도 항목은 KPI의 "최대 한도" 선택(`selectMaxLimit`/`calculateAgentKpi`)에서 제외한다.
2. 프로필 카드에서는 해당 항목을 "초기화됨·갱신 대기 / Reset — awaiting update"로 표시한다. 사용률은 관측 당시 값임을 밝히고, 진행 막대와 숫자를 0으로 바꾸지 않는다.
3. 모든 한도가 만료되었으면 KPI에 "갱신 대기"를 표시한다. `reset_at`이 없거나 파싱되지 않으면 현행처럼 현재 값으로 취급한다.
4. 순수 함수 단위 테스트를 둔다. 경우: 만료 1개+유효 1개, 전부 만료, `reset_at` 없음.

### C. 재렌더링 시 상태 보존
root 재현: 에이전트 카드의 `details`를 연 뒤 수동 새로고침하면 닫힌다(baseline `details_refresh`: before_open=true, after_open=false). 키보드 focus baseline은 판정 유보로 기록되어 있다.
1. 자동 폴링, 수동 새로고침, 언어 전환 후에도 다음이 유지되어야 한다.
   - `details` 열림 상태(에이전트 id 등 안정 키 기준)
   - 정렬(현재 `state.sortState`)과 필터·검색어
   - 창 스크롤과 `.table-scroll` 가로 스크롤
   - 키보드 포커스: 정렬 버튼은 table+column 키 기준, 그 밖에는 id 기준
2. 정렬 버튼을 클릭하거나 Enter/Space로 누른 뒤에도 포커스가 같은 열 버튼에 남아야 한다.
3. 권장 구현: `renderSnapshot`과 `setupSortableHeader` 안에서 렌더 전에 열린 details 키, 활성 요소 식별자, 스크롤 위치를 모으고 렌더 후 복원한다. 정렬 버튼에 `data-sort-table`/`data-sort-col`을 붙인다.

### D. 차트·범위 버튼·알림
1. 각 차트 SVG에 `role="img"`를 붙이고, 지표명·범위·최근·최소·최대·단위를 요약한 `aria-label`을 단다. 데이터가 없으면 그 사실을 알린다. 호버 값은 SVG `<title>` 자식 요소로 제공한다. svg의 `title` 속성은 툴팁으로 보이지 않는다.
2. 범위 버튼(`.btn-range`)에 `aria-pressed`를 달고 현재 범위와 일치시킨다.
3. stale·오류 알림 문구는 상태가 바뀔 때만 갱신해 매 폴링마다 다시 낭독되지 않게 한다. 계속 바뀌는 경과 초는 live region 밖, 즉 헤더 시각 표시에 둔다.

### E. 스킬 뷰 탐색과 필터
root 실측: 스킬 표 812행, MCP 요약이 1440px 폭에서 1504px, 390px 폭에서 2552px 아래에 있다.
1. 스킬 뷰 상단에 "개요 / 스킬 목록 / MCP" 섹션 바로가기를 둔다. 버튼으로 만들어 `scrollIntoView`로 이동하고, 대상 제목(`tabindex="-1"`)에 포커스를 준다. hash는 바꾸지 않는다. 메인 3메뉴는 그대로 유지한다.
2. 범위 필터 `#filter-skill-scope`를 추가한다.
   - `common`(기본): `common_id`가 있는 행을 보여 주되, 같은 (agent, common_id)는 한 행으로 줄인다. 대표 행 선택 순서는 활성(true) → 미확인(null) → 비활성(false)이다. 비활성 캐시 복제본 때문에 기본 목록이 중복되면 안 된다. Antigravity처럼 실제 선택 상태가 미확인인 행(`enabled=null`)은 빠뜨리지 않고 "미확인"으로 표시한다.
   - `all`: 등록된 원본 행을 줄이지 않고 그대로 보여 준다(현행 812행).
   - 저장소 원본 행(`isRepo`)은 이 필터의 영향을 받지 않는다. `__repository__`를 선택하면 언제나 저장소 행이 보인다.
   - 참고(현재 실측): Claude는 `common_id`가 있는 행이 50개이고 고유 값은 36개다. 활성 행은 39개, 그중 공통은 36개다.
3. 상태 필터 `#filter-skill-status`를 추가한다. 값: `ALL` / `enabled`(true) / `disabled`(false) / `unknown`(null).
4. 표 위에 "표시 N행 / 전체 M행"을 표시하고 `aria-live="polite"`를 단다. Claude는 같은 `common_id`가 중복 행으로 나올 수 있으므로 "행" 단위로 센다.
5. 요약 카드와 분류 표의 수치(공통 선택 36, 설치 수, 활성 수 등 서버 집계값)는 필터와 상관없이 그대로 둔다.
6. 기존 e2e 동작을 유지한다.
   - 검색 `ponytail-help` + ALL → 4행 이상
   - `opencode` → 1행
   - `__repository__` 행 수는 언어 전환 후에도 같아야 함
   - 옵션 문구 'Repository Origin' 유지

### F. 모바일·가독성
1. 390, 768, 1440px 폭에서 3메뉴가 모두 잘리지 않고 보이며 누를 수 있어야 한다. 390px에서 첫 메뉴가 잘리는 현상을 고친다. 페이지 가로 넘침은 없어야 한다.
2. 760px 이하에서는 헤더 버튼, 메뉴, 범위 버튼, 필터 입력·선택, 정렬 버튼, 섹션 바로가기의 터치 높이를 40~44px 이상으로 한다.
3. 보조(muted) 문구는 최소 12px로 하고, 다크·라이트 두 테마 모두 배경 대비 4.5:1 이상을 맞춘다. root 실측: KPI 라벨 11px·#8f8e86, 헤더 툴바 버튼 높이 26px.
4. KPI 토큰 라벨 옆이나 아래에 "관측된 세션 누적 · 청구량 아님 / Observed session total · not billing"을 짧게 표시한다. 한국어·영어 모두.

## 검증 (작업자 실행 범위; 목록은 범위이지 권한 부여가 아님)
```
node --check test/monitor/app/static/app.js
node --test --test-isolation=none test/monitor/tests/ui/*.test.js
```
- `--test-isolation=none`으로 실행해 개별 테스트 수(`ℹ tests`)를 확인한다. 기준선은 45개이며, 결과는 45 + 새 테스트 수 이상이어야 한다. 파일 단위 요약을 테스트 수로 혼동하지 않는다.
- `usability.test.js`는 A~F의 순수 함수 또는 DOM 없이 검증 가능한 부분을 다룬다. 최소 항목: B 만료 처리, A 상태 결정 함수, D aria 요약 문자열, E 필터 함수와 개수. 기존 45개 테스트는 모두 통과해야 한다.
- 브라우저 회귀, 배포(`docker compose up -d --build`), 기록은 orchestrator가 한다. 작업자는 서버를 재시작하거나 docker를 실행하지 않는다.

## 결과 형식 (작업자 → orchestrator)
```
RESULT UX-001: passed|partial|blocked
changed: <files>
tests: <command> exit=<n> pass=<n> fail=<n>
not_done: <기준 번호와 이유>
risks: <짧게>
```
