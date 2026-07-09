#!/usr/bin/env python3
"""Marketplace-style installer for listing, installing, updating, and rolling back skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
MARKETPLACE = ROOT / "marketplace" / "manifest.json"
INDEX = ROOT / "marketplace" / "index.json"
GRAPH = ROOT / "graphs" / "skill_graph.json"
PLATFORM_ALIASES = {
    "hermes": "hermes",
    "claude": "claude-code",
    "claude-code": "claude-code",
    "codex": "codex",
    "cursor": "cursor",
}


def load_json(path: Path) -> Any:
    if not path.exists():
        raise ValueError(f"missing file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    registry = load_json(REGISTRY)
    marketplace = load_json(MARKETPLACE)
    if marketplace.get("version") != registry.get("version"):
        raise ValueError("marketplace manifest version must match registry version")
    return registry


def load_index() -> dict[str, Any]:
    registry = load_registry()
    index = load_json(INDEX)
    if index.get("version") != registry.get("version"):
        raise ValueError("marketplace index version must match registry version")
    indexed = {entry["name"] for entry in index.get("skills", [])}
    registered = {entry["name"] for entry in registry["skills"]}
    if indexed != registered:
        raise ValueError(f"marketplace index skills do not match registry: {sorted(indexed ^ registered)}")
    return index


def select_skills(registry: dict[str, Any], skill_name: str | None) -> list[dict[str, Any]]:
    skills = registry["skills"]
    if skill_name is None:
        return skills
    selected = [entry for entry in skills if entry["name"] == skill_name]
    if not selected:
        raise ValueError(f"unknown skill: {skill_name}")
    return selected


def platform_id(value: str) -> str:
    if value not in PLATFORM_ALIASES:
        raise ValueError(f"unsupported platform: {value}")
    return PLATFORM_ALIASES[value]


def target_base(home: Path, platform: str) -> Path:
    if platform == "hermes":
        return home / ".hermes" / "skills"
    if platform == "claude-code":
        return home / ".claude" / "skills"
    if platform == "codex":
        return home / ".codex" / "skills"
    if platform == "cursor":
        return home / ".cursor" / "skills"
    raise ValueError(f"unsupported platform: {platform}")


def skill_destination(base: Path, platform: str, entry: dict[str, Any]) -> Path:
    if platform == "hermes":
        return base / entry.get("category", "meta") / entry["name"]
    return base / entry["name"]


def backup_root(home: Path, platform: str, skill: str) -> Path:
    return home / ".our-skills-backups" / platform / skill


def copy_skill(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frontmatter(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not path.exists():
        return fields
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return fields
    block = content.split("---", 2)[1]
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields


def file_map(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }


def preview_diff(source: Path, dest: Path) -> None:
    source_files = file_map(source)
    dest_files = file_map(dest)
    print(f"[DIFF] {source} -> {dest}")
    changes = False
    for rel in sorted(set(source_files) | set(dest_files)):
        before = dest_files.get(rel)
        after = source_files.get(rel)
        if before is None:
            print(f"  + {rel}")
            changes = True
        elif after is None:
            print(f"  - {rel}")
            changes = True
        elif before != after:
            print(f"  M {rel}")
            changes = True
    if not changes:
        print("  = no file changes")


def audit_log(home: Path) -> Path:
    return home / ".our-skills-audit" / "events.jsonl"


def write_audit(home: Path, event: dict[str, Any]) -> None:
    log = audit_log(home)
    log.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z", **event}
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")


def latest_audit_event(home: Path, platform: str, skill: str) -> dict[str, Any] | None:
    log = audit_log(home)
    if not log.exists():
        return None
    latest: dict[str, Any] | None = None
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("platform") == platform and event.get("skill") == skill and event.get("action") in {"install", "update"}:
            latest = event
    return latest


def backup_existing(home: Path, platform: str, dest: Path, skill: str) -> Path | None:
    if not dest.exists():
        return None
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup = backup_root(home, platform, skill) / stamp
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(dest), str(backup))
    return backup


def latest_backup(home: Path, platform: str, skill: str) -> Path | None:
    root = backup_root(home, platform, skill)
    if not root.exists():
        return None
    backups = sorted(path for path in root.iterdir() if path.is_dir())
    return backups[-1] if backups else None


def command_list(registry: dict[str, Any]) -> int:
    index = load_index()
    print(f"{registry['project']} {registry['version']}")
    for entry in index["skills"]:
        score = entry["quality"]["score"]
        print(f"{entry['name']}\t{entry['version']}\t{entry['category']}\t{entry['status']}\t{score:.0f}\t{entry['summary']}")
    return 0


def graph_dependencies() -> dict[str, list[str]]:
    graph = load_json(GRAPH)
    deps: dict[str, set[str]] = defaultdict(set)
    for edge in graph.get("edges", []):
        if edge.get("type") == "hard":
            deps[edge["from"]].add(edge["to"])
    return {name: sorted(values) for name, values in deps.items()}


def doctor_line(kind: str, message: str) -> None:
    print(f"[{kind}] {message}")


def command_doctor(args: argparse.Namespace) -> int:
    registry = load_registry()
    index = load_index()
    platform = platform_id(args.platform)
    home = Path(args.target_root).expanduser().resolve()
    base = target_base(home, platform)
    skills = select_skills(registry, args.skill)
    deps = graph_dependencies()
    indexed = {entry["name"]: entry for entry in index["skills"]}
    issue_count = 0

    doctor_line("OK", f"registry {registry['version']} and marketplace index are synchronized")
    doctor_line("OK", f"platform {platform} target base is {base}")

    for entry in skills:
        name = entry["name"]
        source = ROOT / entry["path"]
        source_skill = source / "SKILL.md"
        dest = skill_destination(base, platform, entry)
        dest_skill = dest / "SKILL.md"
        indexed_entry = indexed[name]
        print(f"\n{name}")

        if entry.get("deprecated"):
            issue_count += 1
            doctor_line("WARN", f"deprecated; replaced_by={entry.get('replaced_by')} migration_path={entry.get('migration_path')}")
        else:
            doctor_line("OK", f"status={entry.get('status', 'active')} owner={entry.get('owner', 'core-platform')}")

        if not source_skill.exists():
            issue_count += 1
            doctor_line("FAIL", f"source missing {source_skill}")
            continue
        source_fm = frontmatter(source_skill)
        if source_fm.get("name") != name:
            issue_count += 1
            doctor_line("FAIL", f"source frontmatter name {source_fm.get('name')} does not match registry")
        elif source_fm.get("version") != entry.get("version"):
            issue_count += 1
            doctor_line("FAIL", f"source frontmatter version {source_fm.get('version')} does not match registry {entry.get('version')}")
        else:
            doctor_line("OK", f"source {entry['path']}/SKILL.md matches registry metadata")

        description = source_fm.get("description", "")
        if len(description) < 20:
            issue_count += 1
            doctor_line("WARN", "description is short; trigger discovery may be weak")
        else:
            doctor_line("OK", "trigger description is present")

        missing_deps = [dep for dep in deps.get(name, []) if dep not in indexed]
        if missing_deps:
            issue_count += 1
            doctor_line("FAIL", f"dependencies missing from index: {', '.join(missing_deps)}")
        else:
            doctor_line("OK", f"dependencies={', '.join(deps.get(name, [])) or 'none'}")

        platform_paths = {row["id"]: row["install_path"] for row in indexed_entry["platforms"]}
        doctor_line("OK", f"expected platform path {platform_paths[platform]}")

        if not dest_skill.exists():
            issue_count += 1
            doctor_line("WARN", f"not installed at {dest_skill}")
            continue
        dest_fm = frontmatter(dest_skill)
        if dest_fm.get("name") != name:
            issue_count += 1
            doctor_line("FAIL", f"installed frontmatter name {dest_fm.get('name')} does not match {name}")
        elif dest_fm.get("version") != entry.get("version"):
            issue_count += 1
            doctor_line("FAIL", f"installed version {dest_fm.get('version')} does not match registry {entry.get('version')}")
        else:
            doctor_line("OK", f"installed at {dest_skill}")

    if args.strict and issue_count:
        doctor_line("FAIL", f"doctor found {issue_count} issue(s)")
        return 1
    doctor_line("OK", f"doctor completed with {issue_count} issue(s)")
    return 0


def command_install_or_update(args: argparse.Namespace, update: bool) -> int:
    registry = load_registry()
    platform = platform_id(args.platform)
    home = Path(args.target_root).expanduser().resolve()
    base = target_base(home, platform)
    skills = select_skills(registry, args.skill)
    action = "UPDATE" if update else "INSTALL"
    write_enabled = args.apply and not args.dry_run

    for entry in skills:
        source = ROOT / entry["path"]
        dest = skill_destination(base, platform, entry)
        if not (source / "SKILL.md").exists():
            raise ValueError(f"source missing SKILL.md: {source}")
        preview_diff(source, dest)
        if not write_enabled:
            print(f"[DRY-RUN] {action} {entry['name']} -> {dest}")
            continue
        if dest.exists():
            backup = backup_existing(home, platform, dest, entry["name"])
            print(f"[BACKUP] {dest} -> {backup}")
            rollback_mode = "restore_backup"
        else:
            backup = None
            rollback_mode = "remove_created_dest"
        copy_skill(source, dest)
        print(f"[OK] {entry['name']} -> {dest}")
        write_audit(
            home,
            {
                "action": action.lower(),
                "platform": platform,
                "skill": entry["name"],
                "source": str(source),
                "destination": str(dest),
                "backup": str(backup) if backup else None,
                "rollback_mode": rollback_mode,
            },
        )
    return 0


def command_rollback(args: argparse.Namespace) -> int:
    if not args.skill:
        raise ValueError("rollback requires --skill")
    registry = load_registry()
    platform = platform_id(args.platform)
    home = Path(args.target_root).expanduser().resolve()
    base = target_base(home, platform)
    entry = select_skills(registry, args.skill)[0]
    dest = skill_destination(base, platform, entry)
    event = latest_audit_event(home, platform, entry["name"])
    backup = Path(event["backup"]) if event and event.get("backup") else latest_backup(home, platform, entry["name"])
    rollback_mode = event.get("rollback_mode") if event else ("restore_backup" if backup else None)
    if rollback_mode is None:
        raise ValueError(f"no rollback backup found for {entry['name']} on {platform}")
    write_enabled = args.apply and not args.dry_run
    if not write_enabled:
        if rollback_mode == "remove_created_dest":
            print(f"[DRY-RUN] ROLLBACK remove created target {dest}")
        else:
            print(f"[DRY-RUN] ROLLBACK {backup} -> {dest}")
        return 0
    if rollback_mode == "remove_created_dest":
        if dest.exists():
            shutil.rmtree(dest)
        print(f"[OK] rolled back {entry['name']} by removing created target {dest}")
    else:
        if backup is None or not backup.exists():
            raise ValueError(f"rollback backup missing for {entry['name']}: {backup}")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(backup, dest)
        print(f"[OK] rolled back {entry['name']} from {backup}")
    write_audit(
        home,
        {
            "action": "rollback",
            "platform": platform,
            "skill": entry["name"],
            "destination": str(dest),
            "backup": str(backup) if backup else None,
            "rollback_mode": rollback_mode,
        },
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List installable skills")

    for command in ("install", "update"):
        child = sub.add_parser(command, help=f"{command} one or all skills")
        child.add_argument("--platform", required=True, choices=sorted(PLATFORM_ALIASES))
        child.add_argument("--target-root", default=str(Path.home()), help="Home-like root containing .codex/.claude/.hermes/.cursor")
        child.add_argument("--skill", help="Install only one skill; defaults to all")
        child.add_argument("--dry-run", action="store_true", help="Preview only; this is also the default")
        child.add_argument("--apply", action="store_true", help="Write changes after showing the diff preview")

    rollback = sub.add_parser("rollback", help="Restore the latest marketplace backup for a skill")
    rollback.add_argument("--platform", required=True, choices=sorted(PLATFORM_ALIASES))
    rollback.add_argument("--target-root", default=str(Path.home()), help="Home-like root containing backup data")
    rollback.add_argument("--skill", required=True)
    rollback.add_argument("--dry-run", action="store_true", help="Preview only; this is also the default")
    rollback.add_argument("--apply", action="store_true", help="Write rollback changes")

    doctor = sub.add_parser("doctor", help="Diagnose source, platform paths, dependencies, and installed skills")
    doctor.add_argument("--platform", required=True, choices=sorted(PLATFORM_ALIASES))
    doctor.add_argument("--target-root", default=str(Path.home()), help="Home-like root containing .codex/.claude/.hermes/.cursor")
    doctor.add_argument("--skill", help="Diagnose only one skill; defaults to all")
    doctor.add_argument("--strict", action="store_true", help="Return non-zero when warnings or failures are found")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "list":
            return command_list(load_registry())
        if args.command == "install":
            return command_install_or_update(args, update=False)
        if args.command == "update":
            return command_install_or_update(args, update=True)
        if args.command == "rollback":
            return command_rollback(args)
        if args.command == "doctor":
            return command_doctor(args)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
