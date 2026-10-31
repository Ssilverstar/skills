#!/usr/bin/env python3
"""Native Antigravity statusline → sanitized cumulative session totals.

No email, title, cwd, transcript, prompt, credentials, or raw payload is stored.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

OUTPUT = Path(__file__).resolve().parents[1]/'.local/monitor/antigravity-sessions'


def sanitize(data):
    session = data.get('conversation_id') or data.get('session_id')
    context = data.get('context_window') or {}
    inp, out = context.get('total_input_tokens'), context.get('total_output_tokens')
    if not session or not all(isinstance(n, (int, float)) and not isinstance(n, bool)
                              and math.isfinite(n) and n >= 0 for n in (inp, out)):
        return None
    model = data.get('model') or {}
    return {'session_hash': hashlib.sha256(str(session).encode()).hexdigest()[:24],
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'current_model': model.get('display_name') or model.get('id'),
        'plan': data.get('plan_tier'), 'source': 'Antigravity native statusline',
        'usage': {'input_tokens': inp, 'output_tokens': out, 'total_tokens': inp+out},
        'attribution': 'session cumulative; historical per-model breakdown unavailable'}


def main():
    try:
        row = sanitize(json.load(sys.stdin))
        if row:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            dest = OUTPUT/(row['session_hash']+'.json')
            temp = dest.with_suffix('.'+str(os.getpid())+'.tmp')
            temp.write_text(json.dumps(row, ensure_ascii=False, allow_nan=False))
            temp.replace(dest)
            print('Observatory · 세션 토큰 ' + format(row['usage']['total_tokens'], ','))
    except (ValueError, OSError, TypeError):
        # Statusline must not interrupt the coding agent on malformed startup state.
        print('Observatory · 수집 대기')


if __name__ == '__main__':
    main()
