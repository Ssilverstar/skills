#!/usr/bin/env python3
"""Temporary loopback OTLP schema probe. Never persist payload bodies or identity values."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from google.protobuf.json_format import MessageToDict
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import ExportMetricsServiceRequest
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=14318)
    p.add_argument('--seconds', type=int, default=300)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    lock = threading.Lock()
    samples = {}

    def observe(signal, data):
        for resource in data.get('resource' + signal.title(), []):
            attrs = resource.get('resource', {}).get('attributes', [])
            service = next((a['value'].get('stringValue', '') for a in attrs if a['key'] == 'service.name'), 'unknown')
            # Only known product service names are retained; other identifiers are not.
            if not any(x in service.lower() for x in ('codex', 'claude', 'opencode', 'antigravity')):
                service = 'other'
            key = service + ':' + signal
            row = samples.setdefault(key, {'service':service, 'signal':signal, 'requests':0, 'items':0,
                                          'names':[], 'attribute_keys':[], 'resource_keys':[]})
            row['requests'] += 1
            row['resource_keys'] = sorted(set(row['resource_keys']) | {a['key'] for a in attrs})
            scopes = resource.get('scope' + signal.title(), [])
            for scope in scopes:
                items = scope.get({'logs':'logRecords','metrics':'metrics','spans':'spans'}[signal], [])
                for item in items:
                    row['items'] += 1
                    attributes = item.get('attributes', [])
                    if signal == 'metrics':
                        for kind in ('sum', 'gauge', 'histogram', 'exponentialHistogram', 'summary'):
                            for point in item.get(kind, {}).get('dataPoints', []):
                                attributes += point.get('attributes', [])
                                if item.get('name') in ('codex.turn.token_usage', 'claude_code.token.usage'):
                                    schema = row.setdefault('usage_schema', {})
                                    metric = schema.setdefault(item['name'], {'kind': kind, 'labels': {}})
                                    for attr in point.get('attributes', []):
                                        if attr['key'] in ('token_type', 'type'):
                                            value = attr.get('value', {}).get('stringValue')
                                            metric['labels'].setdefault(attr['key'], [])
                                            if value not in metric['labels'][attr['key']]:
                                                metric['labels'][attr['key']].append(value)
                    name = item.get('name') or item.get('eventName')
                    if not name:
                        name = next((a['value'].get('stringValue') for a in attributes if a['key'] in ('event.name','event_name')), None)
                    if name and any(name.startswith(x) for x in ('codex.', 'claude_code.', 'opencode.', 'opencode_', 'gen_ai.')):
                        row['names'] = sorted(set(row['names']) | {name})
                    row['attribute_keys'] = sorted(set(row['attribute_keys']) | {a['key'] for a in attributes})
        result = {'observed_at':datetime.now(timezone.utc).isoformat(), 'privacy':'Only schema keys, known service/event names and counts; no body or identity values', 'samples':list(samples.values())}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_suffix('.tmp')
        temp.write_text(json.dumps(result, indent=2))
        temp.replace(args.output)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass
        def do_POST(self):
            types = {'/v1/logs':('logs', ExportLogsServiceRequest), '/v1/metrics':('metrics', ExportMetricsServiceRequest), '/v1/traces':('spans', ExportTraceServiceRequest)}
            if self.path not in types:
                self.send_error(404); return
            size = int(self.headers.get('Content-Length', 0))
            if size > 8*1024*1024:
                self.send_error(413); return
            raw = self.rfile.read(size)
            if self.headers.get('Content-Encoding') == 'gzip':
                raw = gzip.decompress(raw)
            signal, typ = types[self.path]
            if 'json' in self.headers.get('Content-Type', ''):
                data = json.loads(raw)
            else:
                request = typ(); request.ParseFromString(raw)
                data = MessageToDict(request)
            with lock:
                observe(signal, data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-protobuf')
            self.send_header('Content-Length','0'); self.end_headers()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    timer = threading.Timer(args.seconds, server.shutdown); timer.start()
    print('Loopback schema probe ready', flush=True)
    try:
        server.serve_forever()
    finally:
        timer.cancel(); server.server_close()


if __name__ == '__main__':
    main()
