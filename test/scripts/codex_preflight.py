#!/usr/bin/env python3
"""Read Codex account/limits/skills/MCP metadata; never emit identity or credentials."""
import json
from pathlib import Path
import queue
import threading
import subprocess
import time

root = Path(__file__).resolve().parents[2]
p = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
messages = queue.Queue()


def read_messages():
    # Consume buffered lines continuously. select()+TextIO.readline() can miss
    # a second JSON line already buffered in Python and falsely time out.
    for line in p.stdout:
        messages.put(json.loads(line))
    messages.put(None)


threading.Thread(target=read_messages, daemon=True).start()


def rpc(i, method, params):
    p.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': i, 'method': method, 'params': params}) + '\n')
    p.stdin.flush()
    end = time.monotonic() + 45
    while time.monotonic() < end:
        try:
            obj = messages.get(timeout=max(0.01, end - time.monotonic()))
        except queue.Empty:
            break
        if obj is None:
            return {'error': {'message': 'server exited'}}
        if obj.get('id') == i:
            return obj
    return {'error': {'message': 'RPC timeout'}}


out = {'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
try:
    rpc(1, 'initialize', {'clientInfo': {'name': 'environment-preflight', 'version': '1.0'},
                         'capabilities': {'experimentalApi': True}})
    p.stdin.write('{"jsonrpc":"2.0","method":"initialized","params":{}}\n')
    p.stdin.flush()
    result = rpc(2, 'account/read', {'refreshToken': False})
    a = result.get('result', {}).get('account') or {}
    out['account'] = {k: a.get(k) for k in ['type', 'planType']}
    if 'error' in result:
        out['account_error'] = result['error'].get('message', '')[:160]
    r = rpc(3, 'account/rateLimits/read', {})
    if 'error' in r:
        out['rate_limits_error'] = r['error'].get('message', '')[:160]
    else:
        limits = r.get('result', {})
        out['rate_limits'] = limits.get('rateLimits')
        # The API rate-limit snapshot has no account identity or token fields.
    s = rpc(4, 'skills/list', {'cwds': [str(root)], 'forceReload': True})
    for row in s.get('result', {}).get('data', []):
        skills = row.get('skills', [])
        enabled = [x['name'] for x in skills if x.get('enabled', True)]
        required = json.loads((root / 'distribution/profiles/codex-general-sw.json').read_text())['user_required']
        out['skills'] = {'total': len(skills), 'enabled': len(enabled),
                         'error_count': len(row.get('errors', [])),
                         'required_missing': sorted(set(required) - set(enabled)),
                         'extra_enabled': sorted(set(enabled) - set(json.loads((root / 'distribution/profiles/codex-general-sw.json').read_text())['enabled']))}
    m = rpc(5, 'mcpServerStatus/list', {'limit': 100, 'detail': 'toolsAndAuthOnly'})
    if 'error' in m:
        out['mcp_error'] = m['error'].get('message', '')[:160]
    else:
        out['mcp'] = [{k: row.get(k) for k in ['name', 'authStatus', 'runtimeStatus']} |
                      {'tool_count': len(row.get('tools', {})), 'discovery_error': bool(row.get('toolsError'))}
                      for row in m.get('result', {}).get('data', [])]
        out['mcp_has_more'] = bool(m.get('result', {}).get('nextCursor'))
finally:
    p.terminate()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
print(json.dumps(out, ensure_ascii=False, indent=2))
