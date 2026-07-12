#!/usr/bin/env python3
"""Check whether the repository is ready for public GitHub upload."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_PUBLIC_FILE_BYTES = 50 * 1024 * 1024

REQUIRED_FILES = [
    "README.md",
    "OSS_REVIEW.md",
    "AGENTS.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CLA.md",
    ".gitignore",
    ".gitattributes",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/skill_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/action-self-test.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/scorecard.yml",
    ".github/workflows/skill-review-bot.yml",
    ".github/workflows/supply-chain.yml",
    ".github/dependabot.yml",
    ".github/secret_scanning.yml",
    "scripts/verify_release.py",
    "scripts/review_bot.py",
    "scripts/check_maintenance_evidence.py",
    "scripts/check_supply_chain.py",
    "scripts/check_external_adoption.py",
    "scripts/external_repo_check.py",
    "scripts/generate_slsa_provenance.py",
    "scripts/our_skills.py",
    "scripts/run_maintenance_demo.py",
    "action.yml",
    "our-skills",
    "our-skills.cmd",
    "scripts/check_release_archive.py",
    "docs/codex-for-oss-case-study.md",
    "docs/maintainer-workflows.md",
    "docs/quickstart.md",
    "docs/github-action.md",
    "docs/roadmap-to-ecosystem.md",
    "docs/security-review-checklist.md",
    "docs/slsa-provenance.md",
    "docs/threat-model.md",
    "eval-runs/codex-maintenance/README.md",
    "eval-runs/codex-maintenance/traces.json",
    "examples/external-repos/python-library/skills.json",
    "examples/end-to-end-maintenance/expected-report.json",
    "schemas/external-skills.schema.json",
]

FORBIDDEN_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_dsa",
    "id_ed25519",
}

FORBIDDEN_SUFFIXES = {
    ".pem",
    ".p12",
    ".pfx",
    ".key",
    ".pyc",
}

FORBIDDEN_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "dist",
    "dist-smoke",
    "dist-release",
    ".our-skills-dist",
    ".our-skills-quickstart",
    ".quickstart-home",
    "tmp",
    "temp",
}


def iter_public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in FORBIDDEN_DIRS for part in rel_parts[:-1]):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def check_required_files() -> list[str]:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    return [f"missing required public file: {path}" for path in missing]


def check_forbidden_files() -> list[str]:
    problems: list[str] = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_dir() and path.name in FORBIDDEN_DIRS and path.name != ".git":
            problems.append(f"local generated directory should be removed before upload: {rel}")
        if not path.is_file():
            continue
        if ".git" in path.relative_to(ROOT).parts:
            continue
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(f"forbidden public-upload file: {rel}")
    return problems


def check_file_sizes(files: list[Path]) -> list[str]:
    problems = []
    for path in files:
        size = path.stat().st_size
        if size > MAX_PUBLIC_FILE_BYTES:
            rel = path.relative_to(ROOT).as_posix()
            problems.append(f"file is larger than GitHub web upload comfort limit: {rel} ({size} bytes)")
    return problems


def check_license_text() -> list[str]:
    license_path = ROOT / "LICENSE"
    if not license_path.exists():
        return []
    text = license_path.read_text(encoding="utf-8", errors="replace")
    required = ["MIT License", "Permission is hereby granted", "our-skills contributors"]
    missing = [fragment for fragment in required if fragment not in text]
    return [f"LICENSE does not look like the expected MIT license; missing: {', '.join(missing)}"] if missing else []


def main() -> int:
    files = iter_public_files()
    problems = []
    problems.extend(check_required_files())
    problems.extend(check_forbidden_files())
    problems.extend(check_file_sizes(files))
    problems.extend(check_license_text())
    if problems:
        for problem in problems:
            print(f"[FAIL] {problem}")
        return 1
    print(f"[OK] Publication-ready check passed across {len(files)} public files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
