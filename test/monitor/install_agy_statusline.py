#!/usr/bin/env python3
"""Install a scoped metrics statusline while preserving the default Antigravity UI."""
import argparse
import json
from pathlib import Path
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    settings = Path.home()/'.gemini/antigravity-cli/settings.json'
    original = settings.read_text()
    data = json.loads(original)
    script = Path(__file__).with_name('agy_statusline.py').resolve()
    command = shlex.join([sys.executable, str(script)])
    existing = data.get('statusLine')
    if existing and existing.get('command') != command:
        raise SystemExit('Existing user statusline preserved; explicit composition is required.')
    data['statusLine'] = {'type': 'command', 'command': command, 'enabled': True, 'stack_with_default': True}
    if not args.apply:
        print(json.dumps({'change': 'statusLine only', 'statusLine': data['statusLine']}, indent=2))
        return
    backup = settings.with_name('settings.json.before-observatory')
    if not backup.exists():
        backup.write_text(original); backup.chmod(0o600)
    temp = settings.with_suffix('.observatory.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n'); temp.chmod(0o600)
    temp.replace(settings)
    print('Installed statusLine; model, trusted workspaces and other settings preserved.')
    print('Backup:', backup)


if __name__ == '__main__':
    main()
