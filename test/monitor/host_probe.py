#!/usr/bin/env python3
"""Read-only host observer. Exports allowlisted aggregates, never conversation text.

Run outside the web container. Only the sanitized output directory is mounted there.
Local usage is available retained history, not subscription billing or account totals.
"""
from __future__ import annotations
import argparse
import csv
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import re
import sqlite3
import subprocess
import threading
import time
import tomllib
from datetime import datetime, timezone
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
DEFAULT_OUTPUT = ROOT / 'test/.local/monitor/snapshot.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def iso(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    return datetime.fromtimestamp(value / 1000 if value > 1e11 else value, timezone.utc).isoformat()


def load(path, fallback=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {} if fallback is None else fallback


def command(args, timeout=8):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def num(value):
    try:
        n = float(value)
        return n if n == n and abs(n) != float('inf') else None
    except (ValueError, TypeError):
        return None


def json_lines(path):
    try:
        with path.open() as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue  # Concurrent writer can leave a partial final line.
    except OSError:
        return


def clean_usage(u, kind):
    """Normalize input INCLUDING cache. Reasoning is already a subset of output."""
    inp = u.get('input_tokens', u.get('input', 0)) or 0
    out = u.get('output_tokens', u.get('output', 0)) or 0
    cache = u.get('cached_input_tokens', u.get('cache_read_input_tokens', (u.get('cache') or {}).get('read', 0))) or 0
    write = u.get('cache_creation_input_tokens', (u.get('cache') or {}).get('write', 0)) or 0
    if kind in ('claude', 'opencode'):
        inp += cache + write
    return {'input_tokens': inp, 'output_tokens': out, 'cached_input_tokens': cache,
            'cache_write_input_tokens': write, 'total_tokens': inp + out}


def aggregate(records):
    models = {}
    sessions = set()
    latest = None
    for model, session, timestamp, usage in records:
        if not model or model == '<synthetic>':
            continue
        row = models.setdefault(model, {'model': model, 'sessions_set': set(),
            **dict.fromkeys(['input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'total_tokens'], 0)})
        row['sessions_set'].add(session)
        sessions.add(session)
        for key, value in usage.items():
            if key in row and isinstance(value, (int, float)):
                row[key] += value
        if timestamp and (latest is None or timestamp > latest[0]):
            latest = (timestamp, model)
    rows = []
    for row in models.values():
        row['sessions'] = len(row.pop('sessions_set'))
        rows.append(row)
    keys = ['input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'total_tokens']
    usage = {k: sum(r[k] for r in rows) if rows else None for k in keys}
    usage.update(sessions=len(sessions), cost_usd=None, reasoning_tokens=None,
                 window='보존된 로컬 이력 전체 · 계정 청구량 아님')
    return sorted(rows, key=lambda r: r['total_tokens'], reverse=True), usage, latest


def codex_usage(home=HOME):
    records = {}
    limits = None
    for path in (home / '.codex/sessions').rglob('*.jsonl'):
        model = 'unknown'
        events = []
        legacy = []
        previous = 0
        for r in json_lines(path):
            p = r.get('payload') or {}
            timestamp = r.get('timestamp')
            if r.get('type') == 'turn_context':
                model = p.get('model', model)
            elif r.get('type') == 'token_usage_record':
                events.append((p.get('response_id') or (str(path), r.get('ordinal')),
                               (model, str(path), timestamp, clean_usage(p.get('usage') or {}, 'codex'))))
            elif r.get('type') == 'event_msg' and p.get('type') == 'token_count':
                if p.get('rate_limits') and (limits is None or (timestamp or '') > limits[0]):
                    limits = (timestamp or '', p['rate_limits'])
                info = p.get('info') or {}
                cumulative = info.get('total_token_usage') or {}
                total = cumulative.get('total_tokens', previous)
                # Legacy records repeat the latest usage on unrelated events; only
                # accept when the cumulative total advances. New records take precedence.
                if total > previous:
                    legacy.append(((str(path), total), (model, str(path), timestamp,
                                   clean_usage(info.get('last_token_usage') or {}, 'codex'))))
                previous = total
        for key, value in events or legacy:
            records[key] = value
    return list(records.values()), limits


def claude_usage(home=HOME):
    records, skills = {}, {}
    for path in (home / '.claude/projects').rglob('*.jsonl'):
        for r in json_lines(path):
            if r.get('type') != 'assistant':
                continue
            m = r.get('message') or {}
            timestamp = r.get('timestamp')
            # Streamed content blocks may repeat the same message usage.
            key = m.get('id') or r.get('uuid')
            if key and m.get('usage'):
                value = (m.get('model'), r.get('sessionId') or str(path), timestamp,
                         clean_usage(m['usage'], 'claude'))
                if key not in records or value[3]['total_tokens'] >= records[key][3]['total_tokens']:
                    records[key] = value
            for item in m.get('content') or []:
                if isinstance(item, dict) and item.get('type') == 'tool_use' and item.get('name') == 'Skill':
                    name = (item.get('input') or {}).get('skill')
                    if name:
                        skills[item.get('id') or (key, name)] = (name, timestamp)
    return list(records.values()), list(skills.values())


def opencode_usage(home=HOME):
    path = home / '.local/share/opencode/opencode.db'
    if not path.exists():
        return [], []
    records = []
    skills = []
    # SQLite read-only connection respects WAL; do not use immutable on a live DB.
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True, timeout=2) as db:
        for sid, stamp, data in db.execute("SELECT session_id,time_updated,data FROM session_message WHERE type='assistant'"):
            r = json.loads(data)
            if r.get('tokens'):
                records.append(((r.get('model') or {}).get('id'), sid, iso(stamp), clean_usage(r['tokens'], 'opencode')))
            for part in r.get('content') or []:
                if not isinstance(part, dict) or part.get('type') != 'tool' or part.get('name') != 'skill':
                    continue
                state = part.get('state') or {}
                inp = state.get('input') or {}
                name = inp.get('id') or inp.get('name')
                if name:
                    skills.append((name, iso(stamp)))
        # OpenCode V2 stores tool calls as tool-call parts, not V1 tool state.
        for typ, stamp, data in db.execute("SELECT type,time_updated,data FROM session_part WHERE type IN ('tool','tool-call')"):
            r = json.loads(data)
            tool = r.get('tool') or r.get('name')
            inp = r.get('input') or (r.get('state') or {}).get('input') or {}
            if tool == 'skill' and isinstance(inp, dict) and inp.get('name'):
                skills.append((inp['name'], iso(stamp)))
    return records, skills


def codex_metadata(repo=ROOT):
    p = subprocess.Popen(['codex', 'app-server', '--stdio'], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    messages = queue.Queue()
    def read():
        for line in p.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                pass
    threading.Thread(target=read, daemon=True).start()
    def rpc(i, method, params):
        p.stdin.write(json.dumps({'id': i, 'method': method, 'params': params}) + '\n')
        p.stdin.flush()
        end = time.monotonic() + 12
        while time.monotonic() < end:
            try:
                r = messages.get(timeout=max(0.01, end - time.monotonic()))
            except queue.Empty:
                break
            if r.get('id') == i:
                return r.get('result') or {}
        return {}
    try:
        rpc(1, 'initialize', {'clientInfo': {'name': 'local-observatory', 'version': '1.0'}})
        p.stdin.write('{"method":"initialized","params":{}}\n'); p.stdin.flush()
        acct = rpc(2, 'account/read', {'refreshToken': False}).get('account') or {}
        rate = rpc(3, 'account/rateLimits/read', {}).get('rateLimits')
        data = rpc(4, 'skills/list', {'cwds': [str(repo)], 'forceReload': True}).get('data', [])
        skills = []
        for row in data:
            for s in row.get('skills') or []:
                skills.append({'name': s['name'], 'path': str(s.get('path', '')).replace(str(HOME), '~'),
                    'description': str(s.get('description') or '')[:280], 'enabled': s.get('enabled', True),
                    'origin': 'Codex skills/list', 'invocations': None, 'last_used_at': None,
                    'usage_evidence': '호출 집계 미계측'})
        return {'observed_at': now(), 'plan': acct.get('planType'), 'rate': rate, 'skills': skills}
    finally:
        p.terminate()
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait()


def normalize_limits(rate):
    result = []
    for key in ('primary', 'secondary'):
        r = (rate or {}).get(key)
        if r:
            minutes = r.get('windowDurationMins', r.get('window_minutes'))
            result.append({'label': f'{minutes}분 한도' if minutes else key,
                'used_percent': r.get('usedPercent', r.get('used_percent')),
                'reset_at': iso(r.get('resetsAt', r.get('resets_at')))})
    return result


def local_metadata():
    """Native inventory and runtime identity. No credentials, env or process args."""
    result = {}
    raw = command(['agy', '--output-format', 'json', '--print', '/usage'], timeout=15)
    if raw:
        try:
            data = json.loads(raw).get('command', {}).get('data', {})
            limits = []
            for group in data.get('groups', []):
                for bucket in group.get('buckets', []):
                    remaining = num(bucket.get('remaining_fraction'))
                    if remaining is not None:
                        limits.append({'label': group.get('name', '') + ' · ' + bucket.get('window', bucket.get('name', '')),
                            'used_percent': round((1-remaining)*100, 2), 'remaining_percent': round(remaining*100, 2),
                            'reset_at': bucket.get('reset_time')})
            if limits:
                result['antigravity_plan'] = {'name': 'Google AI Pro', 'source': 'Antigravity native /usage (no model turn)',
                    'observed_at': now(), 'limits': limits}
        except (ValueError, AttributeError, TypeError):
            pass
    raw = command(['opencode', 'api', 'get', '/api/skill', '--param', 'directory=' + str(ROOT)], timeout=12)
    if raw:
        try:
            result['opencode_skills'] = [{'name': r.get('id') or r['name'],
                'path': str(r.get('path', '')).replace(str(HOME), '~'),
                'description': str(r.get('description') or '')[:280],
                'enabled': None, 'origin': 'OpenCode native registration', 'invocations': None,
                'last_used_at': None, 'usage_evidence': '호출 집계 미계측'} for r in json.loads(raw).get('data', [])]
        except (ValueError, KeyError, TypeError):
            pass
    raw = command(['docker', 'inspect', 'llm-server', '--format', '{{json .Path}}\n{{json .Config.Image}}'])
    if raw:
        try:
            executable, image = map(json.loads, raw.splitlines())
            result['inference'] = {'container_image': image, 'runtime_executable': Path(executable).name,
                'engine': 'llama.cpp' if Path(executable).name == 'llama-server' else None,
                'observed_at': now()}
            version = command(['docker', 'exec', 'llm-server', 'python', '-c',
                               "import importlib.metadata; print(importlib.metadata.version('vllm'))"], timeout=10)
            if version and len(version) < 120:
                result['inference']['installed_vllm_version'] = version
        except (ValueError, TypeError):
            pass
    return result


def skill_file(path, enabled=None, origin='filesystem'):
    try:
        text = path.read_text()[:20000]
    except OSError:
        return None
    name = re.search(r'^name:\s*[\'"]?([^\n\'"]+)', text, re.M)
    desc = re.search(r'^description:\s*[\'"]?([^\n]+)', text, re.M)
    return {'name': name.group(1).strip() if name else path.parent.name,
        'description': (desc.group(1).strip('"\' ') if desc else '')[:280],
        'path': str(path).replace(str(HOME), '~'), 'enabled': enabled, 'origin': origin,
        'invocations': None, 'last_used_at': None, 'usage_evidence': '호출 집계 미계측'}


def scan_skills(roots):
    found = {}
    for root, enabled, origin in roots:
        root = Path(root)
        if not root.exists():
            continue
        # glob follows directory symlinks at this level (Path.rglob does not).
        paths = list(root.glob('*/SKILL.md')) + list(root.glob('skills/*/SKILL.md'))
        for p in paths:
            row = skill_file(p, enabled, origin)
            if row:
                found[(row['name'], str(p.resolve()))] = row
    return list(found.values())


def inventory(metadata, usage_evidence):
    timestamp = now()
    claude = [(HOME/'.claude/skills', True, 'user'), (ROOT/'.claude/skills', True, 'project')]
    claude_settings = load(HOME/'.claude/settings.json')
    enabled = claude_settings.get('enabledPlugins', {})
    for plugin, installs in load(HOME/'.claude/plugins/installed_plugins.json').get('plugins', {}).items():
        for entry in installs:
            if entry.get('installPath'):
                claude.append((Path(entry['installPath']), enabled.get(plugin, None), plugin))
    # Auto-loaded local plugins are not in installed_plugins.json. Count their selected
    # entry points, not the preserved upstream support directories.
    for manifest in (HOME/'.claude/skills').glob('*/.claude-plugin/plugin.json'):
        plugin = load(manifest).get('name', manifest.parent.parent.name) + '@skills-dir'
        claude.append((manifest.parent.parent, enabled.get(plugin, True), plugin))
    for synced in (HOME/'.claude/skills/synced').glob('*'):
        if synced.is_dir():
            claude.append((synced, True, 'anthropic-skills'))
    claude_rows = scan_skills(claude)
    for row in claude_rows:
        override_name = ('anthropic-skills:' + row['name']) if row['origin'] == 'anthropic-skills' else row['name']
        if claude_settings.get('skillOverrides', {}).get(override_name) in ('off', 'user-invocable-only'):
            row['enabled'] = False
    oc = (metadata or {}).get('opencode_skills') or scan_skills([(HOME/'.config/opencode/skills', None, 'user'),
                     (HOME/'.agents/skills', None, 'shared'), (ROOT/'.agents/skills', None, 'project')])
    rules = load(HOME/'.config/opencode/opencode.json').get('permissions', [])
    for row in oc:
        for rule in rules:
            if rule.get('action') == 'skill' and fnmatch.fnmatch(row['name'], rule.get('resource', '')):
                row['enabled'] = rule.get('effect') == 'allow'
    groups = [
        ('codex', (metadata or {}).get('skills', []), 'native skills/list'),
        ('claude', claude_rows, 'filesystem + installed/local plugins + skillOverrides; native bundled tools separate'),
        ('opencode', oc, 'native registration + explicit permission rules; unset enabled state unverified' if (metadata or {}).get('opencode_skills') else 'filesystem + explicit permission rules; built-ins not enumerated'),
        ('antigravity', scan_skills([(HOME/'.gemini/antigravity-cli/skills', None, 'user'),
                                   (ROOT/'.agents/skills', None, 'project')]), 'filesystem; runtime enabled state unverified')]
    agents = []
    common = load(ROOT/'distribution/profiles/common-general-sw.json').get('skills', [])
    selected = {r['directory']: r['id'] for r in common}
    for name, rows, source in groups:
        evidence = usage_evidence.get(name, [])
        for row in rows:
            row['common_id'] = selected.get(row['name'].split(':')[-1])
            matches = [stamp for skill, stamp in evidence if skill.split(':')[-1] == row['name'].split(':')[-1]]
            if matches:
                row['invocations'] = len(matches)
                row['last_used_at'] = max(x for x in matches if x) if any(matches) else None
                row['usage_evidence'] = '로컬 로그의 호출 요청 · 성공/완주 여부 별도'
        agents.append({'agent': name, 'installed_count': len(rows),
            'common_selected_count': len(common),
            'common_installed_count': len({r['common_id'] for r in rows if r.get('common_id')}),
            'common_enabled_count': (len({r['common_id'] for r in rows if r.get('common_id') and r['enabled'] is True})
                                     if any(r['enabled'] is not None for r in rows) else None),
            'platform_extra_count': sum(r['enabled'] is True and not r.get('common_id') for r in rows),
            'enabled_count': sum(r['enabled'] is True for r in rows) if rows and all(r['enabled'] is not None for r in rows) else None,
            'source': source, 'observed_at': (metadata or {}).get('observed_at') if name == 'codex' else timestamp,
            'skills': rows})
    repository = []
    for p in (ROOT/'skills').glob('*/SKILL.md'):
        row = skill_file(p)
        if row:
            row['path'] = str(p.relative_to(ROOT)); repository.append(row)
    return {'repository': repository, 'agents': agents,
            'notes': ['파일 존재·활성 설정·호출 요청은 다른 증거입니다. 미계측은 미사용이 아닙니다.',
                      '저장소 원본과 외부 스킬 등록부는 별개입니다. 외부 등록 목록: skills/README.md',
                      'OpenCode registration and final build-agent permissions differ. Activation outside explicit rules is unverified.']}


def mcp_fingerprint(command):
    inputs = {'command':command}
    for name in ('mcp_launch.py','profiles/common-mcp.json'):
        path=ROOT/'distribution'/name
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()


def mcp_inventory():
    """Sanitized configured servers plus dated protocol checks; never expose env/headers."""
    common = list(load(ROOT/'distribution/profiles/common-mcp.json').get('servers', {}))
    try:
        codex = tomllib.loads((HOME/'.codex/config.toml').read_text()).get('mcp_servers', {})
    except (OSError, ValueError):
        codex = {}
    configs = {'codex':codex, 'claude':load(HOME/'.claude.json').get('mcpServers', {}),
               'opencode':load(HOME/'.config/opencode/opencode.json').get('mcp', {}).get('servers', {}),
               'antigravity':load(HOME/'.gemini/config/mcp_config.json').get('mcpServers', {})}
    evidence = load(ROOT/'test/results/common-mcp.json')
    checked = {a['agent']:{r['name']:r for r in a.get('servers',[])} for a in evidence.get('agents',[])}
    groups=[]
    for agent, servers in configs.items():
        rows=[]
        for name in sorted(set(common)|set(servers)):
            config=servers.get(name)
            enabled=bool(config) and not config.get('disabled',False) and config.get('enabled',True)
            row={'name':name, 'scope':'common' if name in common else 'platform',
                 'configured':config is not None, 'enabled':enabled,
                 'status':'configured' if config else 'unverified', 'tool_count':None, 'checked_at':None,
                 'note':'Configured; no current protocol verification.'}
            if config and config.get('command'):
                command=config['command']
                args=command if isinstance(command,list) else [command,*config.get('args',[])]
                fingerprint=mcp_fingerprint(args)
                prior=checked.get(agent,{}).get(name,{})
                if enabled and prior.get('config_fingerprint')==fingerprint:
                    for key in ('status','tool_count','checked_at','note'):
                        row[key]=prior.get(key,row[key])
                    row['note']='Last read-only protocol verification, not continuous session monitoring.'
            rows.append(row)
        groups.append({'agent':agent,'common_configured_count':sum(r['configured'] for r in rows if r['scope']=='common'),
                       'servers':rows})
    return {'common_servers':common,'agents':groups,'observed_at':now()}


_cpu_previous = None


def hardware(metadata=None):
    global _cpu_previous
    mem = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        k, v = line.split(':', 1); mem[k] = int(v.strip().split()[0]) * 1024
    cpu = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    total, idle = sum(cpu), cpu[3] + cpu[4]
    percent = None
    if _cpu_previous and total > _cpu_previous[0]:
        percent = round(100 * (1 - (idle - _cpu_previous[1]) / (total - _cpu_previous[0])), 2)
    _cpu_previous = total, idle
    gpu = []
    raw = command(['nvidia-smi', '--query-gpu=name,driver_version,power.draw,power.limit,memory.used,memory.total,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'])
    for r in csv.reader((raw or '').splitlines(), skipinitialspace=True):
        if len(r) == 8:
            gpu.append({'name': r[0], 'driver_version': r[1], 'power_watts': num(r[2]),
                'power_limit_watts': num(r[3]), 'memory_used_bytes': num(r[4]) * 1048576 if num(r[4]) is not None else None,
                'memory_total_bytes': num(r[5]) * 1048576 if num(r[5]) is not None else None,
                'utilization_percent': num(r[6]), 'temperature_c': num(r[7]),
                'memory_note': 'GB10 공유 메모리: 전용 VRAM 카운터 미지원' if num(r[5]) is None else None})
    process_raw = command(['nvidia-smi', '--query-compute-apps=process_name,used_gpu_memory',
                           '--format=csv,noheader,nounits'])
    processes = [{'name':Path(r[0]).name, 'memory_used_bytes':num(r[1])*1048576}
                 for r in csv.reader((process_raw or '').splitlines(), skipinitialspace=True)
                 if len(r)==2 and num(r[1]) is not None]
    # A per-process sum is not dedicated VRAM usage and has no valid VRAM percentage on GB10.
    if len(gpu) == 1:
        gpu[0]['compute_processes'] = processes
        gpu[0]['process_memory_used_bytes'] = sum(r['memory_used_bytes'] for r in processes) if processes else None
    inference = {'endpoint': 'localhost:8000', 'reachable': False, 'models': [], 'engine': None, 'version': None}
    try:
        with urlopen('http://127.0.0.1:8000/v1/models', timeout=2) as response:
            inference['models'] = [x['id'] for x in json.load(response).get('data', [])]
        inference['reachable'] = True
        with urlopen('http://127.0.0.1:8000/version', timeout=2) as response:
            inference['version'] = json.load(response).get('version')
    except (OSError, ValueError, KeyError):
        pass
    inference.update((metadata or {}).get('inference') or {})
    if inference.get('engine') == 'llama.cpp':
        try:
            with urlopen('http://127.0.0.1:8000/props', timeout=2) as response:
                props = json.load(response)
            build = props.get('build_info')
            if isinstance(build, str):
                inference['version'] = build[:160]
        except (OSError, ValueError, KeyError):
            pass
    used = mem['MemTotal'] - mem['MemAvailable']
    return {'hostname': platform.node(), 'architecture': platform.machine(), 'os': platform.system(),
        'kernel': platform.release(), 'cpu_count': os.cpu_count(), 'cpu_percent': percent,
        'memory_total_bytes': mem['MemTotal'], 'memory_used_bytes': used,
        'memory_used_percent': round(used / mem['MemTotal'] * 100, 2), 'gpu': gpu,
        'inference': inference, 'notes': ([] if gpu else ['GPU 조회 불가: 드라이버/권한/도구 상태 확인']),
        'observed_at': now()}


def agent_row(name, records, plan, notes):
    models, usage, latest = aggregate(records)
    return {'id': name, 'name': {'codex': 'Codex', 'claude': 'Claude Code', 'opencode': 'OpenCode', 'antigravity': 'Antigravity'}[name],
            'model': latest[1] if latest else None, 'status': 'observed' if latest else 'unavailable',
            'source': 'local session usage' if latest else '지원되는 사용량 소스 없음',
            'observed_at': latest[0] if latest else None, 'plan': plan, 'usage': usage, 'models': models, 'notes': notes}


def antigravity_statusline_usage():
    records = []
    for path in (DEFAULT_OUTPUT.parent/'antigravity-sessions').glob('*.json'):
        r = load(path)
        usage = r.get('usage') or {}
        if isinstance(usage.get('input_tokens'), (int, float)) and isinstance(usage.get('output_tokens'), (int, float)):
            # The native statusline supplies cumulative session totals, not a
            # historical model breakdown. Keep that distinction in the label.
            records.append(('세션 누적 · 모델별 분해 미지원', path.stem, r.get('observed_at'), usage))
    return records


def snapshot(metadata):
    errors = []
    def safe(name, fn, fallback):
        try:
            return fn()
        except Exception as e:
            errors.append(name + ': ' + type(e).__name__)
            return fallback
    cx, fallback_rate = safe('codex usage', codex_usage, ([], None))
    cl, cl_skills = safe('claude usage', claude_usage, ([], []))
    oc, oc_skills = safe('opencode usage', opencode_usage, ([], []))
    rate = (metadata or {}).get('rate')
    stamp = (metadata or {}).get('observed_at')
    if not rate and fallback_rate:
        stamp, rate = fallback_rate
    plan = {'name': (metadata or {}).get('plan') or (rate or {}).get('plan_type'),
            'source': 'Codex account API' if (metadata or {}).get('rate') else 'Codex retained session rate-limit observation',
            'observed_at': stamp, 'limits': normalize_limits(rate)}
    # These are explicitly dated UI observations from preflight, not live APIs.
    cl_plan = {'name': 'Claude Pro', 'source': 'preflight /usage UI observation (historical)',
        'observed_at': '2026-10-31T03:00:00+00:00',
        'limits': [{'label': '세션 (과거 관측)', 'used_percent': 18, 'reset_at': '2026-10-31T05:49:00+00:00'},
                   {'label': '주간 (과거 관측)', 'used_percent': 3, 'reset_at': '2026-11-01T16:59:00+00:00'}]}
    live_claude_plan = load(DEFAULT_OUTPUT.parent/'claude-plan.json')
    if live_claude_plan.get('limits'):
        cl_plan.update(live_claude_plan)
    agents = [agent_row('codex', cx, plan, ['캐시 읽기는 입력 토큰에 포함. 추론은 출력에 포함. 중복 합산하지 않음.']),
              agent_row('claude', cl, cl_plan, ['메시지 ID로 스트리밍 중복 제거. 입력은 일반 입력+캐시 읽기+캐시 쓰기.',
                        '구독 한도는 네이티브 상태줄의 마지막 관측값. 활동이 없으면 갱신되지 않으므로 관측 시각 확인.' if live_claude_plan.get('limits') else '구독 한도는 과거 UI 관측값이며 실시간 한도가 아님.']),
              agent_row('opencode', oc, {'name': '로컬 추론', 'source': 'local provider', 'observed_at': now(), 'limits': []},
                        ['로컬 이력은 공급자가 바뀐 과거 모델도 포함할 수 있음.', '토큰 비용과 GPU 전력 비용은 별도.']),
              agent_row('antigravity', antigravity_statusline_usage(), (metadata or {}).get('antigravity_plan') or {'name': 'Google AI Pro', 'source': 'preflight UI observation',
                        'observed_at': '2026-10-31T03:09:00+00:00', 'limits': []},
                        ['네이티브 상태줄이 관측한 세션 누적 입력/출력을 사용. 과거 미관측 세션은 포함되지 않음.',
                         '모델별 이력 분해·누적 캐시 토큰은 미지원. 현재 선택 모델과 세션 전체 토큰을 구분.'])]
    if agents[-1]['usage']['total_tokens'] is not None:
        agents[-1]['source'] = 'Antigravity native statusline observed sessions'
        agents[-1]['usage']['window'] = '상태줄로 관측된 세션 누적 · 과거 미관측 세션 제외'
        agents[-1]['usage']['cached_input_tokens'] = None
        agents[-1]['usage']['cache_write_input_tokens'] = None
        for row in agents[-1]['models']:
            row['cached_input_tokens'] = None
            row['cache_write_input_tokens'] = None
    elif (metadata or {}).get('antigravity_plan'):
        agents[-1]['status'] = 'partial'
        agents[-1]['source'] = 'Antigravity native quota; token observer awaiting first sample'
        agents[-1]['observed_at'] = metadata['antigravity_plan']['observed_at']
    configured_model = load(HOME/'.gemini/antigravity-cli/settings.json').get('model')
    if isinstance(configured_model, str):
        agents[-1]['model'] = configured_model
        agents[-1]['notes'].append('표시 모델은 로컬 설정값이며 사용량 측정 모델을 추정한 값이 아닙니다.')
    return {'schema_version': 1, 'collected_at': now(), 'agents': agents,
        'hardware': safe('hardware', lambda: hardware(metadata), {}),
        'skills': safe('skills', lambda: inventory(metadata, {'claude': cl_skills, 'opencode': oc_skills}), {'repository': [], 'agents': [], 'notes': []}),
        'mcp': safe('mcp', mcp_inventory, {'common_servers':[], 'agents':[]}),
        'errors': errors}


def write_snapshot(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False))
    os.chmod(temp, 0o644)  # Sanitized metrics are readable by the unprivileged web container.
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--interval', type=float, default=15)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--no-codex-api', action='store_true')
    args = parser.parse_args()
    metadata, updated = None, 0
    while True:
        if time.monotonic() - updated > 300:
            try:
                fresh = {} if args.no_codex_api else codex_metadata()
                metadata = {**(metadata or {}), **fresh, **local_metadata()}
            except (OSError, ValueError, BrokenPipeError):
                pass
            updated = time.monotonic()
        data = snapshot(metadata)
        write_snapshot(args.output, data)
        print(json.dumps({'collected_at': data['collected_at'], 'agents': len(data['agents']),
                          'gpu': len(data['hardware'].get('gpu', [])), 'errors': data['errors']}), flush=True)
        if args.once:
            break
        time.sleep(max(3, args.interval))


if __name__ == '__main__':
    main()
