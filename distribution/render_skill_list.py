#!/usr/bin/env python3
"""Render the reviewed inventory from the Codex profile; --check detects stale docs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = {
    'required': ('필수 — 네 에이전트 모두 보존/설치', '사용자가 지정한 8개. 강한 트리거도 사용자 필수 예외로 보존.'),
    'core-partially-reviewed': ('기본 유지 — 공통 선택 목록', '도구 전제조건과 호스트별 별칭은 공통 프로필에 기록. 전체 워크플로 호환성 인증은 아님.'),
    'on-demand': ('프로젝트별 사용', '해당 스택 작업에서 선택. 현재 Codex 전역에서는 비활성.'),
    'excluded-compat-codex': ('Codex 호환성 제외', 'Claude 전용 하네스/명령 또는 도구 전제. 다른 에이전트는 자체 호환성을 판단.'),
    'excluded-overlap-or-trigger': ('중복/강제 트리거 제외', '대표 기능과 중복하거나 작업 범위를 강제하는 흐름. 사용자 요청 시 재검토.'),
    'needs-review': ('검토 보류 — 현재 Codex 전역 비활성', '불필요 판정이 아님. 최초 일괄 제외 상태를 승계했으며 본문·사용 필요를 확인한 후 복구 가능.'),
}


def render(profile):
    names = profile['enabled'] + profile['disabled']
    classes = profile['classification']
    assert len(names) == len(set(names)) and set(classes) == set(names)
    assert set(classes.values()) <= set(GROUPS)
    assert set(profile['user_required']) == {n for n, c in classes.items() if c == 'required'}
    assert set(profile['user_required']) <= set(profile['enabled'])
    rows = ['# 합의된 스킬 사용 목록', '',
            '원본: [codex-general-sw.json](profiles/codex-general-sw.json). 이 문서는 `python3 distribution/render_skill_list.py`로 생성합니다. 직접 편집하지 않습니다.', '',
            '2026-10-31 · Codex + Opus 5.5 high 합의. [공통 기준·에이전트별 예외](skill-policy.md)를 함께 적용합니다.', '',
            f"Codex 프로필 검토 목록 {len(names)}개(로컬·앱 항목 포함): 활성 {len(profile['enabled'])}개, 비활성 {len(profile['disabled'])}개. 개수는 목표가 아니라 이 환경의 결과입니다.", '',
            '전체 기본 선택 36개는 네 에이전트 공통입니다. Claude ECC 전체 노출 예외는 폐기했습니다. 플랫폼 내장·앱 동기화 항목은 별도이며 실제 도구 전제조건을 충족해야 실행할 수 있습니다.', '']
    common = json.loads((ROOT / 'profiles/common-general-sw.json').read_text())
    assert {r['id'] for r in common['skills']} == set(profile['enabled'])
    rows += ['## 공통 목록과 실제 이름', '',
             '원본: [common-general-sw.json](profiles/common-general-sw.json). Claude의 ECC 13개는 `ecc-common` 로컬 플러그인으로 배포하며 원본 훅·보조 파일을 보존합니다.', '',
             '| 공통 ID | Claude | OpenCode / Antigravity | 실행 전제 |', '| --- | --- | --- | --- |']
    native = {'docx':'anthropic-skills:docx', 'pdf':'anthropic-skills:pdf', 'skill-creator':'skill-creator:skill-creator',
              'humanize-korean':'humanize-korean:humanize-korean', 'prefer-gh-for-github':'prefer-gh-for-github:prefer-gh-for-github'}
    for row in common['skills']:
        name = row['id']
        alias = 'ecc-common:' + row['directory'] if name.startswith('ecc:') else (name if name.startswith('ponytail:') else native.get(name,row['directory']))
        rows.append(f"| `{name}` | `{alias}` | `{row['directory']}` | {row['prerequisites']} |")
    rows.append('')
    for key, (title, why) in GROUPS.items():
        selected = sorted(n for n, c in classes.items() if c == key)
        rows += [f'## {title} ({len(selected)}개)', '', why, '']
        rows += [f'- `{name}`' for name in selected]
        rows.append('')
    return '\n'.join(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = render(json.loads((ROOT / 'profiles/codex-general-sw.json').read_text()))
    target = ROOT / 'skill-list.md'
    if args.check:
        if not target.exists() or target.read_text() != result:
            raise SystemExit('skill-list.md is stale; run distribution/render_skill_list.py')
        print('skill-list.md matches the profile')
    else:
        target.write_text(result)
        print(target)
