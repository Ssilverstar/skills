#!/usr/bin/env python3
"""Preview or install this repository's user-scoped host probe service."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UNIT = 'agent-observatory-probe.service'
MARKER = '# Managed by skills/test/monitor/install_host_service.py\n'


def quote(text):
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    target = Path.home()/'.config/systemd/user'/UNIT
    binary_dirs = [str(Path(sys.executable).parent)]
    for name in ('codex', 'opencode', 'agy'):
        binary = shutil.which(name)
        if binary:
            binary_dirs.append(str(Path(binary).parent))
    binary_dirs += ['/usr/local/cuda/bin', '/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin']
    service_path = ':'.join(dict.fromkeys(binary_dirs))
    working_dir = str(ROOT).replace('%', '%%').replace(' ', '\\x20')
    content = MARKER + f'''[Unit]
Description=Agent Observatory sanitized host metrics probe
After=default.target

[Service]
Type=simple
WorkingDirectory={working_dir}
Environment={quote('PATH=' + service_path)}
ExecStart={quote(sys.executable)} {quote(HERE/'host_probe.py')} --interval 15
Restart=on-failure
RestartSec=5
UMask=0022

[Install]
WantedBy=default.target
'''
    if target.exists() and not target.read_text().startswith(MARKER):
        raise SystemExit('Refusing to replace a service not owned by this installer.')
    if not args.apply:
        print(content)
        print('Preview only. Use --apply to install and start:', target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text() != content:
        backup = target.with_suffix('.service.previous')
        if backup.exists():
            raise SystemExit('Previous backup exists; inspect it before changing the service.')
        backup.write_text(target.read_text())
    target.write_text(content)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', '--user', 'enable', '--now', UNIT], check=True)
    subprocess.run(['systemctl', '--user', 'restart', UNIT], check=True)
    subprocess.run(['systemctl', '--user', 'is-active', UNIT], check=True)
    print('Installed', target)


if __name__ == '__main__':
    main()
