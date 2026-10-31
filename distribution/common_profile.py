#!/usr/bin/env python3
"""Preview/apply the pinned local common profile, preserving vendor caches and hooks.

This is a deployment for the audited workstation, not a package downloader.
--apply refuses missing or changed inputs. Backups include original settings;
the installation receipt lists every created link and the filtered plugin.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import os

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
PROFILE = ROOT / 'distribution/profiles/common-general-sw.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(source):
    return Path(source.replace('$REPO', str(ROOT))).expanduser()


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + '.common-tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    rows = json.loads(PROFILE.read_text())['skills']
    assert len(rows) == len({r['id'] for r in rows}) == 36
    assert sum(r['required'] for r in rows) == 8
    for row in rows:
        if digest(resolve(row['source'])/'SKILL.md') != row['sha256']:
            raise SystemExit('Source changed; review and repin: ' + row['id'])
    settings_path = HOME/'.claude/settings.json'
    settings_original = settings_path.read_text()
    settings = json.loads(settings_original)
    installed = json.loads((HOME/'.claude/plugins/installed_plugins.json').read_text())['plugins']
    ecc = Path(installed['ecc@ecc'][0]['installPath'])
    filtered = HOME/'.claude/skills/ecc'
    native_claude = {'docx', 'pdf', 'skill-creator', 'humanize-korean', 'prefer-gh-for-github'}
    links = []
    for agent, base in [('claude', HOME/'.claude/skills'), ('opencode', HOME/'.config/opencode/skills'),
                        ('antigravity', HOME/'.gemini/antigravity-cli/skills'), ('codex', HOME/'.codex/skills')]:
        for row in rows:
            name = row['id']
            if agent == 'codex' and name != 'herdr-orchestrate':
                continue
            if agent == 'claude' and (name.startswith(('ecc:', 'ponytail:')) or name in native_claude):
                continue
            dest, source = base/row['directory'], resolve(row['source'])
            if dest.exists() or dest.is_symlink():
                if not (dest/'SKILL.md').exists():
                    raise SystemExit('Broken existing skill: ' + str(dest))
                # Preserve independently installed packages when their entry point matches.
                if digest(dest/'SKILL.md') != row['sha256']:
                    raise SystemExit('Existing skill differs; review before replacing: ' + str(dest))
            else:
                links.append((dest, source))
    selected_ecc = {r['directory'] for r in rows if r['id'].startswith('ecc:')}
    if filtered.exists() and not (filtered/'.common-profile.json').exists():
        raise SystemExit('Unmanaged filtered plugin already exists')
    settings.setdefault('enabledPlugins', {})['ecc@ecc'] = False
    settings['enabledPlugins']['ecc@skills-dir'] = False
    settings['enabledPlugins']['ecc-common@skills-dir'] = True
    settings['enabledPlugins']['web-slides@hh-claude-kit'] = False
    overrides = settings.setdefault('skillOverrides', {})
    # Synced packages are preserved; only the three selected native alternatives remain exposed.
    for path in (HOME/'.claude/skills/synced').glob('*/*/SKILL.md'):
        name = path.parent.name
        if name not in ('docx', 'pdf'):
            overrides['anthropic-skills:' + name] = 'off'
    overrides['anthropic-skills:skill-creator'] = 'off'
    oc_path = HOME/'.config/opencode/opencode.json'
    oc_original = oc_path.read_text()
    oc = json.loads(oc_original)
    oc.setdefault('model', 'llm-server/Qwen3.8-Flash-Next-IQ3_S')
    # An exact allowlist of third-party skills; built-in operational tools remain separate.
    rules = [r for r in oc.get('permissions', []) if r.get('action') != 'skill']
    rules += [{'action':'skill', 'resource':'*', 'effect':'deny'}]
    rules += [{'action':'skill', 'resource':r['directory'], 'effect':'allow'} for r in rows]
    rules += [{'action':'skill', 'resource':name, 'effect':'allow'} for name in ('opencode', 'report')]
    oc['permissions'] = rules
    plan = {'profile': 'common-general-sw', 'common_selected':len(rows), 'links_to_create':len(links),
            'claude_ecc_selected':len(selected_ecc), 'claude_ecc_hooks':'preserved once; original plugin off',
            'claude_native_alternatives':sorted(native_claude), 'filtered_plugin_exists':filtered.exists(),
            'action':'apply' if args.apply else 'preview'}
    print(json.dumps(plan, ensure_ascii=False))
    if not args.apply:
        return
    if settings_path.read_text() != settings_original or oc_path.read_text() != oc_original:
        raise SystemExit('Config changed during preview; retry after reviewing the current settings')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup = HOME/'.local/share/agent-skills'/('common-backup-' + stamp)
    backup.mkdir(parents=True, mode=0o700)
    receipt = {'profile_sha256':digest(PROFILE), 'created_links':[], 'settings':[],
               'filtered_plugin':str(filtered), 'upstream_ecc':str(ecc), 'native_alternatives':sorted(native_claude)}
    instruction_paths = [HOME/'.codex/AGENTS.md', HOME/'.claude/CLAUDE.md', HOME/'.gemini/GEMINI.md', HOME/'.config/opencode/AGENTS.md']
    for path in (settings_path, oc_path, *instruction_paths):
        target = backup/(path.parent.name + '-' + path.name)
        shutil.copy2(path, target); target.chmod(0o600)
        receipt['settings'].append({'path':str(path), 'backup':str(target), 'before_sha256':digest(path)})
    # Full supporting tree, including non-selected skills' hook helpers, is retained.
    # Only their SKILL.md discovery entry points and legacy commands are omitted.
    if not filtered.exists():
        def ignore(directory, names):
            relative = Path(directory).relative_to(ecc)
            skip = {'.git', 'node_modules'} & set(names)
            if relative == Path('.'):
                skip |= {'commands', '.mcp.json'} & set(names)
            if 'SKILL.md' in names and not (len(relative.parts)==2 and relative.parts[0]=='skills' and relative.parts[1] in selected_ecc):
                skip.add('SKILL.md')
            return skip
        staging = backup/'ecc-staging'
        shutil.copytree(ecc, staging, ignore=ignore)
        manifest = json.loads((staging/'.claude-plugin/plugin.json').read_text())
        manifest['name'] = 'ecc-common'
        manifest['commands'] = []
        manifest['description'] = 'Locally filtered ECC 2.2.3: 13 selected skills; original hooks/support and agents preserved.'
        write_json(staging/'.claude-plugin/plugin.json', manifest)
        write_json(staging/'.common-profile.json', {'upstream':str(ecc),'selected':sorted(selected_ecc), 'hooks_sha256':digest(ecc/'hooks/hooks.json')})
        assert digest(staging/'hooks/hooks.json') == digest(ecc/'hooks/hooks.json')
        assert len(list(staging.rglob('SKILL.md'))) == 13
        staging.rename(filtered)
    # An installed disabled plugin still reserves its name in Claude's loader.
    manifest_path = filtered/'.claude-plugin/plugin.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['name'] = 'ecc-common'
    write_json(manifest_path, manifest)
    for dest, source in links:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(source, target_is_directory=True)
        receipt['created_links'].append({'path':str(dest),'target':str(source)})
    # Existing plugin userConfig retains its namespace; copy config to the local plugin key too.
    config = settings.get('pluginConfigs', {})
    if 'ecc@ecc' in config:
        config['ecc-common@skills-dir'] = config['ecc@ecc']
    write_json(settings_path, settings)
    write_json(oc_path, oc)
    common = (ROOT/'instructions/common.md').read_text()
    block = re.search(r'<!-- BEGIN skill-runtime -->.*?<!-- END skill-runtime -->', common, re.S).group()
    for path in instruction_paths:
        old = path.read_text()
        new = re.sub(r'<!-- BEGIN skill-runtime -->.*?<!-- END skill-runtime -->', lambda _:block, old, flags=re.S)
        if new == old and '<!-- BEGIN skill-runtime -->' not in old:
            new = old.rstrip()+'\n\n'+block+'\n'
        path.write_text(new)
    for row in receipt['settings']:
        row['after_sha256'] = digest(Path(row['path']))
    write_json(backup/'receipt.json', receipt)
    print(json.dumps({'backup':str(backup), 'created_links':len(links), 'filtered_skill_count':13}))


if __name__ == '__main__':
    main()
