#!/usr/bin/env python3
"""Read-only live deployment checks; persist sanitized evidence, not raw snapshots."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def main():
    health = get('http://127.0.0.1:8787/health')
    assert all(health.get(k) == 'ok' for k in ('status', 'collector', 'prometheus')), health
    current = get('http://127.0.0.1:8787/api/snapshot')
    snapshot = current['snapshot']
    assert current['status'] == 'ok', current['status']
    assert not snapshot['errors'], snapshot['errors']
    queries = {}
    for query in ('observatory_gpu_utilization_percent', 'observatory_agent_tokens',
                  'observatory_skills_installed', 'traces_span_metrics_calls_total'):
        data = get('http://127.0.0.1:9090/api/v1/query?' + urllib.parse.urlencode({'query': query}))
        rows = data['data']['result']
        assert data['status'] == 'success' and rows, query
        queries[query] = {'series': len(rows), 'sample_present': True}
    raw = subprocess.check_output(['docker', 'compose', '-f', str(ROOT/'test/monitor/compose.yaml'),
                                   'ps', '--format', 'json'], text=True)
    services = [{k: row.get(k) for k in ('Service', 'State', 'Health')}
                for row in map(json.loads, raw.splitlines())]
    assert len(services) == 3 and all(s['State'] == 'running' for s in services)
    service = subprocess.check_output(['systemctl', '--user', 'is-active',
                                      'agent-observatory-probe.service'], text=True).strip()
    assert service == 'active'
    agents = [{'id': a['id'], 'status': a['status'], 'tokens_observed': bool(a.get('usage')),
               'quota_observed': bool((a.get('plan') or {}).get('limits'))} for a in snapshot['agents']]
    assert len(agents) == 4 and all(a['tokens_observed'] for a in agents)
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'result': 'PASS',
              'health': health, 'snapshot_status': current['status'], 'snapshot_errors': [],
              'probe_service': service, 'containers': services, 'agents': agents,
              'prometheus_queries': queries}
    target = ROOT/'test/results/monitor-deployment.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
