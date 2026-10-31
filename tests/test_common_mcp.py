import importlib.util
import json
from pathlib import Path
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mcp_profile', ROOT/'distribution/mcp_profile.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class CommonConfiguration(unittest.TestCase):
    def test_codex_merge_preserves_unrelated_config_and_removes_old_secret_table(self):
        original='''model = "example"
[mcp_servers.github]
command = "old"
[mcp_servers.github.env]
GITHUB_TOKEN = "SYNTHETIC_OLD_SECRET"
[mcp_servers.other]
url = "https://example.invalid/mcp"
[otel]
exporter = "none"
[[skills.config]]
name = "unused"
enabled = false
'''
        commands={n:['python3','/example/launcher.py',n] for n in module.NAMES}
        result=module.render_codex(original,commands)
        parsed=tomllib.loads(result)
        self.assertNotIn('SYNTHETIC_OLD_SECRET',result)
        self.assertEqual(parsed['mcp_servers']['other'],{'url':'https://example.invalid/mcp'})
        self.assertEqual(parsed['otel'],{'exporter':'none'})
        self.assertFalse(parsed['skills']['config'][0]['enabled'])
        self.assertEqual(module.render_codex(result,commands),result)

    def test_common_selection_matches_codex_and_required_skills(self):
        common=json.loads((ROOT/'distribution/profiles/common-general-sw.json').read_text())['skills']
        codex=json.loads((ROOT/'distribution/profiles/codex-general-sw.json').read_text())
        self.assertEqual({r['id'] for r in common},set(codex['enabled']))
        self.assertEqual(len({r['directory'] for r in common}),36)
        self.assertEqual({r['id'] for r in common if r['required']},set(codex['user_required']))


if __name__=='__main__':unittest.main()
