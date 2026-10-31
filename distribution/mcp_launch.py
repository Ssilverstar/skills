#!/usr/bin/env python3
"""Common stdio MCP launcher. Never writes credentials to files or stdout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def command(name):
    profile = json.loads((ROOT/'profiles/common-mcp.json').read_text())['servers']
    if name not in profile:
        raise ValueError('Unknown common MCP server')
    if name == 'git':
        return ['uvx', '--from', profile[name]['package'], 'mcp-server-git']
    if name == 'github':
        return ['docker', 'run', '--rm', '-i', '-e', 'GITHUB_PERSONAL_ACCESS_TOKEN', profile[name]['image']]
    browsers = sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))
    if not browsers:
        raise RuntimeError('Install Playwright Chromium before starting chrome-devtools')
    return ['npx', '--yes', profile[name]['package'], '--headless', '--isolated',
            '--executablePath='+str(browsers[-1]), '--no-usage-statistics', '--no-performance-crux']


def main():
    name = sys.argv[1]
    env = dict(os.environ)
    # The audited workstation installs uvx/npx through this user-owned toolchain.
    env['PATH'] = os.pathsep.join([str(Path.home()/'miniconda3/bin'), str(Path.home()/'.local/bin'), env.get('PATH','')])
    argv = command(name)
    if name == 'github':
        proc = subprocess.run(['gh', 'auth', 'token'], env=env, capture_output=True, text=True, timeout=15)
        if proc.returncode or not proc.stdout.strip():
            raise RuntimeError('Existing gh authentication is unavailable; run gh auth login')
        env['GITHUB_PERSONAL_ACCESS_TOKEN'] = proc.stdout.strip()
    executable = shutil.which(argv[0], path=env['PATH'])
    if not executable:
        raise RuntimeError('Missing executable: ' + argv[0])
    os.execve(executable, argv, env)


if __name__ == '__main__':
    main()
