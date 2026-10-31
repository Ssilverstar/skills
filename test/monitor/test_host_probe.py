"""Accounting regression tests use synthetic data, never private transcripts."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import host_probe as probe
from agy_statusline import sanitize
from claude_statusline import sanitize as sanitize_claude


class AccountingTests(unittest.TestCase):
    def test_mcp_inventory_hides_credentials_and_invalidates_changed_command(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'distribution/profiles').mkdir(parents=True)
            (root/'distribution/profiles/common-mcp.json').write_text(json.dumps({'servers': {'git': {}}}))
            (root/'test/results').mkdir(parents=True)
            config = {'mcpServers': {'git': {'command': 'server', 'args': ['repo'],
                        'env': {'TOKEN': 'PRIVATE_TOKEN'}, 'headers': {'Authorization': 'PRIVATE_AUTH'}}}}
            (root/'.claude.json').write_text(json.dumps(config))
            with patch.object(probe, 'ROOT', root), patch.object(probe, 'HOME', root):
                fingerprint = probe.mcp_fingerprint(['server', 'repo'])
                report = {'agents': [{'agent': 'claude', 'servers': [{'name': 'git',
                    'config_fingerprint': fingerprint, 'status': 'connected', 'tool_count': 12,
                    'checked_at': '2026-01-01T00:00:00Z'}]}]}
                (root/'test/results/common-mcp.json').write_text(json.dumps(report))
                result = probe.mcp_inventory()
                claude = next(a for a in result['agents'] if a['agent'] == 'claude')
                self.assertEqual(claude['servers'][0]['status'], 'connected')
                self.assertNotIn('PRIVATE', json.dumps(result))
                config['mcpServers']['git']['args'] = ['different-repo']
                (root/'.claude.json').write_text(json.dumps(config))
                changed = next(a for a in probe.mcp_inventory()['agents'] if a['agent'] == 'claude')
                self.assertEqual(changed['servers'][0]['status'], 'configured')
                self.assertIsNone(changed['servers'][0]['checked_at'])

    def test_claude_quota_observer_preserves_zero_and_drops_private_fields(self):
        row = sanitize_claude({'email':'PRIVATE', 'transcript_path':'PRIVATE',
            'rate_limits':{'five_hour':{'used_percentage':0,'resets_at':1794011379},
                           'seven_day':{'used_percentage':12},'unknown':{'used_percentage':99}}})
        self.assertEqual(len(row['limits']), 2)
        self.assertEqual(row['limits'][0]['used_percent'], 0)
        self.assertNotIn('PRIVATE', json.dumps(row))

    def test_antigravity_statusline_drops_identity_and_content(self):
        row = sanitize({'conversation_id':'private-id','email':'secret@example.com',
            'conversation_title':'PRIVATE', 'model':{'id':'gemini'},
            'context_window':{'total_input_tokens':100,'total_output_tokens':20}})
        self.assertEqual(row['usage']['total_tokens'], 120)
        for secret in ('private-id','secret@example.com','PRIVATE'):
            self.assertNotIn(secret, json.dumps(row))
        self.assertIsNone(sanitize({'session_id':'s','context_window':{'total_input_tokens':float('nan'),'total_output_tokens':0}}))

    def test_cache_and_reasoning_are_not_double_counted(self):
        self.assertEqual(probe.clean_usage({'input_tokens': 100, 'cached_input_tokens': 80,
            'output_tokens': 20, 'reasoning_output_tokens': 10}, 'codex')['total_tokens'], 120)
        value = probe.clean_usage({'input_tokens': 10, 'cache_read_input_tokens': 80,
            'cache_creation_input_tokens': 10, 'output_tokens': 20}, 'claude')
        self.assertEqual((value['input_tokens'], value['total_tokens']), (100, 120))

    def test_multi_model_session_is_one_agent_session(self):
        rows, usage, latest = probe.aggregate([
            ('a', 's1', '2026-01-01', probe.clean_usage({'input_tokens': 10}, 'codex')),
            ('b', 's1', '2026-01-02', probe.clean_usage({'input_tokens': 20}, 'codex'))])
        self.assertEqual(usage['sessions'], 1)
        self.assertEqual(usage['total_tokens'], 30)
        self.assertEqual(sum(x['sessions'] for x in rows), 2)

    def test_claude_streamed_message_and_skill_call_deduplication(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            p = home / '.claude/projects/project/session.jsonl'
            p.parent.mkdir(parents=True)
            rows = []
            for output in [4, 8, 6]:
                rows.append({'type': 'assistant', 'timestamp': '2026-01-01T00:00:00Z',
                    'sessionId': 's1', 'message': {'id': 'm1', 'model': 'model-a',
                    'usage': {'input_tokens': 10, 'cache_read_input_tokens': 20, 'output_tokens': output},
                    'content': [{'type': 'tool_use', 'name': 'Skill', 'id': 't1',
                                 'input': {'skill': 'ponytail-help'}}, {'type': 'text', 'text': 'PRIVATE_SENTINEL'}]}})
            p.write_text('\n'.join(map(json.dumps, rows)))
            records, skills = probe.claude_usage(home)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0][3]['total_tokens'], 38)
            self.assertEqual(len(skills), 1)
            self.assertNotIn('PRIVATE_SENTINEL', json.dumps([records, skills]))

    def test_codex_uses_request_records_instead_of_repeated_events(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            p = home / '.codex/sessions/s.jsonl'; p.parent.mkdir(parents=True)
            rows = [{'type': 'turn_context', 'payload': {'model': 'm'}}]
            for _ in range(3):
                rows.append({'type': 'event_msg', 'payload': {'type': 'token_count',
                    'info': {'total_token_usage': {'total_tokens': 99}, 'last_token_usage': {'input_tokens': 99}}}})
                rows.append({'type': 'token_usage_record', 'timestamp': '2026-01-01',
                    'payload': {'response_id': 'r1', 'usage': {'input_tokens': 10, 'output_tokens': 2}}})
            p.write_text('\n'.join(map(json.dumps, rows)))
            records, _ = probe.codex_usage(home)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0][3]['total_tokens'], 12)

    def test_opencode_v2_embedded_skill_and_token_accounting(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td); p = home/'.local/share/opencode/opencode.db'; p.parent.mkdir(parents=True)
            with sqlite3.connect(p) as db:
                db.execute('CREATE TABLE session_message (session_id, time_updated, type, data)')
                db.execute('CREATE TABLE session_part (type, time_updated, data)')
                data = {'model': {'id': 'qwen'}, 'tokens': {'input': 10, 'output': 5, 'cache': {'read': 20}},
                        'content': [{'type': 'tool', 'name': 'skill', 'state': {'status': 'completed', 'input': {'id': 'ponytail-help'}}}]}
                db.execute('INSERT INTO session_message VALUES (?,?,?,?)', ('s', 1000000000001, 'assistant', json.dumps(data)))
            records, skills = probe.opencode_usage(home)
            self.assertEqual(records[0][3]['total_tokens'], 35)
            self.assertEqual(skills[0][0], 'ponytail-help')

    def test_gpu_na_is_not_zero_and_empty_usage_is_unknown(self):
        self.assertIsNone(probe.num('[N/A]'))
        self.assertIsNone(probe.num('NaN'))
        self.assertEqual(probe.num('0'), 0)
        self.assertIsNone(probe.aggregate([])[1]['total_tokens'])

    def test_atomic_snapshot_replaces_previous_json(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'spool/snapshot.json'
            probe.write_snapshot(p, {'n': 1})
            probe.write_snapshot(p, {'n': 2})
            self.assertEqual(json.loads(p.read_text()), {'n': 2})
            self.assertFalse(p.with_suffix('.tmp').exists())


if __name__ == '__main__':
    unittest.main()
