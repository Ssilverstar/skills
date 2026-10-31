# 저장소 작업 지침

이 저장소는 여러 에이전트에 배포할 지침, 스킬, herdr 사용 가이드의 원본을 관리합니다.

## 먼저 읽을 문서

- 모든 대상: `instructions/common.md`
- Codex: `instructions/agents/codex.md`
- OpenCode: `instructions/agents/opencode.md`
- 그 외 대상: `instructions/agents/`의 해당 파일
- herdr를 사용할 때: `herdr/README.md` 및 관련 워크플로

현재 실행 대상에 해당하는 문서를 직접 읽습니다. 다른 대상의 전용 지침을 일괄 적용하지 않습니다.

## 이 저장소를 수정할 때

- 공통 규칙은 `instructions/common.md`에서 관리하고 대상별 문서에 복제하지 않습니다.
- 대상별 차이는 `instructions/agents/`에 기록합니다.
- 실제 스킬은 `skills/<skill-name>/SKILL.md`에 작성합니다.
- herdr의 확인되지 않은 명령, 옵션, 설치 경로를 지어내지 않습니다.
- 구조를 변경하면 `README.md`와 문서 링크를 함께 갱신합니다.
- 작성 절차는 `docs/authoring.md`, 배포 관련 내용은 `distribution/README.md`를 따릅니다.
