#!/usr/bin/env python3
"""Run the deterministic issue-to-review-to-release maintenance demo."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "examples" / "end-to-end-maintenance"
ISSUE = SCENARIO / "issue.json"
BEFORE = SCENARIO / "repository-before"
AFTER = SCENARIO / "repository-after"
EXPECTED = SCENARIO / "expected-report.json"
PYTHON = sys.executable


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def relative_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def changed_files() -> list[str]:
    before = relative_files(BEFORE)
    after = relative_files(AFTER)
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def validate_issue(data: Any) -> None:
    if not isinstance(data, dict):
        raise AssertionError("issue must be an object")
    required = ("id", "title", "type", "severity", "report", "acceptance_criteria")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise AssertionError(f"issue missing required fields: {', '.join(missing)}")
    if not isinstance(data["acceptance_criteria"], list) or len(data["acceptance_criteria"]) < 3:
        raise AssertionError("issue must contain at least three acceptance criteria")


def build_report() -> dict[str, Any]:
    issue_data = json.loads(ISSUE.read_text(encoding="utf-8"))
    validate_issue(issue_data)

    before_tests = run([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"], BEFORE)
    if before_tests.returncode == 0 or "IndexError" not in before_tests.stderr:
        raise AssertionError("the issue reproduction must fail with IndexError before the patch")

    changed = changed_files()
    required_changes = {"src/release_notes.py", "skills.json", "skills/release-notes-review/SKILL.md"}
    if not required_changes.issubset(set(changed)):
        raise AssertionError("the PR fixture does not contain the expected implementation and skill changes")
    source = (AFTER / "src" / "release_notes.py").read_text(encoding="utf-8")
    forbidden = ("eval(", "exec(", "shell=True", "subprocess.")
    if any(marker in source for marker in forbidden):
        raise AssertionError("the patch contains an unsafe execution primitive")

    after_tests = run([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"], AFTER)
    if after_tests.returncode != 0:
        raise AssertionError(f"the fixed repository test suite failed: {after_tests.stdout}{after_tests.stderr}")

    with tempfile.TemporaryDirectory(prefix="our-skills-maintenance-demo-") as tmp_dir:
        workspace = Path(tmp_dir) / "external-repository"
        shutil.copytree(AFTER, workspace)
        release_gate = run(
            [
                PYTHON,
                str(ROOT / "scripts" / "external_repo_check.py"),
                "--workspace",
                str(workspace),
                "--registry",
                "skills.json",
                "--mode",
                "all",
                "--output",
                ".our-skills-dist",
                "--report",
                ".our-skills-dist/gate-report.json",
            ],
            ROOT,
        )
        if release_gate.returncode != 0:
            raise AssertionError(f"release gate failed: {release_gate.stdout}{release_gate.stderr}")
        gate_report = json.loads((workspace / ".our-skills-dist" / "gate-report.json").read_text(encoding="utf-8"))
        artifact = workspace / gate_report["release"]["artifact"]
        manifest = workspace / gate_report["release"]["manifest"]
        checksum = workspace / gate_report["release"]["checksum"]
        if not all(path.is_file() for path in (artifact, manifest, checksum)):
            raise AssertionError("release gate did not retain every required artifact")

    return {
        "schema_version": 1,
        "kind": "our-skills-maintenance-demo-report",
        "scenario": "issue-to-pr-review-to-release-gate",
        "status": "pass",
        "stages": [
            {
                "id": "issue-triage",
                "status": "pass",
                "evidence": {
                    "issue": issue_data["id"],
                    "classification": issue_data["type"],
                    "severity": issue_data["severity"],
                    "acceptance_criteria": len(issue_data["acceptance_criteria"]),
                    "reproduction": "expected IndexError confirmed",
                },
            },
            {
                "id": "pr-review",
                "status": "pass",
                "evidence": {
                    "changed_files": changed,
                    "before_tests": "expected failure",
                    "after_tests": "pass",
                    "security_findings": 0,
                    "recommendation": "approve",
                },
            },
            {
                "id": "release-gate",
                "status": "pass",
                "evidence": {
                    "quality_status": gate_report["status"],
                    "skill_count": gate_report["skill_count"],
                    "artifact_verified": gate_report["release"]["verified"],
                    "sidecars": ["manifest", "sha256"],
                },
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the run with the checked-in expected report")
    parser.add_argument("--output", help="Write the report to this path")
    args = parser.parse_args()
    try:
        report = build_report()
        if args.check:
            expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
            if report != expected:
                raise AssertionError("maintenance demo output differs from expected-report.json")
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"[OK] Wrote demo report: {output}")
        for stage in report["stages"]:
            print(f"[PASS] {stage['id']}")
        print("[OK] Issue-to-review-to-release demo passed")
        return 0
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
