#!/usr/bin/env python3
"""Validate v3 ecosystem assets for docs, contribution, examples, and evals."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "AGENTS.md",
    "docs/index.html",
    "docs/styles.css",
    "docs/assets/ecosystem-map.svg",
    "docs/third-party-skill-spec.md",
    "docs/review-checklist.md",
    "docs/codex-for-oss-case-study.md",
    "docs/maintainer-workflows.md",
    "eval-runs/codex-maintenance/README.md",
    "eval-runs/codex-maintenance/traces.json",
    "CONTRIBUTING.md",
    "CLA.md",
    "SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/CODEOWNERS",
    ".github/workflows/skill-review-bot.yml",
    "schemas/third-party-skill.schema.json",
    "templates/third-party-skill/SKILL.md",
    "examples/task-library.json",
    "examples/replay-dataset.json",
    "evals/model_matrix.json",
    "reports/model-eval-report.json",
    "reports/model-eval-report.md",
    "scripts/check_maintenance_evidence.py",
]


REQUIRED_MARKERS = {
    "README.md": (
        "## 60-Second Review",
        "### Three Commands",
        "### Three Evidence Links",
        "Codex for OSS Case Study",
        "12 replayable Codex maintainer workflow records",
        "releases/tag/v3.0.0",
    ),
    "AGENTS.md": (
        "## Review Behavior",
        "## Release Behavior",
        "## Security Behavior",
    ),
    "docs/codex-for-oss-case-study.md": (
        "## The Maintainer Problem",
        "## Why Codex Fits",
        "## Evidence Already in This Repository",
        "## Real Codex Maintenance Evidence",
    ),
    "docs/maintainer-workflows.md": (
        "## Pull Request Review",
        "## Issue Triage",
        "## Release Workflow",
        "## Security Audit",
        "## Evidence Replay",
    ),
}


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    failures = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            failures.append(f"missing {rel}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    registry = load_json("skills.json")
    skills = {entry["name"] for entry in registry["skills"]}
    task_library = load_json("examples/task-library.json")
    replay_dataset = load_json("examples/replay-dataset.json")
    model_matrix = load_json("evals/model_matrix.json")
    model_report = load_json("reports/model-eval-report.json")
    schema = load_json("schemas/third-party-skill.schema.json")

    task_skills = {task["skill"] for task in task_library.get("tasks", [])}
    if task_skills != skills:
        failures.append(f"task library skills do not match registry: {sorted(task_skills ^ skills)}")

    by_skill = {skill: set() for skill in skills}
    for case in replay_dataset.get("cases", []):
        if case.get("skill") in by_skill:
            by_skill[case["skill"]].add(case.get("case_type"))
    for skill, case_types in by_skill.items():
        missing = {"success", "failure", "boundary"} - case_types
        if missing:
            failures.append(f"{skill} replay dataset missing {sorted(missing)}")

    required_models = {"codex", "claude", "gemini", "local-model"}
    models = {model["id"] for model in model_matrix.get("models", [])}
    if models != required_models:
        failures.append(f"model matrix mismatch: {sorted(models ^ required_models)}")
    report_models = {model["id"] for model in model_report.get("models", [])}
    if report_models != required_models:
        failures.append(f"model eval report mismatch: {sorted(report_models ^ required_models)}")

    required_schema_fields = {"name", "description", "version", "owner", "license", "security_review"}
    if not required_schema_fields.issubset(set(schema.get("required", []))):
        failures.append("third-party schema missing required governance fields")

    docs = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    for marker in ("Marketplace", "Doctor", "Quality", "Contribute", "Replay"):
        if marker not in docs:
            failures.append(f"docs site missing section marker: {marker}")

    for rel, markers in REQUIRED_MARKERS.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{rel} missing reviewer marker: {marker}")

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("[OK] Ecosystem assets are complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
