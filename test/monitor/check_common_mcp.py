#!/usr/bin/env python3
"""Check each agent's configured common MCP command with real read-only calls.

Only names, counts and statuses are saved. Tool responses and credential values
never enter the report. Uses the installed MCP Python client SDK.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tomllib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from host_probe import mcp_fingerprint

ROOT=Path(__file__).resolve().parents[2]
HOME=Path.home()
COMMON=['git','github','chrome-devtools']


def configs():
    codex=tomllib.loads((HOME/'.codex/config.toml').read_text())['mcp_servers']
    claude=json.loads((HOME/'.claude.json').read_text()).get('mcpServers',{})
    oc=json.loads((HOME/'.config/opencode/opencode.json').read_text()).get('mcp',{}).get('servers',{})
    agy=json.loads((HOME/'.gemini/config/mcp_config.json').read_text()).get('mcpServers',{})
    return {'codex':codex,'claude':claude,'opencode':oc,'antigravity':agy}


def argv(config):
    command=config['command']
    return command if isinstance(command,list) else [command,*config.get('args',[])]


async def check(agent,name,config,gate):
    row={'name':name,'scope':'common','configured':bool(config),'enabled':not config.get('disabled',False),
         'status':'unverified','tool_count':None,'checked_at':None,
         'note':'Direct handshake and read-only call using this agent configuration; session reload is separate.'}
    if not config:return row
    row['config_fingerprint']=mcp_fingerprint(argv(config))
    try:
        async with gate, asyncio.timeout(60):
            args=argv(config)
            with open(os.devnull,'w') as err:
                async with stdio_client(StdioServerParameters(command=args[0],args=args[1:],env=dict(os.environ)),errlog=err) as (read,write):
                    async with ClientSession(read,write) as client:
                        initialized=await client.initialize()
                        row['server_version']=initialized.serverInfo.version
                        listing=await client.list_tools()
                        row['tool_count']=len(listing.tools)
                        tool,params={'git':('git_status',{'repo_path':str(ROOT)}),'github':('get_me',{}),
                                     'chrome-devtools':('list_pages',{})}[name]
                        result=await client.call_tool(tool,params)
                        row['read_only_tool']=tool
                        row['status']='error' if result.isError else 'connected'
                        if result.isError:row['note']='Read-only tool returned an error; response content not retained.'
    except Exception as exc:
        row['status']='error';row['note']='MCP verification failed: '+type(exc).__name__
    row['checked_at']=datetime.now(timezone.utc).isoformat()
    return row


async def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'test/results/common-mcp.json');args=p.parse_args()
    configured=configs();gate=asyncio.Semaphore(3)
    groups=[]
    expected={name:argv(configured['codex'][name]) for name in COMMON}
    for agent,servers in configured.items():
        rows=await asyncio.gather(*(check(agent,name,servers.get(name,{}),gate) for name in COMMON))
        groups.append({'agent':agent,'common_configured_count':sum(r['configured'] for r in rows),'servers':rows,
                       'commands_match':all(argv(servers[n])==expected[n] for n in COMMON)})
        print(agent, [(r['name'],r['status'],r['tool_count']) for r in rows],flush=True)
    result={'common_servers':COMMON,'agents':groups,'observed_at':datetime.now(timezone.utc).isoformat(),
            'verification':'Configured commands tested directly; not a claim about already-open agent processes.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    if not all(r['status']=='connected' for g in groups for r in g['servers']):raise SystemExit(1)


if __name__=='__main__':asyncio.run(main())
