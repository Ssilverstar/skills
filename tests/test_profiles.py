import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'distribution/codex_profile.py'


class ProfileSafety(unittest.TestCase):
    def test_apply_idempotence_and_guarded_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / 'config.toml'
            original = b'# Keep my comment\nmodel = "example"\n[plugins."example@test"]\nenabled = true\n'
            config.write_bytes(original)
            env = dict(os.environ, CODEX_HOME=directory)

            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                                      capture_output=True, text=True)

            preview = run()
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(config.read_bytes(), original)
            applied = run('--apply')
            self.assertEqual(applied.returncode, 0, applied.stderr)
            backup = json.loads(applied.stdout)['backup']
            updated = config.read_bytes()
            self.assertIn(original.rstrip(), updated)
            self.assertFalse(json.loads(run('--apply').stdout)['changed'])
            config.write_bytes(updated + b'# later edit\n')
            self.assertNotEqual(run('--restore', backup).returncode, 0)
            self.assertTrue(config.read_bytes().endswith(b'# later edit\n'))
            config.write_bytes(updated)
            self.assertEqual(run('--restore', backup).returncode, 0)
            self.assertEqual(config.read_bytes(), original)

    def test_existing_override_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.toml'
            original = b'[[skills.config]]\nname = "graft"\nenabled = false\n'
            config.write_bytes(original)
            result = subprocess.run([sys.executable, str(SCRIPT), '--apply'],
                                    env=dict(os.environ, CODEX_HOME=directory), capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_bytes(), original)

    def test_list_and_shared_exclusions_match(self):
        result = subprocess.run([sys.executable, str(ROOT / 'distribution/render_skill_list.py'), '--check'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        codex = json.loads((ROOT / 'distribution/profiles/codex-general-sw.json').read_text())
        opencode = json.loads((ROOT / 'distribution/profiles/opencode-general-sw.json').read_text())
        expected = {n.split(':', 1)[1] for n in codex['disabled'] if n.startswith('superpowers:')}
        self.assertEqual({r['resource'] for r in opencode['permissions']}, expected)
        required = {n.split(':')[-1] for n in codex['user_required']}
        self.assertEqual(len(required), 8)
        self.assertFalse(required & expected)


if __name__ == '__main__':
    unittest.main()
