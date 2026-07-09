#!/usr/bin/env python3
"""Validate skills.json against the repository layout and SKILL.md metadata."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def read_frontmatter(skill_file: Path) -> dict[str, str]:
    content = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError(f"{skill_file}: missing YAML frontmatter")

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    if not REGISTRY.exists():
        print(f"[FAIL] Missing registry: {REGISTRY}")
        return 1

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ok = True
    version = registry.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        print("[FAIL] Registry project version must be valid semver")
        ok = False
    current_release = registry.get("release_policy", {}).get("current_release")
    if version and current_release != f"v{version}":
        print("[FAIL] release_policy.current_release must match project version")
        ok = False
    deprecation_policy = registry.get("deprecation_policy", {})
    status_values = set(deprecation_policy.get("status_values", []))
    if not {"active", "deprecated", "removed"}.issubset(status_values):
        print("[FAIL] deprecation_policy.status_values must include active, deprecated, and removed")
        ok = False

    skills = registry.get("skills", [])
    if not skills:
        print("[FAIL] Registry has no skills")
        return 1

    seen_names: set[str] = set()
    seen_paths: set[str] = set()

    for entry in skills:
        name = entry.get("name")
        rel_path = entry.get("path")
        skill_version = entry.get("version")
        if not name or not rel_path:
            print(f"[FAIL] Registry entry missing name/path: {entry}")
            ok = False
            continue
        if not isinstance(skill_version, str) or not SEMVER_RE.match(skill_version):
            print(f"[FAIL] {name}: registry version must be valid semver")
            ok = False
        owner = entry.get("owner")
        status = entry.get("status")
        deprecated = entry.get("deprecated")
        if not isinstance(owner, str) or not owner.strip():
            print(f"[FAIL] {name}: owner must be a non-empty string")
            ok = False
        if status not in status_values:
            print(f"[FAIL] {name}: status must be one of {sorted(status_values)}")
            ok = False
        if not isinstance(deprecated, bool):
            print(f"[FAIL] {name}: deprecated must be boolean")
            ok = False
        if deprecated and status != "deprecated":
            print(f"[FAIL] {name}: deprecated=true requires status=deprecated")
            ok = False
        if deprecated and not entry.get("migration_path"):
            print(f"[FAIL] {name}: deprecated skills require migration_path")
            ok = False
        if not deprecated and (entry.get("replaced_by") is not None or entry.get("migration_path") is not None):
            print(f"[FAIL] {name}: active skills must keep replaced_by and migration_path null")
            ok = False
        if name in seen_names:
            print(f"[FAIL] Duplicate skill name in registry: {name}")
            ok = False
        if rel_path in seen_paths:
            print(f"[FAIL] Duplicate skill path in registry: {rel_path}")
            ok = False
        seen_names.add(name)
        seen_paths.add(rel_path)

        skill_dir = ROOT / rel_path
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            print(f"[FAIL] Registry path missing SKILL.md: {rel_path}")
            ok = False
            continue

        try:
            frontmatter = read_frontmatter(skill_file)
        except ValueError as exc:
            print(f"[FAIL] {exc}")
            ok = False
            continue

        actual_name = frontmatter.get("name")
        if actual_name != name:
            print(f"[FAIL] {rel_path}: registry name '{name}' != frontmatter name '{actual_name}'")
            ok = False
        frontmatter_version = frontmatter.get("version")
        if not frontmatter_version:
            print(f"[FAIL] {rel_path}: frontmatter missing version")
            ok = False
        elif frontmatter_version != skill_version:
            print(f"[FAIL] {rel_path}: registry version '{skill_version}' != frontmatter version '{frontmatter_version}'")
            ok = False
        if skill_dir.name != name:
            print(f"[FAIL] {rel_path}: directory name '{skill_dir.name}' != registry name '{name}'")
            ok = False

    actual_skill_dirs = {
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }
    registered_dirs = {str(entry["path"]).replace("\\", "/").split("/")[-1] for entry in skills}

    missing_from_registry = sorted(actual_skill_dirs - registered_dirs)
    if missing_from_registry:
        print(f"[FAIL] Skill directories missing from registry: {', '.join(missing_from_registry)}")
        ok = False

    stale_registry_entries = sorted(registered_dirs - actual_skill_dirs)
    if stale_registry_entries:
        print(f"[FAIL] Registry entries without directories: {', '.join(stale_registry_entries)}")
        ok = False

    if ok:
        print(f"[OK] Registry matches {len(skills)} skill directories")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
