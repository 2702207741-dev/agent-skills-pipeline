#!/usr/bin/env python3
"""Marketplace-style installer for listing, installing, updating, and rolling back skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
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
TRANSACTION_ID_RE = re.compile(r"^[0-9]{20}-[0-9a-f]{12}$")


def load_json(path: Path) -> Any:
    if not path.exists():
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        raise ValueError(f"missing file: {display}")
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
    file_map(source)
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
    if path_is_link_like(root) or not root.is_dir():
        raise ValueError(f"file tree root must be a regular directory: {root}")

    pending = [root]
    files: list[Path] = []
    while pending:
        current = pending.pop()
        for path in current.iterdir():
            if path_is_link_like(path):
                raise ValueError(f"file tree must not contain a link or junction: {path}")
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise ValueError(f"file tree contains an unsupported entry: {path}")
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(files, key=lambda item: item.relative_to(root).as_posix())
    }


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def path_is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    junction_check = getattr(path, "is_junction", None)
    if junction_check is not None and junction_check():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def assert_no_link_components(root: Path, path: Path, label: str) -> None:
    root = root.absolute()
    path = path.absolute()
    if path_is_link_like(root):
        raise ValueError(f"{label} root must not be a link or junction: {root}")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes its allowed root: {path}") from exc
    current = root
    for part in relative.parts:
        current /= part
        if path_is_link_like(current):
            raise ValueError(f"{label} must not traverse a link or junction: {current}")


def remove_destination(path: Path) -> None:
    if path_is_link_like(path):
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()
    elif path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def assert_destination_boundary(home: Path, base: Path, destination: Path) -> None:
    assert_no_link_components(home, destination, "destination")
    resolved_home = home.resolve()
    resolved_base = base.resolve()
    resolved_parent = destination.parent.resolve()
    try:
        resolved_base.relative_to(resolved_home)
        resolved_parent.relative_to(resolved_base)
    except ValueError as exc:
        raise ValueError(f"destination escapes the target root: {destination}") from exc
def build_operation(home: Path, base: Path, platform: str, entry: dict[str, Any]) -> dict[str, Any]:
    source_path = ROOT / entry["path"]
    assert_no_link_components(ROOT, source_path, "source")
    source = source_path.resolve()
    try:
        source.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"source escapes the repository: {source_path}") from exc
    destination = skill_destination(base, platform, entry)
    assert_destination_boundary(home, base, destination)
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"source missing a regular SKILL.md: {source}")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"destination exists but is not a directory: {destination}")
    source_files = file_map(source)
    return {
        "skill": entry["name"],
        "source": str(source),
        "destination": str(destination),
        "source_files": source_files,
        "source_digest": digest_value(source_files),
        "destination_files_before": file_map(destination),
        "rollback_mode": "restore_backup" if destination.exists() else "remove_created_dest",
    }


def build_install_plan(home: Path, platform: str, entries: list[dict[str, Any]], action: str) -> dict[str, Any]:
    home = home.resolve()
    base = target_base(home, platform)
    operations = [build_operation(home, base, platform, entry) for entry in entries]
    created_at = datetime.utcnow().isoformat(timespec="microseconds") + "Z"
    seed = {"action": action, "platform": platform, "target_root": str(home), "created_at": created_at, "operations": operations}
    transaction_id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + "-" + digest_value(seed)[:12]
    plan = {
        "schema_version": 1,
        "kind": "our-skills-install-plan",
        "transaction_id": transaction_id,
        **seed,
    }
    plan["plan_sha256"] = digest_value(plan)
    return plan


def validate_install_plan(plan: dict[str, Any], action: str, platform: str, home: Path) -> None:
    if plan.get("schema_version") != 1 or plan.get("kind") != "our-skills-install-plan":
        raise ValueError("install plan schema is not recognized")
    supplied_digest = plan.get("plan_sha256")
    unsigned = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if supplied_digest != digest_value(unsigned):
        raise ValueError("install plan digest does not match its content")
    if not isinstance(plan.get("transaction_id"), str) or not TRANSACTION_ID_RE.fullmatch(plan["transaction_id"]):
        raise ValueError("install plan transaction_id is invalid")
    if plan.get("action") != action or plan.get("platform") != platform or plan.get("target_root") != str(home.resolve()):
        raise ValueError("install plan action, platform, or target root does not match the command")

    registry = load_registry()
    registered = {entry["name"]: entry for entry in registry["skills"]}
    operations = plan.get("operations")
    if not isinstance(operations, list) or not operations:
        raise ValueError("install plan needs at least one operation")
    names = [operation.get("skill") for operation in operations if isinstance(operation, dict)]
    if len(names) != len(operations) or len(names) != len(set(names)) or any(name not in registered for name in names):
        raise ValueError("install plan contains unknown or duplicate skills")
    base = target_base(home.resolve(), platform)
    for operation in operations:
        expected = build_operation(home.resolve(), base, platform, registered[operation["skill"]])
        for field in (
            "source",
            "destination",
            "source_files",
            "source_digest",
            "destination_files_before",
            "rollback_mode",
        ):
            if operation.get(field) != expected[field]:
                raise ValueError(f"install plan is stale or altered for {operation['skill']}: {field}")


def write_install_plan(plan: dict[str, Any], output: Path) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote install plan {output} sha256={plan['plan_sha256']}")


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
    assert_no_link_components(home, log, "audit log")
    log.parent.mkdir(parents=True, exist_ok=True)
    previous_digest: str | None = None
    if log.exists():
        lines = [line for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            previous = json.loads(lines[-1])
            previous_digest = previous.get("event_sha256") or hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
    event = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "previous_event_sha256": previous_digest,
        **event,
    }
    event["event_sha256"] = digest_value(event)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")


def verify_audit_chain(home: Path) -> list[str]:
    log = audit_log(home)
    if not log.exists():
        return []
    findings: list[str] = []
    previous_digest: str | None = None
    for line_number, line in enumerate(log.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            findings.append(f"audit line {line_number} is not valid JSON")
            previous_digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
            continue
        stored = event.get("event_sha256")
        if stored is None:
            previous_digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
            continue
        if event.get("previous_event_sha256") != previous_digest:
            findings.append(f"audit line {line_number} previous hash does not match")
        unsigned = {key: value for key, value in event.items() if key != "event_sha256"}
        expected = digest_value(unsigned)
        if stored != expected:
            findings.append(f"audit line {line_number} event hash does not match")
        previous_digest = stored
    return findings


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
    audit_findings = verify_audit_chain(home)
    if audit_findings:
        issue_count += len(audit_findings)
        for finding in audit_findings:
            doctor_line("FAIL", finding)
    else:
        doctor_line("OK", "audit log hash chain is valid")

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


def apply_install_plan(
    plan: dict[str, Any],
    failure_after: int | None = None,
    failure_phase: str = "install",
) -> None:
    home = Path(plan["target_root"])
    platform = plan["platform"]
    transaction_id = plan["transaction_id"]
    if failure_phase not in {"stage", "backup", "install"}:
        raise ValueError(f"unknown failure injection phase: {failure_phase}")
    validate_install_plan(plan, plan["action"], platform, home)
    staging_root = home / ".our-skills-staging" / transaction_id
    backup_base = home / ".our-skills-backups" / "transactions" / transaction_id / platform
    assert_no_link_components(home, staging_root, "transaction staging")
    assert_no_link_components(home, backup_base, "transaction backup")
    if staging_root.exists() or backup_base.exists():
        raise ValueError(f"transaction workspace already exists: {transaction_id}")

    touched: list[dict[str, Any]] = []
    try:
        for index, operation in enumerate(plan["operations"], start=1):
            staged = staging_root / operation["skill"]
            copy_skill(Path(operation["source"]), staged)
            if file_map(staged) != operation["source_files"]:
                raise ValueError(f"staged files do not match plan for {operation['skill']}")
            if failure_after is not None and failure_phase == "stage" and index >= failure_after:
                raise RuntimeError(f"injected failure during staging after {failure_after} operation(s)")

        for index, operation in enumerate(plan["operations"], start=1):
            destination = Path(operation["destination"])
            staged = staging_root / operation["skill"]
            backup = backup_base / operation["skill"] if operation["rollback_mode"] == "restore_backup" else None
            assert_destination_boundary(home, target_base(home, platform), destination)
            if file_map(destination) != operation["destination_files_before"]:
                raise ValueError(f"destination changed after plan validation for {operation['skill']}")
            touch = {"operation": operation, "destination": destination, "backup": backup}
            touched.append(touch)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if backup is not None:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(backup))
                print(f"[BACKUP] {destination} -> {backup}")
            if failure_after is not None and failure_phase == "backup" and index >= failure_after:
                raise RuntimeError(f"injected failure after backup for {failure_after} operation(s)")
            shutil.move(str(staged), str(destination))
            print(f"[OK] {operation['skill']} -> {destination}")
            if failure_after is not None and failure_phase == "install" and index >= failure_after:
                raise RuntimeError(f"injected failure after {failure_after} operation(s)")
    except Exception as exc:
        rollback_errors: list[str] = []
        for touch in reversed(touched):
            destination = touch["destination"]
            backup = touch["backup"]
            try:
                remove_destination(destination)
                if backup is not None and backup.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(backup), str(destination))
            except Exception as rollback_exc:
                rollback_errors.append(f"{touch['operation']['skill']}: {rollback_exc}")
        write_audit(
            home,
            {
                "action": "transaction_failed",
                "platform": platform,
                "transaction_id": transaction_id,
                "plan_sha256": plan["plan_sha256"],
                "error": str(exc),
                "rollback_errors": rollback_errors,
            },
        )
        detail = f"; rollback errors: {', '.join(rollback_errors)}" if rollback_errors else "; all touched destinations restored"
        raise ValueError(f"transaction {transaction_id} failed: {exc}{detail}") from exc
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)

    audit_operations = []
    for touch in touched:
        operation = touch["operation"]
        backup = touch["backup"]
        audit_operation = {
            "skill": operation["skill"],
            "source": operation["source"],
            "destination": operation["destination"],
            "backup": str(backup) if backup else None,
            "rollback_mode": operation["rollback_mode"],
            "source_digest": operation["source_digest"],
        }
        audit_operations.append(audit_operation)
        write_audit(
            home,
            {
                "action": plan["action"],
                "platform": platform,
                "transaction_id": transaction_id,
                "plan_sha256": plan["plan_sha256"],
                **audit_operation,
            },
        )
    write_audit(
        home,
        {
            "action": "transaction_commit",
            "platform": platform,
            "transaction_id": transaction_id,
            "plan_sha256": plan["plan_sha256"],
            "operations": audit_operations,
        },
    )


def command_install_or_update(args: argparse.Namespace, update: bool) -> int:
    registry = load_registry()
    platform = platform_id(args.platform)
    home = Path(args.target_root).expanduser().resolve()
    action = "update" if update else "install"
    if args.apply_plan and (args.skill or args.plan_output or args.apply or args.dry_run):
        raise ValueError("--apply-plan cannot be combined with --skill, --plan-output, --apply, or --dry-run")

    if args.apply_plan:
        plan = load_json(Path(args.apply_plan).expanduser().resolve())
        validate_install_plan(plan, action, platform, home)
        apply_install_plan(plan)
        return 0

    entries = select_skills(registry, args.skill)
    plan = build_install_plan(home, platform, entries, action)
    for operation in plan["operations"]:
        preview_diff(Path(operation["source"]), Path(operation["destination"]))
        print(f"[PLAN] {action.upper()} {operation['skill']} -> {operation['destination']}")
    print(f"[PLAN] transaction={plan['transaction_id']} sha256={plan['plan_sha256']}")
    if args.plan_output:
        write_install_plan(plan, Path(args.plan_output))
    if not args.apply or args.dry_run:
        print("[DRY-RUN] No installation files were changed")
        return 0
    validate_install_plan(plan, action, platform, home)
    apply_install_plan(plan)
    return 0


def transaction_commit_event(home: Path, transaction_id: str) -> dict[str, Any] | None:
    log = audit_log(home)
    if not log.exists():
        return None
    match = None
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("action") == "transaction_commit" and event.get("transaction_id") == transaction_id:
            match = event
    return match


def validate_transaction_operations(
    home: Path,
    platform: str,
    transaction_id: str,
    operations: Any,
) -> list[dict[str, Any]]:
    if not isinstance(operations, list) or not operations:
        raise ValueError(f"transaction has no rollback operations: {transaction_id}")
    base = target_base(home, platform)
    backup_base = home / ".our-skills-backups" / "transactions" / transaction_id / platform
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError(f"transaction contains an invalid rollback operation: {transaction_id}")
        skill = operation.get("skill")
        if not isinstance(skill, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill) or skill in seen:
            raise ValueError(f"transaction contains an invalid or duplicate skill: {skill}")
        seen.add(skill)
        destination_value = operation.get("destination")
        if not isinstance(destination_value, str):
            raise ValueError(f"transaction destination is invalid for {skill}")
        destination = Path(destination_value)
        if not destination.is_absolute() or destination.name != skill:
            raise ValueError(f"transaction destination is invalid for {skill}: {destination}")
        assert_destination_boundary(home, base, destination)
        if destination.exists():
            file_map(destination)
        rollback_mode = operation.get("rollback_mode")
        backup_value = operation.get("backup")
        if rollback_mode == "restore_backup":
            expected_backup = (backup_base / skill).absolute()
            if not isinstance(backup_value, str) or Path(backup_value).absolute() != expected_backup:
                raise ValueError(f"transaction backup path is invalid for {skill}")
            assert_no_link_components(backup_base, expected_backup, "transaction backup")
        elif rollback_mode == "remove_created_dest":
            if backup_value is not None:
                raise ValueError(f"new destination unexpectedly has a backup for {skill}")
        else:
            raise ValueError(f"transaction rollback mode is invalid for {skill}")
        validated.append(operation)
    return validated


def command_rollback_transaction(args: argparse.Namespace, home: Path, platform: str) -> int:
    if not isinstance(args.transaction, str) or not TRANSACTION_ID_RE.fullmatch(args.transaction):
        raise ValueError(f"invalid transaction id: {args.transaction}")
    audit_findings = verify_audit_chain(home)
    if audit_findings:
        raise ValueError("audit log integrity failed: " + "; ".join(audit_findings))
    event = transaction_commit_event(home, args.transaction)
    if event is None or event.get("platform") != platform:
        raise ValueError(f"unknown transaction for {platform}: {args.transaction}")
    operations = validate_transaction_operations(home, platform, args.transaction, event.get("operations"))

    base = target_base(home, platform)
    for operation in reversed(operations):
        destination = Path(operation["destination"])
        assert_destination_boundary(home, base, destination)
        if operation["rollback_mode"] == "remove_created_dest":
            print(f"[DRY-RUN] ROLLBACK remove created target {destination}")
        else:
            print(f"[DRY-RUN] ROLLBACK {operation['backup']} -> {destination}")
    if not args.apply or args.dry_run:
        return 0

    staging_root = home / ".our-skills-staging" / f"rollback-{args.transaction}"
    assert_no_link_components(home, staging_root, "rollback staging")
    if staging_root.exists():
        raise ValueError(f"rollback staging directory already exists: {staging_root}")
    snapshots: list[tuple[Path, Path | None]] = []
    changed: list[Path] = []
    try:
        for operation in operations:
            destination = Path(operation["destination"])
            snapshot = staging_root / operation["skill"] if destination.exists() else None
            if snapshot is not None:
                copy_skill(destination, snapshot)
            snapshots.append((destination, snapshot))
        for operation in reversed(operations):
            destination = Path(operation["destination"])
            remove_destination(destination)
            changed.append(destination)
            if operation["rollback_mode"] == "restore_backup":
                backup = Path(operation["backup"])
                if not backup.is_dir():
                    raise ValueError(f"transaction backup is missing: {backup}")
                copy_skill(backup, destination)
    except Exception as exc:
        restore_errors: list[str] = []
        snapshots_by_destination = {destination: snapshot for destination, snapshot in snapshots}
        for destination in reversed(changed):
            try:
                remove_destination(destination)
                snapshot = snapshots_by_destination[destination]
                if snapshot is not None and snapshot.exists():
                    copy_skill(snapshot, destination)
            except Exception as restore_exc:
                restore_errors.append(f"{destination}: {restore_exc}")
        detail = f"; restore errors: {', '.join(restore_errors)}" if restore_errors else "; pre-rollback state restored"
        raise ValueError(f"transaction rollback failed: {exc}{detail}") from exc
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)

    write_audit(
        home,
        {
            "action": "rollback_transaction",
            "platform": platform,
            "transaction_id": args.transaction,
            "source_event_sha256": event.get("event_sha256"),
            "operation_count": len(operations),
        },
    )
    print(f"[OK] rolled back transaction {args.transaction}")
    return 0


def command_rollback(args: argparse.Namespace) -> int:
    registry = load_registry()
    platform = platform_id(args.platform)
    home = Path(args.target_root).expanduser().resolve()
    if args.transaction:
        if args.skill:
            raise ValueError("rollback accepts either --skill or --transaction, not both")
        return command_rollback_transaction(args, home, platform)
    if not args.skill:
        raise ValueError("rollback requires --skill or --transaction")
    base = target_base(home, platform)
    entry = select_skills(registry, args.skill)[0]
    dest = skill_destination(base, platform, entry)
    assert_destination_boundary(home, base, dest)
    if dest.exists():
        file_map(dest)
    audit_findings = verify_audit_chain(home)
    if audit_findings:
        raise ValueError("audit log integrity failed: " + "; ".join(audit_findings))
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
        remove_destination(dest)
        print(f"[OK] rolled back {entry['name']} by removing created target {dest}")
    else:
        if backup is None or not backup.exists():
            raise ValueError(f"rollback backup missing for {entry['name']}: {backup}")
        assert_no_link_components(home / ".our-skills-backups", backup, "rollback backup")
        remove_destination(dest)
        copy_skill(backup, dest)
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
        child.add_argument("--plan-output", help="Write the content-bound installation plan as JSON")
        child.add_argument("--apply-plan", help="Apply one previously previewed plan after revalidation")

    rollback = sub.add_parser("rollback", help="Restore the latest marketplace backup for a skill")
    rollback.add_argument("--platform", required=True, choices=sorted(PLATFORM_ALIASES))
    rollback.add_argument("--target-root", default=str(Path.home()), help="Home-like root containing backup data")
    rollback.add_argument("--skill")
    rollback.add_argument("--transaction", help="Roll back every operation in a committed transaction")
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
