#!/usr/bin/env python3
"""Automatic review bot for registry, safety, replay, platform, and ecosystem gates."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DEFAULT_OUTPUT = ROOT / "reports" / "review-bot-report.json"


def run_gate(name: str, args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, env=env)
    return {
        "name": name,
        "command": args,
        "exit_code": result.returncode,
        "status": "pass" if result.returncode == 0 else "fail",
        "stdout_tail": result.stdout.splitlines()[-20:],
        "stderr_tail": result.stderr.splitlines()[-20:],
    }


def registry_skill_paths() -> list[str]:
    registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    return [entry["path"] for entry in registry["skills"]]


def build_report() -> dict[str, Any]:
    gates = [
        ("registry", [PYTHON, "scripts/check_registry.py"]),
        ("skill-format", [PYTHON, "scripts/validate-skill.py", *registry_skill_paths()]),
        ("fixtures", [PYTHON, "scripts/run_fixture_checks.py"]),
        ("security", [PYTHON, "scripts/security_scan.py"]),
        ("maintenance-evidence", [PYTHON, "scripts/check_maintenance_evidence.py", "--no-replay"]),
        ("rigorbench", [PYTHON, "scripts/run_rigorbench.py"]),
        ("graph", [PYTHON, "scripts/check_skill_graph.py"]),
        ("platform-reports", [PYTHON, "scripts/generate_platform_reports.py", "--check"]),
        ("example-dataset", [PYTHON, "scripts/generate_example_dataset.py", "--check"]),
        ("model-eval", [PYTHON, "scripts/run_model_eval.py", "--check"]),
        ("ecosystem", [PYTHON, "scripts/check_ecosystem.py"]),
        ("release-archive", [PYTHON, "scripts/check_release_archive.py"]),
        ("publication-ready", [PYTHON, "scripts/check_publication_ready.py"]),
    ]
    results = [run_gate(name, command) for name, command in gates]
    return {
        "schema_version": 1,
        "kind": "our-skills-review-bot-report",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "status": "pass" if all(result["status"] == "pass" for result in results) else "fail",
        "gates": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Review the full repository instead of changed files")
    parser.add_argument("--check", action="store_true", help="Fail when any review gate fails")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Write JSON review report")
    args = parser.parse_args()
    report = build_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {output}")
    for gate in report["gates"]:
        print(f"[{gate['status'].upper()}] {gate['name']}")
    if args.check and report["status"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
