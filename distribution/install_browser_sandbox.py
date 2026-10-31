#!/usr/bin/env python3
"""Install a narrowly scoped AppArmor userns profile for the audited Chromium binary.

Does not disable Chromium's sandbox or the host-wide userns restriction.
The exact path must be reviewed again after a browser version update.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    choices=sorted((Path.home()/'.cache/ms-playwright').glob('chromium-*/chrome-linux*/chrome'))
    if not choices:raise SystemExit('No installed Chromium')
    browser=choices[-1].resolve()
    if any(c in str(browser) for c in '*?[]{}"\n'):raise SystemExit('Unsupported profile path')
    target=Path('/etc/apparmor.d/agent-observatory-chromium')
    content='''# Managed by distribution/install_browser_sandbox.py
abi <abi/4.0>,
include <tunables/global>
profile agent-observatory-chromium "'''+str(browser)+'''" flags=(unconfined) {
  userns,
}
'''
    print(content)
    if not a.apply:return
    if target.exists() and target.read_text()!=content:
        raise SystemExit('Existing profile differs; review before replacing')
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(content);f.flush()
        subprocess.run(['sudo','-n','install','-o','root','-g','root','-m','0644',f.name,str(target)],check=True)
    subprocess.run(['sudo','-n','apparmor_parser','-r',str(target)],check=True)
    print('Installed exact-path profile:',target)


if __name__=='__main__':main()
