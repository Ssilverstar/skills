#!/usr/bin/env python3
"""Capture only native Claude quota fields, then preserve the user's statusline."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys

OUTPUT = Path(__file__).resolve().parents[1]/'.local/monitor/claude-plan.json'


def sanitize(data):
    limits = []
    for key, value in (data.get('rate_limits') or {}).items():
        if key not in ('five_hour', 'seven_day', 'spend_limit') or not isinstance(value, dict):
            continue
        used = value.get('used_percentage')
        reset = value.get('resets_at')
        if isinstance(used, bool) or not isinstance(used, (int, float)) or not math.isfinite(used):
            continue
        try:
            reset_at = datetime.fromtimestamp(reset, timezone.utc).isoformat() if reset is not None else None
        except (ValueError, TypeError, OverflowError):
            reset_at = None
        limits.append({'label': key, 'used_percent': used, 'reset_at': reset_at})
    if not limits:
        return None
    return {'source': 'Claude native statusline rate_limits',
            'observed_at': datetime.now(timezone.utc).isoformat(), 'limits': limits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-command-file', type=Path, required=True)
    args = parser.parse_args()
    raw = sys.stdin.read()
    try:
        row = sanitize(json.loads(raw))
        if row:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            temp = OUTPUT.with_suffix('.'+str(os.getpid())+'.tmp')
            temp.write_text(json.dumps(row, ensure_ascii=False, allow_nan=False)); temp.replace(OUTPUT)
    except (ValueError, OSError, TypeError):
        pass
    original = json.loads(args.original_command_file.read_text())['command']
    # Only the original locally configured command is run. Input is not interpolated.
    result = subprocess.run(['/bin/sh', '-c', original], input=raw, text=True, check=False)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
