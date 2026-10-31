# 시험 준비 및 환경 점검

[최종 보고](final-report.md): 변경 전후·커스텀 Herdr 스킬·공통 스킬/MCP·시험 결과·패널/Git 마무리. 초기 결과 파일의 시각과 최신 검증을 구분합니다.

이 디렉터리에서 사내 제안과 집 환경의 차이, 에이전트별 계정·모델·스킬·MCP 사전 점검을 관리합니다. 기존 `tests/`는 저장소 프로필 적용기의 자동 검증 코드입니다.

환경 비교·최소 동작 점검과 모니터링 앱 구현 시험을 완료했습니다. 통제된 성능·비용 절감 벤치마크는 실행하지 않았습니다. 사내 예산은 사용자 제안서의 전제이고 회사 시스템에서 검증한 값은 아닙니다. 인증정보, 계정 식별자, 원문 세션 로그는 기록하지 않습니다.

모니터링 웹앱은 실제 Herdr 위임으로 구현해 독립 실행 중입니다. 통제된 단독 모델 비교 벤치마크와는 구분합니다.

- [Agent Observatory 실행 안내](monitor/README.md)
- [구현 계약과 역할](monitor-brief.md)
- [Herdr 운영 비교 기록](monitor-study.md)
- [최종 검사 결과](results/final-verification.json) · [초기 검사 결과](results/monitor-checks.json) · [배포 상태](results/monitor-deployment.json) · [최신 브라우저 검사](results/monitor-v2-e2e.json)
- [Opus 스킬 검토 의견](herdr-orchestrate-review-claude.md)
- [Claude의 미구현·개선 실행안](monitor-gaps.md) · [LAN 접속 검증](results/monitor-lan-access.json)

- [전체 에이전트 상태와 패널 정리 결과](agent-status.md)
- `smoke.txt`: 공개 표식 읽기와 간단한 산술 응답 점검용 입력
- [사내/집 환경 비교](environment-comparison.md)
- [Claude 사전 점검](claude-preflight.md)
- [Antigravity 전환 기록](antigravity-migration.md)
- [Antigravity 실제 응답 점검 결과](results/antigravity.json)
- [Codex API 점검 결과](results/codex.json)

## 검증 환경

웹 컨테이너 의존성은 `monitor/requirements.txt`, 호스트 검증 도구는 `requirements-checks.txt`에 고정합니다. 기존 Playwright Chromium을 사용합니다. MCP 점검은 설치된 Git·GitHub·Chrome DevTools 서버와 Docker/gh 인증이 필요합니다. 의존성 설치가 곧 공급자 로그인이나 도구 사용 승인을 뜻하지 않습니다.
