#!/usr/bin/env python3
"""Configure local metrics only after the collector allowlist has been verified."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tomllib

BEGIN = '# BEGIN agent-observatory native metrics'
END = '# END agent-observatory native metrics'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    args = p.parse_args()
    home = Path.home()
    codex = home/'.codex/config.toml'
    claude = home/'.claude/settings.json'
    text = codex.read_text()
    if BEGIN in text:
        before, tail = text.split(BEGIN, 1)
        text = before + tail.split(END, 1)[1]
    if 'otel' in tomllib.loads(text):
        raise SystemExit('Existing custom OTel configuration requires manual merge')
    updated = text.rstrip() + '\n\n' + BEGIN + '''
[otel]
exporter = "none"
trace_exporter = "none"
log_user_prompt = false
metrics_exporter = { otlp-http = { endpoint = "http://127.0.0.1:4318/v1/metrics", protocol = "binary" } }
''' + END + '\n'
    assert tomllib.loads(updated)['otel']['log_user_prompt'] is False
    settings = json.loads(claude.read_text())
    settings.setdefault('env', {}).update({
        'CLAUDE_CODE_ENABLE_TELEMETRY':'1',
        'OTEL_EXPORTER_OTLP_ENDPOINT':'http://127.0.0.1:4318',
        'OTEL_EXPORTER_OTLP_PROTOCOL':'http/protobuf',
        'OTEL_METRICS_EXPORTER':'otlp', 'OTEL_METRIC_EXPORT_INTERVAL':'10000',
        'OTEL_LOGS_EXPORTER':'none', 'OTEL_TRACES_EXPORTER':'none',
        'OTEL_LOG_USER_PROMPTS':'0', 'OTEL_LOG_ASSISTANT_RESPONSES':'0',
        'OTEL_LOG_TOOL_DETAILS':'0', 'OTEL_LOG_TOOL_CONTENT':'0',
    })
    print(json.dumps({'action':'apply' if args.apply else 'preview', 'agents':['codex','claude'],
                      'signals':['metrics'], 'endpoint':'127.0.0.1:4318', 'requires':'new agent process'}))
    if not args.apply:
        return
    backup=home/'.local/share/agent-skills'/('otel-backup-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    backup.mkdir(parents=True, mode=0o700)
    records=[]
    for path, value in [(codex, updated),(claude,json.dumps(settings,ensure_ascii=False,indent=2)+'\n')]:
        target=backup/(path.parent.name.lstrip('.')+'-'+path.name)
        shutil.copy2(path,target); target.chmod(0o600)
        tmp=path.with_suffix(path.suffix+'.otel-tmp'); tmp.write_text(value); tmp.chmod(path.stat().st_mode & 0o777);tmp.replace(path)
        records.append({'path':str(path),'backup':str(target),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (backup/'receipt.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({'backup':str(backup)}))


if __name__ == '__main__':
    main()
