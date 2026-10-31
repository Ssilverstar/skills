#!/usr/bin/env python3
"""Sanitize retained usage for a specified trial window; never estimate billing."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import host_probe as probe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--since', required=True)
    p.add_argument('--codex-session', required=True)
    p.add_argument('--claude-session', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    start = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
    def within(record):
        return bool(record[2]) and datetime.fromisoformat(record[2].replace('Z', '+00:00')) >= start
    cx, _ = probe.codex_usage()
    cl, _ = probe.claude_usage()
    oc, _ = probe.opencode_usage()
    with sqlite3.connect('file:' + str(probe.HOME/'.local/share/opencode/opencode.db') + '?mode=ro', uri=True) as db:
        sessions = {r[0] for r in db.execute('SELECT id FROM session_v2 WHERE directory=? AND time_created>=?',
                    (str(probe.ROOT), int(start.timestamp() * 1000)))}
    selections = {
        'codex': [r for r in cx if args.codex_session in r[1] and within(r)],
        'claude': [r for r in cl if r[1] == args.claude_session and within(r)],
        'opencode': [r for r in oc if r[1] in sessions and within(r)]}
    end = datetime.now(timezone.utc)
    result = {'since': start.isoformat(), 'measured_at': end.isoformat(),
        'elapsed_minutes': round((end-start).total_seconds()/60, 2),
        'scope': 'Selected Codex and Claude sessions; OpenCode sessions created in this repository during the window',
        'complete': False, 'agents': {},
        'limitations': ['Ongoing responses may not yet be logged.', 'Antigravity samples are cumulative observed sessions, not a precise trial-window delta.',
                       'Token totals include cache; they are not billed subscription usage or API dollar cost.',
                       'No equivalent single-agent baseline was executed.']}
    for name, records in selections.items():
        models, usage, _ = probe.aggregate(records)
        usage['window'] = '선택한 시험 세션과 시간 구간 · 계정 청구량 아님'
        result['agents'][name] = {'models': models, 'usage': usage, 'record_count': len(records)}
    ag = [r for r in probe.antigravity_statusline_usage() if within(r)]
    if ag:
        models, usage, latest = probe.aggregate(ag)
        usage.update(cached_input_tokens=None, cache_write_input_tokens=None)
        for model in models:
            model.update(cached_input_tokens=None, cache_write_input_tokens=None)
        usage['window'] = '시험 중 관측된 세션 누적 · 시작 이전 사용량을 차감할 수 없음'
        result['agents']['antigravity'] = {'usage': usage, 'models': models,
            'observed_at': latest, 'record_count': len(ag), 'exact_window': False}
    else:
        result['agents']['antigravity'] = {'usage': None, 'reason': 'No native statusline sample observed'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'elapsed_minutes': result['elapsed_minutes'], 'records': {k:len(v) for k,v in selections.items()}}))


if __name__ == '__main__':
    main()
