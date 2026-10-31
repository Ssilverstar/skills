# Gemini CLI → Antigravity CLI 전환

2026-10-31 사용자 요청에 따른 집 시험 환경 변경입니다.

- Gemini CLI `@google/gemini-cli` 0.66.0 패키지 제거 완료. `gemini` 실행 파일과 npm 패키지가 남아 있지 않음을 확인했습니다.
- 기존 개인 설정·스킬·전역 `GEMINI.md`는 보존했습니다.
- Google 공식 설치기로 Antigravity CLI **1.4.12 / Linux ARM64** 설치. 다운로드 SHA-512 검증 통과.
- 실행 파일: `~/.local/bin/agy`. 터미널에서 `agy`로 실행하며 `--print`, `--mode plan`, `--model`, `models`, `mcp` 등의 명령을 제공합니다.
- 공식 설치기가 `~/.bashrc`, `~/.profile`에 실행 경로를 추가했습니다.
- 필수 8개와 Herdr, 총 9개를 `~/.gemini/antigravity-cli/skills/`에 링크했습니다. 원본은 수정하지 않았습니다.
- [이전 스크립트](scripts/migrate_google_skills.py)는 기본 미리보기이며 `--apply`로 링크합니다. [실행 결과](results/antigravity-skill-migration.json)를 남겼습니다.
- 새 Herdr 패널 `w3:p8`에서 `agy --mode plan`을 실행했습니다. 로그인 후 재확인 시 초기 설정은 완료됐고 **Google AI Pro**가 표시됐습니다. 데이터 수집 옵션의 최종 선택값은 확인하지 않았습니다.
- `agy models`에서 Gemini 3.8 Flash low/medium/high를 확인했습니다. 기본 Gemini 4 Argon에서 `/model`로 **Gemini 3.8 Flash (Medium)**을 선택하고 실제 파일 읽기·산술 응답·필수 8개 스킬 인식을 확인했습니다. `ponytail-help`는 ReadFile로 원문을 읽었으며 별도 Skill 도구 호출은 아닙니다.
- 비대화형 첫 시험은 파일 읽기 권한 자동 거절로 미완료였습니다. 대화형 시험에서 스킬 원문 파일 하나에 대한 읽기만 허용한 후 성공했습니다. 전체 권한 우회 옵션은 사용하지 않았습니다. [비식별 결과](results/antigravity.json).
- `agy mcp list`는 미설정이며 연결 실패가 아닙니다. 구독 잔여 한도는 확인하지 않았습니다.
- 점검 후 사용자 요청대로 Claude·OpenCode·Antigravity 패널을 닫고, 현재 작업 공간에 Codex 패널 하나만 남았음을 확인했습니다. [전체 상태](agent-status.md).
- 기존 Gemini 인증 대기 프로세스를 종료했습니다. 다른 작업 공간의 에이전트는 건드리지 않았습니다.

## 공식 근거

- [Google Antigravity CLI 설치](https://antigravity.google/docs/getting-started?tab=cli)
- [Gemini CLI 마이그레이션: 스킬 경로·전역 지침·MCP 형식](https://antigravity.google/docs/cli/gcli-migration/)

Gemini CLI는 Google OAuth 인증 이후 개인용 Code Assist에서 더 이상 지원되지 않는 클라이언트라는 서버 응답으로 모델 실행이 차단됐습니다. 이 오류를 Antigravity가 설치되지 않았다는 뜻이나 모델 자체 장애로 해석하지 않습니다.
