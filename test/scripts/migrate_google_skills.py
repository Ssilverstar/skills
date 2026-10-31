#!/usr/bin/env python3
"""Link existing user skills into Antigravity CLI; preview by default."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
home = Path.home()
source = home / '.gemini/skills'
target = home / '.gemini/antigravity-cli/skills'
pairs = [(p, target / p.name) for p in sorted(source.iterdir()) if (p / 'SKILL.md').is_file()]
required = {'graft', 'archify', 'herdr', 'ponytail', 'ponytail-audit', 'ponytail-debt',
            'ponytail-gain', 'ponytail-help', 'ponytail-review'}
assert required <= {src.name for src, _ in pairs}, 'Required source missing'
for src, dst in pairs:
    if dst.exists() or dst.is_symlink():
        assert dst.is_symlink() and dst.resolve() == src.resolve(), f'Conflict: {dst.name}'
if args.apply:
    target.mkdir(parents=True, exist_ok=True)
    for src, dst in pairs:
        if not dst.is_symlink():
            dst.symlink_to(src.resolve(), target_is_directory=True)
print(json.dumps({'action': 'applied' if args.apply else 'preview', 'count': len(pairs),
                  'names': [src.name for src, _ in pairs],
                  'source_preserved': True, 'target': '~/.gemini/antigravity-cli/skills'}, indent=2))
