#!/usr/bin/env python3
"""Preview/apply the reviewed Codex profile, or restore its exact config backup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
import tomllib

PROFILE = Path(__file__).parent / "profiles/codex-general-sw.json"
BEGIN = "# BEGIN managed codex-general-sw profile"
END = "# END managed codex-general-sw profile"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode):
    fd, temporary = tempfile.mkstemp(prefix=".skill-profile-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--restore", type=Path, metavar="BACKUP_DIRECTORY")
    args = parser.parse_args()
    codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config = codex_root / "config.toml"
    original = config.read_bytes()
    mode = config.stat().st_mode & 0o777

    if args.restore:
        record = json.loads((args.restore / "record.json").read_text())
        if str(config.resolve()) != record["config"]:
            raise SystemExit("Backup belongs to a different config path")
        if digest(original) != record["after_sha256"]:
            raise SystemExit("Config changed after apply; restore manually to preserve later edits")
        previous = (args.restore / "config.toml").read_bytes()
        if digest(previous) != record["before_sha256"]:
            raise SystemExit("Backup checksum mismatch")
        atomic_write(config, previous, mode)
        print(json.dumps({"restored": str(config)}))
        return

    profile = json.loads(PROFILE.read_text())
    enabled, disabled = profile["enabled"], profile["disabled"]
    if len(set(enabled + disabled)) != len(enabled + disabled):
        raise SystemExit("Duplicate or conflicting profile entries")
    if not set(profile.get("user_required", [])).issubset(enabled):
        raise SystemExit("User-required skills must stay in the enabled list")
    text = original.decode()
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise SystemExit("Invalid managed section markers")
        start, finish = text.index(BEGIN), text.index(END) + len(END)
        if finish <= start:
            raise SystemExit("Invalid managed section order")
        text = text[:start] + text[finish:].lstrip("\n")
    existing = tomllib.loads(text)
    targets = set(enabled + disabled)
    for entry in existing.get("skills", {}).get("config", []):
        if entry.get("name") in targets or entry.get("path"):
            raise SystemExit("Existing skill overrides need review; no settings changed")

    lines = [BEGIN, "# Source: distribution/profiles/codex-general-sw.json"]
    for name in disabled:
        lines.extend(["[[skills.config]]", "name = " + json.dumps(name), "enabled = false", ""])
    lines.append(END)
    updated = (text.rstrip() + "\n\n" + "\n".join(lines) + "\n").encode()
    parsed = tomllib.loads(updated.decode())
    assert all(any(e.get("name") == name and e["enabled"] is False
                   for e in parsed["skills"]["config"]) for name in disabled)
    # Every pre-existing setting other than the new skills block is preserved.
    assert {k: v for k, v in parsed.items() if k != "skills"} == {
        k: v for k, v in existing.items() if k != "skills"}
    summary = {"config": str(config), "reviewed_enabled": len(enabled),
               "disabled": len(disabled), "changed": updated != original,
               "action": "apply" if args.apply else "preview"}
    if args.apply and updated != original:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = codex_root / "backups" / ("skills-general-sw-" + stamp)
        backup.mkdir(parents=True, mode=0o700)
        atomic_write(backup / "config.toml", original, 0o600)
        record = {"config": str(config.resolve()), "before_sha256": digest(original),
                  "after_sha256": digest(updated), "profile": str(PROFILE.resolve())}
        atomic_write(backup / "record.json", (json.dumps(record, indent=2) + "\n").encode(), 0o600)
        if config.read_bytes() != original:
            raise SystemExit("Config changed during preview; no settings changed")
        atomic_write(config, updated, mode)
        summary["backup"] = str(backup)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
