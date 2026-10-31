#!/usr/bin/env python3
"""Preview/apply the same local MCP launchers to four agents; preserve unrelated settings."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
NAMES = list(json.loads((ROOT/'profiles/common-mcp.json').read_text())['servers'])


def common_commands():
    return {n:[sys.executable, str(ROOT/'mcp_launch.py'), n] for n in NAMES}


def render_codex(text, commands):
    # Remove only the three replaced MCP tables and their nested env tables.
    chunks = re.split(r'(?m)(?=^\[)', text)
    kept=[]
    for chunk in chunks:
        header=chunk.splitlines()[0] if chunk else ''
        if any(re.match(r'^\[mcp_servers\.(?:'+re.escape(n)+'|"'+re.escape(n)+r'")(?:\.|\])',header) for n in NAMES):
            continue
        kept.append(chunk)
    updated=''.join(kept).rstrip()+'\n\n'
    for name, argv in commands.items():
        updated += '[mcp_servers.'+json.dumps(name)+']\ncommand = '+json.dumps(argv[0])+'\nargs = '+json.dumps(argv[1:])+'\n\n'
    before, after=tomllib.loads(text),tomllib.loads(updated)
    assert {k:v for k,v in before.items() if k!='mcp_servers'} == {k:v for k,v in after.items() if k!='mcp_servers'}
    for name,value in before.get('mcp_servers',{}).items():
        if name not in NAMES: assert after['mcp_servers'][name]==value
    return updated


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    commands=common_commands();updates={}
    cp=HOME/'.codex/config.toml';updates[cp]=render_codex(cp.read_text(),commands)
    for agent,path in [('claude',HOME/'.claude.json'),('opencode',HOME/'.config/opencode/opencode.json'),
                       ('antigravity',HOME/'.gemini/config/mcp_config.json')]:
        raw=path.read_text() if path.exists() else ''
        data=json.loads(raw) if raw.strip() else {}
        servers=data.setdefault('mcp',{}).setdefault('servers',{}) if agent=='opencode' else data.setdefault('mcpServers',{})
        for name,argv in commands.items():
            servers[name]={'type':'local','command':argv} if agent=='opencode' else {'command':argv[0],'args':argv[1:]}
            if agent=='claude':servers[name]['type']='stdio'
        updates[path]=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    print(json.dumps({'action':'apply' if a.apply else 'preview','common_servers':NAMES,'agent_configs':len(updates),
                      'credentials':'resolved through gh at launch; no copied token values'}))
    if not a.apply:return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup=HOME/'.local/share/agent-skills'/('mcp-backup-'+stamp);backup.mkdir(parents=True,mode=0o700)
    record=[]
    for i,(path,text) in enumerate(updates.items()):
        target=backup/(str(i)+'-'+path.name);previous=None
        if path.exists():shutil.copy2(path,target);target.chmod(0o600);previous=str(target)
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix(path.suffix+'.mcp-tmp');temporary.write_text(text);temporary.chmod(0o600);temporary.replace(path)
        record.append({'path':str(path),'backup':previous,'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    # The filtered ECC plugin must not start a second, unconfigured browser server.
    duplicate=HOME/'.claude/skills/ecc/.mcp.json'
    if duplicate.exists():
        target=backup/'ecc-mcp.json';duplicate.rename(target)
        record.append({'path':str(duplicate),'backup':str(target),'removed_duplicate':True})
    (backup/'receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'backup':str(backup)}))


if __name__=='__main__':main()
