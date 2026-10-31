#!/usr/bin/env python3
"""Preview/install the quota observer without replacing the user's statusline UI."""
import argparse
import json
from pathlib import Path
import shlex
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    settings = Path.home()/'.claude/settings.json'
    original = settings.read_text(); data = json.loads(original)
    previous = data.get('statusLine')
    if not isinstance(previous, dict) or not previous.get('command'):
        raise SystemExit('No existing command statusline; configure explicitly before wrapping.')
    here = Path(__file__).resolve().parent
    original_file = here.parent/'.local/monitor-adapters/claude-original-command.json'
    command = shlex.join([sys.executable, str(here/'claude_statusline.py'), '--original-command-file', str(original_file)])
    if previous['command'] == command:
        print('Observer already configured.'); return
    if original_file.exists():
        raise SystemExit('Stored original exists but current command differs; inspect before changing.')
    if not args.apply:
        print(json.dumps({'change':'Wrap existing statusLine command; preserve original output', 'command':command}, indent=2)); return
    backup = settings.with_name('settings.json.before-observatory')
    if backup.exists():
        raise SystemExit('Backup already exists; inspect before changing.')
    backup.write_text(original); backup.chmod(0o600)
    original_file.parent.mkdir(parents=True, exist_ok=True)
    original_file.write_text(json.dumps({'command':previous['command']})); original_file.chmod(0o600)
    data['statusLine'] = {**previous, 'command':command}
    temp = settings.with_suffix('.observatory.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n'); temp.chmod(0o600); temp.replace(settings)
    print('Installed quota observer, preserved existing statusline output and settings. Backup:', backup)


if __name__ == '__main__':
    main()
