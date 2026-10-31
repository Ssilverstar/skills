# GAP-AGY: Antigravity CLI 사용량 노출 정보 확인 및 차이 분석

- 작성자: Antigravity (Gemini 3.8 Flash)
- 일시: 2026-10-31
- 근거: `test/monitor-gaps.md` §2-A, `agy --version`, `agy --help`, `test/.local/monitor/antigravity-sessions/*.json`, 공식 문서(https://antigravity.google/docs/cli/statusline/)

---

## 1. 개요 및 검증 기준

Antigravity CLI가 공식적으로 노출하는 사용량·세션·토큰 정보의 실측 상태를 확인하고, `test/monitor-gaps.md`의 개선 실행안(§2-A)을 뒷받침하는 근거를 정리합니다.

모든 항목은 다음 세 가지 기준으로 명확히 구분하여 기록합니다:
1. **실측 확인**: 호스트 상에서 직접 실행한 명령 출력(`agy --version`, `agy --help`) 또는 실제 파일(`test/.local/monitor/antigravity-sessions/*.json`)을 통해 확인된 항목
2. **공식 문서**: 공식 공급자 문서(https://antigravity.google/docs/cli/statusline/)에 명시되어 있는 사양/필드
3. **미확인**: 현재 실측 스풀에 미포함되어 있거나, 공식 문서에 명시적 필드가 존재하지 않아 실시간 확인되지 않은 항목

---

## 2. CLI 명령 실행 결과 (실측 확인)

### 2.1 `agy --version`
- **실측 결과**: `1.4.12`
- **구분**: **실측 확인**

### 2.2 `agy --help`
- **실측 결과**:
  - 기본 실행 플래그: `--model`, `--agent`, `--effort (low|medium|high|xhigh|max)`, `--mode (accept-edits, auto, plan)`, `--conversation`, `--continue`, `--output-format (text, json, stream-json)`, `--input-format`, `--settings`, `--log-file` 등
  - 서브커맨드: `agent`, `agents`, `changelog`, `help`, `install`, `mcp`, `mic-serve`, `models`, `plugin`, `plugins`, `remote-control`, `update`
  - 토큰 및 쿼터 직접 조회용 CLI 플래그(예: `--tokens`, `--usage` 등)는 제공되지 않음
- **구분**: **실측 확인**

---

## 3. statusLine 전달 JSON 필드 대조표

공식 문서(https://antigravity.google/docs/cli/statusline/)에 정의된 필드 구조와 현재 로컬 호스트 실측 데이터 간의 대조 결과입니다.

| 필드 경로 | 구분 | 내용 및 근거 |
|---|---|---|
| `session_id` | **공식 문서** | 세션 고유 식별자. 로컬 스풀에서는 개인 식별 방지를 위해 `session_hash`로 저장됨 [실측 확인] |
| `transcript_path` | **공식 문서** | 해당 세션의 대화 로그(transcript) 파일 절대 경로 |
| `model.id` | **공식 문서** | 현재 세션/턴에서 활성화된 모델 식별자 (로컬 스풀에는 `current_model`로 기록됨 [실측 확인]) |
| `context_window.total_input_tokens` | **공식 문서** | 세션 누적 총 입력 토큰 수 (로컬 스풀 `usage.input_tokens`에 145,331 확인 [실측 확인]) |
| `context_window.total_output_tokens` | **공식 문서** | 세션 누적 총 출력 토큰 수 (로컬 스풀 `usage.output_tokens`에 76,861 확인 [실측 확인]) |
| `context_window.current_usage.input_tokens` | **공식 문서** | 직전 단일 턴/응답 단위 입력 토큰 delta |
| `context_window.current_usage.output_tokens` | **공식 문서** | 직전 단일 턴/응답 단위 출력 토큰 delta |
| `context_window.current_usage.cache_read_input_tokens` | **공식 문서** | 직전 단일 턴 캐시 읽기 입력 토큰 |
| `context_window.current_usage.cache_creation_input_tokens` | **공식 문서** | 직전 단일 턴 캐시 생성(쓰기) 입력 토큰 |
| `quota` | **공식 문서** | 계정 플랜 및 구독 잔여 쿼터 객체 (로컬 스풀 `plan`: "Google AI Pro" 확인 [실측 확인]) |
| `cost.total_usd` | **공식 문서** | 세션 누적 예상 API 비용(USD) |

---

## 4. 로컬 세션 파일 실측 대조 (`test/.local/monitor/antigravity-sessions/`)

- **검증 파일**: `test/.local/monitor/antigravity-sessions/<session-hash>.json`
- **식별정보 마스킹 준수**: 계정 이메일, 개인 경로 등 식별정보 제외
- **실제 저장된 필드 구조**:
  ```json
  {
    "session_hash": "<session-hash>",
    "observed_at": "2026-10-31T04:06:39.708880+00:00",
    "current_model": "Gemini 3.8 Flash (Medium)",
    "plan": "Google AI Pro",
    "source": "Antigravity native statusline",
    "usage": {
      "input_tokens": 145331,
      "output_tokens": 76861,
      "total_tokens": 222192
    },
    "attribution": "session cumulative; historical per-model breakdown unavailable"
  }
  ```
- **실측 확인 요약**:
  - `usage`에 세션 누적 `input_tokens`, `output_tokens`, `total_tokens`가 정수형으로 정확히 기록됨.
  - 현재 저장 형태에는 모델별 토큰 분해나 캐시 토큰이 포함되지 않고 전체 누적 합산값만 보존됨 (`historical per-model breakdown unavailable`).

---

## 5. 지표 항목별 현황 (GAP 분석)

| 항목 | 구분 | 현황 및 분석 |
|---|---|---|
| **모델별 토큰 분해** | **미확인** (실측 미수집) / **공식 문서** (수집 가능) | 현재 로컬 스풀에는 모델별 누적 분해가 없음. 그러나 공식 문서상 statusLine 호출 시 `model.id`와 `context_window.current_usage`가 제공되므로, 턴 단위 delta를 기록하면 향후 모델별 집계 구현 가능 |
| **캐시 읽기/쓰기 토큰** | **미확인** (실측 미수집) / **공식 문서** (수집 가능) | 현재 스풀의 `usage`에는 캐시 필드가 null/미저장 상태. 공식 문서상 `cache_read_input_tokens`, `cache_creation_input_tokens`가 명시되어 있어 delta 수집으로 누적 집계 가능 |
| **추론(Reasoning) 토큰** | **미확인** | CLI 내 `--effort` 옵션은 존재하나, statusLine 문서 및 실제 스풀에 `reasoning_tokens` 전용 수치 필드는 명시되지 않음 |
| **비용(Cost USD)** | **미확인** (실측 미수집) / **공식 문서** (필드 존재) | 공식 문서에 `cost.total_usd` 필드가 정의되어 있으나 현재 로컬 세션 파일에는 수집·저장되지 않음 |
| **세션별 이력** | **실측 확인** | `test/.local/monitor/antigravity-sessions/` 경로에 세션 해시 단위 JSON 파일로 각각 보존되어 다중 세션 이력 관측 가능 |

---

## 6. 결론

1. **현재 상태**: Antigravity CLI는 `statusLine` 콜백을 통해 세션 누적 입력·출력·총 토큰과 플랜명, 현재 모델명을 정상 노출하고 있으며 이는 파일로 실측 확인되었습니다.
2. **개선 가능성**: 공식 문서(https://antigravity.google/docs/cli/statusline/)에 따르면 `current_usage` 내에 턴별 캐시 읽기/쓰기 토큰과 `model.id`가 포함되어 있으므로, `test/monitor-gaps.md` §2-A의 개선안(응답 단위 delta 기록 및 모델 귀속)은 공식 사양에 부합하며 구현 가능한 방안입니다.
3. **과거 이력의 한계**: 콜백 연결 이전의 과거 세션 데이터는 세션 총량 외에 모델별 세부 분해가 복원되지 않으므로, 향후 개선 시 '콜백 연결 이후 집계'로 명확히 구분하여 표시하는 것이 타당합니다.
