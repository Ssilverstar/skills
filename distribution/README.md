# 배포

이 디렉터리는 대상별 배포 규칙과 스킬 활성화 프로필을 관리합니다. 감사한 로컬 머신용 배포기는 구현했으며, 새 머신에서 패키지를 자동 다운로드하는 범용 설치기는 아닙니다. [공통 정책](skill-policy.md)과 [전체 사용 목록](skill-list.md)을 먼저 읽습니다.

## 원본과 배포 대상

| 대상 | 이 저장소의 진입점 | 전용 지침 | 공유 원본 |
| --- | --- | --- | --- |
| Codex | `AGENTS.md` | `instructions/agents/codex.md` | `instructions/common.md`, `skills/`, `herdr/` |
| Opus / Claude 환경 | `CLAUDE.md` | `instructions/agents/opus.md` | 동일 |
| Gemini | `GEMINI.md` | `instructions/agents/gemini.md` | 동일 |
| OpenCode | `AGENTS.md` | `instructions/agents/opencode.md` | 동일 |

위 진입점은 이 저장소의 구성 규칙입니다. 실제 배포 시에는 각 실행 도구가 지원하는 파일명, 설치 위치, 참조 방식과 스킬 형식을 확인해야 합니다.

## 배포 구현 시 정할 항목

- 사용자 전역 설치와 프로젝트별 설치의 구분
- 대상별 설치 경로와 지원 버전
- 복사, 링크, 문서 병합 등 배포 방식
- 기존 사용자 파일 보존과 충돌 처리
- 적용 전 변경 미리보기, 업데이트, 제거 및 복구 방법
- 배포 후 지침과 스킬이 실제로 로딩되는지 확인하는 방법

배포 산출물은 원본에서 생성하며 직접 수정하지 않는 것을 원칙으로 합니다. 문서를 병합하지 않는 배포 방식에서는 진입점이 참조하는 문서와 스킬의 보조 파일도 함께 배포해야 합니다.

## 공통 프로필과 MCP (현재)

- 선택 원본: [36개 스킬](profiles/common-general-sw.json), [3개 MCP](profiles/common-mcp.json).
- `python3 distribution/common_profile.py`: 소스 SHA-256·기존 파일 충돌을 검사하고 미리보기. `--apply`로 네 대상에 배포합니다. 설치된 패키지가 필요하며 원본 캐시는 변경하지 않습니다.
- `python3 distribution/mcp_profile.py`: 동일 실행 명령의 호스트별 설정을 미리보기. `--apply`로 관련 서버만 병합합니다. 인증정보를 새 설정에 복제하지 않습니다. GitHub 공식 서버 v2.0.3은 고정된 컨테이너 digest를 사용하고 실행 시 기존 `gh` 인증을 읽습니다.
- `python3 test/monitor/install_native_otel.py --apply`: 확인된 Codex·Claude의 **지표만** 로컬 수집기에 전송. 설정 백업 후 적용하며 새 프로세스에서 확인합니다.
- `python3 test/monitor/check_common_mcp.py`: 실제 4×3 MCP 연결·목록·읽기 호출을 검사하고 비식별 결과를 저장합니다. 모델 도구 권한을 자동 승인하지 않습니다.
- `python3 distribution/render_skill_list.py --check`: 선택 목록과 문서 일치 검사.

Claude의 원본 `ecc@ecc`는 비활성, `ecc-common@skills-dir`는 활성입니다. 원본 이름은 비활성 상태에서도 예약되므로 로컬 플러그인의 이름을 달리합니다. 선택한 13개 SKILL.md와 기존 훅·스크립트·보조 파일을 유지하고, legacy commands와 비선택 스킬의 발견 진입점만 배포본에서 제외합니다. 비선택 continuous-learning의 훅 보조 파일은 보존합니다. 원본 Ponytail 훅은 그대로입니다. 브라우저 MCP는 공통 설정에서 제공해 ECC 복제본의 중복 서버를 제거합니다. 업데이트는 원본 버전 검토→공통 해시 갱신→배포본 재생성→새 로더 검증 순서입니다.

`~/.local/share/agent-skills/{common,mcp,otel}-backup-<UTC>/receipt.json`에 변경 경로·원본 백업·적용 후 해시를 기록합니다. 설정 파일에 토큰이 있을 수 있으므로 백업 디렉터리는 0700, 설정 사본은 0600입니다. 복구할 때는 **현재 해시가 receipt의 적용 후 해시와 같은지 먼저 확인**하고 그 파일만 복원합니다. 후속 수정이 있으면 덮어쓰지 말고 병합합니다. 생성 링크는 receipt의 대상과 같은 링크만 제거하며, 공급업체 캐시나 기존 사용자 스킬은 삭제하지 않습니다. 연속 적용의 복구는 최신 receipt부터 역순입니다. 현재 배포기는 자동 롤백을 제공하지 않습니다.

Ubuntu의 Chromium user namespace 제한은 [설치기](install_browser_sandbox.py)가 검증한 Chromium 실행 파일의 **정확한 경로 하나**에 AppArmor 프로필을 설치해 해결합니다(별도 관리자 권한 필요). 호스트 전역 제한과 Chromium sandbox를 끄지 않습니다. 브라우저 버전/경로 변경 시 재검토합니다. 제거 시 `/etc/apparmor.d/agent-observatory-chromium` 프로필을 unload한 후 해당 파일만 제거합니다. [Chromium 공식 설명](https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md).

## 이전 단계: Codex 범용 SW 개발 프로필

[codex-general-sw.json](profiles/codex-general-sw.json)은 Codex 0.166.0의 로컬 활성화 목록입니다. 초기 Opus 합의 시점은 **설치 364개 중 35개 활성·329개 비활성**이었습니다. 현재 파일은 후속 공통 프로필에 맞춰 **36개 활성·359개 비활성(등록 395개)**으로 갱신했습니다. Ponytail 6개·archify를 보존하고 graft를 추가했으며, Claude 하네스에 종속된 `ecc:skill-stocktake`를 Codex 기본 목록에서 제외했습니다. 본문 미검토 항목은 `needs-review`로 구분합니다. [이전 이력](../docs/skill-audit-2026-10-31.md)은 최종 상태와 구분합니다.

저장소 루트에서 미리보기:

```bash
python3 distribution/codex_profile.py
```

적용:

```bash
python3 distribution/codex_profile.py --apply
```

Python 3.11 이상이 필요합니다. `CODEX_HOME`이 설정되어 있으면 해당 경로, 없으면 `~/.codex/config.toml`을 사용합니다. 설정 파일이 이미 있어야 합니다. 비활성 이름은 `[[skills.config]]`에 기록하고 기존 모델·권한·플러그인 설정은 보존합니다. 스킬 파일과 플러그인 캐시는 수정하지 않습니다. 기존 개별 스킬 설정과 충돌하면 변경 없이 중단합니다. 새 이름의 스킬은 자동 비활성화하지 않습니다.

원래 설정은 Codex 홈의 `backups/skills-general-sw-<UTC 시각>/`에 권한을 제한해 백업합니다. 출력된 백업 경로로 복구합니다.

```bash
python3 distribution/codex_profile.py --restore /absolute/path/to/backup-directory
```

복구는 적용 이후 설정 파일이 바뀌지 않았을 때만 수행합니다. 나중에 변경된 설정이 있으면 수동으로 병합해야 하므로 덮어쓰지 않습니다. 전체 복구 대신 한 스킬만 다시 켜려면 Codex의 스킬 관리 UI를 사용하거나 해당 이름의 `enabled` 값을 `true`로 변경합니다. 프로필을 다시 적용하면 검토된 비활성 목록이 재적용됩니다.

다른 머신에 적용하기 전에는 그 머신의 스킬 목록과 비교합니다. 프로필의 `enabled`는 유지 대상 목록이며 설치나 강제 활성화를 수행하지 않습니다. 적용 후 로컬 목록의 활성 개수·파싱 오류를 확인하고 새 App 세션에서도 필요한 스킬이 보이는지 점검합니다.

## 이전 단계: OpenCode 프로필

[opencode-general-sw.json](profiles/opencode-general-sw.json)은 OpenCode 2.2.5의 `permissions` 규칙 11개입니다. 이 머신에는 기존 `~/.config/opencode/opencode.json(c)`가 없어 JSON 파일로 설치했습니다. **다른 머신의 기존 설정 위에 복사하지 말고** `permissions`만 병합하고 순서와 에이전트별 우선순위를 검토합니다.

```bash
opencode api get /api/config
opencode debug agents
opencode api get /api/skill
```

실제 설정과 `build` 에이전트 권한에서 11개 규칙을 확인했습니다. `/api/skill`은 차단 항목도 포함한 등록 목록입니다. 서비스 시작 직후에는 빈 목록이 올 수 있으므로 초기화 후 다시 확인합니다. `--standalone`으로 즉시 종료하는 한 번의 조회만으로 미설치라고 판단하지 않습니다. 이번 설치 이전에는 설정 파일이 없었으므로, 복구는 설치 기록의 해시와 현재 파일이 일치할 때 그 파일만 제거하는 방식입니다. 이후 수정된 파일은 수동 병합합니다.

## 이전 단계: 필수 스킬 보완 설치

[스킬 등록부](../skills/README.md)의 이미 설치된 버전을 사용했습니다. 공급업체 원본이나 캐시는 수정하지 않았습니다.

- `graft`: `@nanonets/graft` 0.21.1의 `dist/claude/skill-template.js`에서 `skillTemplate()`의 출력을 그대로 추출해 `~/.local/share/agent-skills/graft-0.21.1/SKILL.md`로 저장했습니다. 네 전역 스킬 경로에서 이 디렉터리로 링크합니다.
- `archify`: 기존 Codex/Claude 3.0.1 패키지 보존. Gemini/OpenCode는 Codex의 **전체 패키지 디렉터리**에 링크하여 보조 파일도 사용합니다.
- Ponytail 6개: Codex/Claude 플러그인 보존. Gemini/OpenCode는 기존 Claude 플러그인 4.10.3의 각 스킬 디렉터리에 링크합니다. Codex import 1.0.0과 여섯 `SKILL.md` 바이트가 동일함을 확인했습니다.
- [공통 지침](../instructions/common.md)의 `skill-runtime` 구간을 Codex `~/.codex/AGENTS.md`, Claude `~/.claude/CLAUDE.md`, Gemini `~/.gemini/GEMINI.md`, OpenCode `~/.config/opencode/AGENTS.md`에 배포했습니다. 기존 네 파일은 없었으며 다른 지침을 덮어쓰지 않았습니다.

`graft`의 공식 설치기는 Codex/OpenCode/Gemini에 지침 파일을 쓰는 방식도 제공합니다. 이번 **스킬로 배포하는 방식은 사용자 요청에 따른 선택**이며 upstream의 각 호스트 기본 설치와 같다고 주장하지 않습니다. Gemini CLI와 Antigravity 호스트를 혼동하지 않습니다. `graft init`은 실행하지 않았습니다.

재현할 때는 설치된 패키지의 실제 위치와 버전을 확인한 후 아래처럼 템플릿 함수를 호출합니다. 출력 목적지는 기존 파일이 없는 곳을 선택합니다.

```bash
node --input-type=module -e 'const {skillTemplate}=await import(process.argv[1]);process.stdout.write(skillTemplate());' file:///absolute/package/path/dist/claude/skill-template.js
```

이번 원본 SHA-256: `bc338fab9fd85c2531f8e06a7f72d835b67428f29b4a5afe8b26f2814e877cf4`.

설치 내역은 `~/.local/share/agent-skills/install-20261031T015400Z.json`, OpenCode 설정 기록은 같은 디렉터리의 `opencode-profile-install.json`에 있습니다. 원본 파일·생성 링크·지침 해시를 기록하며 개인 경로가 들어 있는 실행 기록은 커밋하지 않습니다. 되돌릴 때 기록과 일치하는 생성 링크/파일만 제거하고 기존 Codex/Claude 스킬과 플러그인은 보존합니다. 패키지 제거/업데이트로 링크가 끊기면 새 버전 검토 후 링크와 등록부를 함께 갱신합니다.

```bash
gemini skills list --all
python3 distribution/render_skill_list.py --check
```

새 설치는 다음 턴 또는 새 세션에서 확인합니다. 목록 발견 성공은 모든 스킬 워크플로 실행을 검증했다는 의미가 아닙니다. 상태와 검증 한계는 [최종 기록](../docs/skill-set-agreement-2026-10-31.md)에 남깁니다.
