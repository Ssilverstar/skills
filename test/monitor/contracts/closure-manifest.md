# Closure manifest — Agent Observatory v2 차수

작성: Claude Opus 5.5(구현 총괄), 확인 시각 2026-10-31T04:51:41Z. 각 항목은 같은 시각에 직접 실행·조회한 결과다(이전 순간의 추정 아님).

## 작업자별 최종 상태

| 항목 | gemini-monitor (w3:pB) | monitor-agents (w3:pA) |
|---|---|---|
| 에이전트·모델 | Antigravity 1.4.12 · Gemini 3.8 Flash (medium) | OpenCode · Qwen3.8 Flash Next (로컬 llama-server) |
| 이번 차수 과제 | FE-005(언어·테마·정렬·배지·해상도) → FE-006(UI 피드백 일괄) | QA-002(보존 정책 v2 독립 검증) |
| 최신 과제 ID | FE-006 | QA-002 |
| 화면 마지막 RESULT | `RESULT: completed results/FE-006.yaml` | `RESULT: completed results/QA-002.md` (턴 3m 28s) |
| Herdr 상태 | idle | idle |
| 화면 승인 대기 | 0건 (visible 확인) | 0건 |
| 산출물 mtime | FE-005.yaml 13:34:25, FE-006.yaml 13:49:51 (KST) | QA-002.md 13:35:42 |
| Claude 독립 재검증 | `node --check` exit 0, `node --test monitor/tests/ui/*.test.js` exit 0 · 26/26 · stderr 0B (Gemini 25 + Claude 통합 1) | 같은 명령 재실행: Python 38/38 OK, `-X dev -W error::ResourceWarning` stderr 경고 0 |
| 판정 | 채택(통합 수정 2건 별도 기록) | 채택(리스크 2건은 Claude 단위 테스트로 보완 확인) |
| 프로세스 | TUI 세션은 열려 있음(대기 상태, 실행 중 과제 없음). 재시작·종료하지 않음 | 동일 |

### 승인 처리 기록(이번 차수)
- Gemini: 한 줄 읽기 전용·검사 명령(`node --check`, `node --test`, `grep -n …`, `ls`, `tail`, `git diff`)만 요청 화면을 먼저 읽고 1회씩 허용. 대화·영구 허용 옵션은 쓰지 않음. 범위 밖 요청 없음.
- OpenCode: 승인 요청 없음(지정 명령만 실행).
- 앞 차수 교훈 반영: 완료 판정은 "화면 마지막 RESULT + 승인 대기 0 + idle"을 함께 확인한 뒤에만 함(GAP-AGY 때 승인 창이 남은 상태를 완료로 잘못 보고했던 것을 정정).

## Claude 통합 변경(작업자 완료 후 소유권 회수)
- `app/static/app.js`: 프로브 라벨 `10080분 한도` 접미사 처리(→ 주간(7일)/Weekly (7d)), 이력 보존 문구를 보이는 해상도 기준(원본 24시간 / 5분 집계 30일)으로 수정. 표식 주석 `통합 수정(Claude)`.
- `tests/ui/integration.test.js`(신규, Claude 소유) 1건.
- `tests/test_server.py`: 보존 정책 v2에 맞춰 TC7·TC8 기대값 갱신(주석 표기).

## 이번 차수 Claude 산출물
- `app/server.py`: 보존 v2(원본 24h·10,000행, 5분 집계 30일·10,000행, 버킷 경계 삭제, 멱등 REPLACE 집계, 늦게 도착한 스냅샷 버킷 재계산, WAL checkpoint·incremental vacuum, 기존 DB 마이그레이션), 원문성 키 제거(`scrub`), `telemetry` 모드, `/api/history` 해상도.
- `tests/test_retention.py`(신규 10건): 경계·건수 상한·멱등·부분 버킷·null·마이그레이션·프라이버시·telemetry.
- `compose.yaml`: 보존 env, 로그 회전(10MB×3), Prometheus `retention.size=2GB`. `compose.lan.yaml` 유지.
- `contracts/api.md` v2, `FE-005.yaml`, `FE-006.yaml`, `native-otel-design.md`(설계·실측 스키마), `README.md`.
- 문서: `test/monitor-gaps.md`, `test/skill-unification-opinion-claude.md`.

## 배포·검증(04:51Z)
- `docker compose -f compose.yaml -f compose.lan.yaml --env-file ../.local/monitor-lan.env up -d --build`: app healthy(127.0.0.1:8787, 192.168.0.65:8787), Prometheus healthy(127.0.0.1:9090), collector 미게시. 로그 옵션 3개 컨테이너 모두 `max-size:10m max-file:3`.
- 실DB 마이그레이션 전 백업: `test/.local/qa002/monitor-pre-v2.sqlite3`(231행, integrity ok). 배포 후 `/health` db_rows 305, agg_rows 17.
- 브라우저(헤드리스 chromium-1243, 호스트 자기 접속): 1440px 에이전트 2×2·세부 정보 접힘·한도 번역, 하드웨어 축·해상도 라벨, 390px 헤더 컨트롤 비겹침 확인. **Windows 실기기 접속은 미확인(사용자 응답 대기)**.
- native OTel smoke(사용자 요청, 별도 headless 프로세스): OpenCode·Claude 각 exit 0, stderr 0B, stdout은 `test/.local/ignored/`만. 결과는 `native-otel-design.md` "실제 송신 스키마 확인".

## 백그라운드 작업·미회수 과제
- Claude가 띄운 백그라운드 셸·모니터: 모두 완료 통지 수신(미완 없음). 로컬 검증용 임시 서버(8791)는 `timeout`으로 종료됨.
- 남은 프로세스: PID 279710 `capture_native_otel.py --seconds 360`(**Codex 소유** 임시 sink, 04:51Z 기준 경과 4분 6초, 360초 후 자체 종료 예정). Claude는 건드리지 않음.
- 미회수 작업자 과제: 없음(FE-005·FE-006·QA-002 모두 회수·판정 완료).
- 커밋·푸시·전역 설정 변경: 없음. 추론 서버 재시작: 없음.

## 추가 차수: native OTel 수신·FE-007 (확인 2026-10-31, Claude)
- gemini-monitor: 최신 과제 **FE-007**, 화면 `RESULT: completed results/FE-007.yaml`, idle, 승인 대기 0. Claude 재검증 `node --check` 0, UI 30/30 stderr 0B. 범위 밖 `grep -rn native_usage test/`(.local 포함) 1건은 취소 후 범위 축소 재요청을 1회 허용. `tests/ui/integration.test.js`(Claude 소유) 미변경(mtime 13:51:16).
- monitor-agents: 최신 과제 QA-002 그대로(추가 배정 없음), idle.
- collector: `otlp/native` 수신(호스트 `127.0.0.1:4318`→컨테이너 4320), metrics allowlist(claude-code·codex_exec, 라벨 model/type/token_type), logs·traces는 `nop` 폐기. 합성 OTLP 검증: 식별자·비허용 지표·미등록 송신자·로그 본문 0건, delta 누적 10+20+30=60. 변경 전 설정 `test/.local/otel-collector.yaml.before-native`.
- 앱 재배포: app healthy, LAN `192.168.0.65:8787` 200, LAN `:4318` 연결 불가(exit 7, 의도). `/api/snapshot` telemetry: 네 에이전트 usage=bridge, `native_usage`는 아직 없음(실제 에이전트 native 설정 전 — 루트 적용 대기). Python 40/40, 경고 0.
- 백그라운드: Claude 모니터·셸 모두 완료 통지 수신. 커밋·푸시·전역 설정 변경 없음.

## 최종 차수: native 정정·공통 런타임·대시보드·MCP (2026-10-31 KST, Claude)

### 작업자 과제 회수
| 작업자 | 최신 과제 | 화면 RESULT | 산출물 mtime | Claude 재검증 | 판정 |
|---|---|---|---|---|---|
| gemini-monitor (Antigravity Gemini 3.8 Flash, w3:pB) | FE-008 | `RESULT: completed results/FE-008.yaml` | 17:20:19 | `node --check` 0, UI 38/38 stderr 0B. 실브라우저 영어 모드 스캔에서 정적 문구·aria 한글 잔존 → AC4 부분 미충족, FE-009 AC6으로 반송 | 부분 채택 |
| gemini-monitor | **FE-009** | `RESULT: completed results/FE-009.yaml`, idle, 승인 대기 0 | 17:37:37 | `node --check` 0, UI 41/41. AC7(추가 요청)은 소유권 회수 후 Claude 통합 수정 | 채택 |
| monitor-agents (OpenCode Qwen3.8 Flash Next, w3:pA) | 스킬 확인(TUI) | `RESULT: skills-check done` | — | 공통 36 + OpenCode 내장 2, ponytail-help 읽기(도구 1회, 편집·셸 0) | 채택 |
| monitor-agents | **QA-003** | `RESULT: pass results/QA-003.md`, idle, 승인 대기 0(문맥 압축 1회 후 자체 재개, 22분) | QA-003.md 18:01:10, lang_dom_check.py 17:53:23 | 현재 빌드에서 Claude가 `tests/lang_dom_check.py` 재실행 exit 0·stderr 0B: 1440/390 × 3뷰 한글 0(option·텍스트 노드·속성 포함, 한국어 로드→영어 전환), MCP 카드 4(gemini 없음), 저장소 필터 1행, 가로 스크롤 없음, 콘솔 오류 0. 1차 실행에서 skills 한글 1건 검출 → Claude 결함 수정 2 후 0 | 채택 |

### Claude 통합 수정(작업자 idle·결과 제출 후)
- `app.js`: FE-009 AC7 — 스킬 분류는 프로브 `common_enabled_count`·`platform_extra_count` 우선(압축본 유지, 없을 때만 목록 계산), MCP connected 라벨 `연결 확인(디스커버리)`/`Connected (discovery)`. 앞서 `formatSkillCounts`·`sortTitle`·`formatGpuProcesses`·`gpuVramNa`·`nativeUsageLimit`. 새 MCP·분류 표는 공용 `setupSortableHeader` 사용(정렬·키보드·aria-sort 동일) 확인.
- `tests/ui/fe009_features.test.js` 85·91행 라벨 기대값 갱신(소유권 회수), `tests/ui/integration.test.js` 8건(Claude 소유).
- **루트 E2E 결함 수정**: `calculateMcpSummary` 기본 id가 `claude,codex,gemini,opencode`라 실제 `antigravity`에 더해 가짜 `gemini` 카드(5개)가 생김 → 계약 id `codex,claude,opencode,antigravity`로 정정, FE-009 fixture의 누락 에이전트 예시도 `antigravity`로, 회귀 테스트 "정확히 네 호스트" 추가. 재배포 후 실브라우저 MCP 카드 4개(CODEX/CLAUDE/OPENCODE/ANTIGRAVITY), 표 13행(공통 3×4 + Codex 플랫폼 `node_repl`). QA-003에 4개 검증 항목 전달.
- **루트 시각 리뷰 결함 수정 3**: Antigravity `common_enabled_count:null`(활성 미확인)을 목록 계산으로 대체해 공통 활성 0으로 보이던 문제 → 필드가 있으면 명시적 null도 미확인으로 보존, 필드 부재만 목록 계산. 회귀 테스트 1건. 재배포 후 영어 분류 표 `antigravity 36 36 Unknown 0 …` 확인.
- **루트 스크린샷 결함 수정 4**: 공용 `el()` 헬퍼가 `attrs.children`을 무시해 MCP 상세표 Agent 열 13행 전부와 모델별 점유율 라벨(`limit-labels`)이 비어 보임 → 헬퍼에서 `attrs.children`도 처리(두 호출부 동시 해결). 재배포 후 실브라우저: MCP 13행 Agent 공백 0, id 집합 {antigravity, claude, codex, opencode}, 점유율 라벨 공백 0(`claude-langscan/mcp-table-en.png`). DOM 헬퍼라 단위 테스트 대신 루트 E2E의 행별 agentName·id 집합 단언으로 회귀 보호. **이것이 Claude의 마지막 앱 편집**(이후 편집 중단).
- **루트 E2E 결함 수정 2**: 스킬 에이전트 필터 `<select>`가 첫 렌더 때 한 번만 만들어져 영어 전환 후에도 '저장소 원본' 옵션이 남고, 옵션 값이 번역 라벨이라 전환 뒤 필터가 어긋남 → 고정 값 `__repository__` + 렌더마다 라벨 재기록. 실브라우저: 영어 전환 후 옵션 `All Agents … Repository Origin`, 저장소 필터 1행(herdr-orchestrate). Claude 스캔에 `<option>` 텍스트 추가 후 영어 모드 한글 0건(`claude-langscan/repo-fix.json`). Claude 첫 스캔이 닫힌 select의 옵션을 수집하지 않아 놓친 사례로 기록. QA-003에 항목 전달.

### Claude 산출물(이번 차수)
- native 정정(독립 리뷰): `otel-collector.yaml` `cumulative_to_delta` → 라벨 정리(+수신 시각 `Now()`, scope name/version 제거) → `delta_to_cumulative`, exporter `send_timestamps`; Codex 송신자 `codex_exec`+`codex-app-server`. `server.py` 마지막 수신 질의 `max(max_over_time(timestamp(m)[24h:1m]))`(창 포맷 결함 수정 포함). `tests/native_pipeline_check.py`(도커 fixture: 2세션 cumulative+reset 41, delta 순서 역전·한 요청 2세션 15, Codex exec 290/3 · app-server 10/1, 미허용 지표·송신자 drop, 식별자 미노출, 이전 구성에서 실패). 백업 `test/.local/otel-collector.yaml.before-native-delta`, `…before-codex-app-server`.
- 계약 `api.md` v2.2~v2.5(native 정정, 공통 스킬 수·GPU 프로세스 메모리, `snapshot.mcp`, 프로브 계수·디스커버리 의미). 과제 `FE-008/009.yaml`, `QA-003.yaml`. 테스트 `McpPassThroughTest`.
- 공통 런타임 검증 `test/results/common-runtime-claude.json`(비식별): Claude headless 36/36(ECC 13은 `ecc-common:*`, plugin 오류 0, 보안 hook 단일 출처), Antigravity headless 36+내장 2·ponytail-help, OpenCode headless는 정지 반복 → 루트 지시대로 TUI 경로 검증. MCP 디스커버리: Claude headless·OpenCode 3/3 connected, `agy mcp list` 3/3 enabled(설정 목록). 실제 도구 호출 12조합 PASS는 루트 `test/results/common-mcp.json`.

### 최종 검증(Claude 실행)
- Python `-W error` 41/41 OK, stderr Warning 0. UI `node --test --test-isolation=none tests/ui/*.test.js` 45/45, stderr 0B(결함 수정 3건 후. 루트 sandbox 기본 격리 모드는 파일 8개 요약만 보여 줌). `tests/native_pipeline_check.py` ok.
- 실브라우저(Chromium 1243 headless, 호스트 자기 접속): 영어 모드 #agents/#hardware/#skills × 1440·390px, details 전부 펼침·6h 범위 클릭 후 **보이는 텍스트·title/aria-label/placeholder/alt 한글 0건**, 가로 스크롤 없음, 콘솔 오류 0(`test/.local/ignored/claude-langscan/fe009.json`).
- 실제 native: headless Claude 2회 input 2+2=4·output 4+4=8 누적, 라벨 `model`·`type`만, `last_received_at`=실제 수신 시각. `/api/snapshot` claude `native_usage` 표시, `usage`는 bridge 유지.
- 배포: app healthy(127.0.0.1·192.168.0.65:8787), collector ok(경고 0), Prometheus healthy. `/health` db_rows 1181, agg_rows 62.

### 승인 처리
- Gemini: 한 줄 읽기 전용·검사 명령(`node --check`, `node --test`, `grep -n`, `ls`, snapshot/index.html 읽기 `node -e`)만 화면 전문 확인 후 1회씩 허용(대화·영구 허용 미사용). Antigravity는 승인 창이 떠도 herdr `idle`로 보고되어 화면 grep 감시로 처리.
- OpenCode: 헤드리스 3회 정지(자체 timeout 무시 1회 → Claude 소유 프로세스만 종료).

### 백그라운드·미회수
- Claude 화면 감시·백그라운드 셸: 전부 완료 통지 수신, 엄격 감시 1개(`bx15ryd0p`)는 조건 교체 위해 TaskStop. 남은 Claude 백그라운드 작업 0, 임시 컨테이너 `native-pipeline-check` 없음.
- 작업자: gemini-monitor 최신 FE-009(idle), monitor-agents 최신 QA-003(idle). 미회수 과제 0. 패널은 닫지 않음(루트 담당).
- 잔여 알려진 위험: 프로브 동적 문구 1건(skills.notes의 OpenCode 허용 목록 안내)이 번역표에 없어 영어 모드에서 'Korean-only probe text (not translated)'로 대체 표시(규칙상 정상, 원문 영어화는 프로브 쪽 후속). **루트 후속: 해당 안내를 host_probe.py의 영어 원문으로 교체하고 프로브 10개 검사 통과·서비스 재시작으로 반영했습니다.** Windows 실기기 접속 미확인. OpenCode fresh headless 정지 미해결.

### 최종 판정 (Claude, 2026-10-31 18:0x KST)
- 독립 재검증: Python 41/41(경고 0), UI 45/45(`--test-isolation=none`, stderr 0B), `native_pipeline_check` ok, QA-003 DOM 검사 재실행 pass, 루트 E2E 12 재통과(루트 보고).
- **구현분 커밋·main 병합에 동의.** 앱 편집 종료.

### 공통 정책 Opus 동의 (distribution/skill-policy.md, profiles/common-general-sw.json, profiles/common-mcp.json, instructions/common.md)
- **동의.** 네 에이전트 공통 36 + 공통 MCP 3(git·GitHub v2.0.3 digest 고정·Chrome DevTools 1.10.1), 플랫폼 내장·앱·OAuth·보조 명령은 공통 수와 섞지 않고 별도 계수, 등록·설정·실행 성공을 다른 증거로 구분 — Opus 재검토(`common-skill-review.md`)와 이번 실측에 부합.
- 조건·잔여: ① OpenCode fresh headless는 정지 재현(기본 모델 지정 후에도) → 스킬 확인은 TUI 경로만, headless 회복은 미확인. ② Antigravity 스킬 활성 상태는 미확인(null)으로 남김. ③ MCP `connected`는 디스커버리, 실제 읽기 호출 12조합 PASS는 루트 증거(`test/results/common-mcp.json`)에 의존. ④ 원본 ECC 전체 노출 예외 폐기는 `ecc-common` 이름 분리 후 Claude 36/36·plugin 오류 0·보안 hook 단일 출처로 확인.

### 최종 diff 범위(Claude 소유분, 커밋 없음 · 브랜치 feat/agent-observatory-common-runtime는 루트 생성)
- `test/monitor/app/server.py`(native 마지막 수신 질의·창 포맷), `otel-collector.yaml`(세션 합산 파이프라인·수신 시각·codex-app-server), `contracts/api.md` v2.2~v2.5, `contracts/FE-008·FE-009·QA-003.yaml`, `closure-manifest.md`, `README.md`·`native-otel-design.md` native 절, `tests/test_retention.py`(McpPassThrough·native 창), `tests/native_pipeline_check.py`, `tests/ui/integration.test.js`(9건), `app/static/app.js` 통합 수정(위 목록), `test/results/common-runtime-claude.json`.
- 작업자분: Gemini `app/static/{index.html,style.css,app.js}`, `tests/ui/{index.js,fe008_features.test.js,fe009_features.test.js}`, `contracts/results/FE-008·FE-009.yaml`. OpenCode `tests/lang_dom_check.py`, `contracts/results/QA-003.md`(회수 대기).
- 전역 설정·host_probe.py·루트 문서는 미수정.
