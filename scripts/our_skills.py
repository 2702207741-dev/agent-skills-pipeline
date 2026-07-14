#!/usr/bin/env python3
"""Unified command-line interface for our-skills maintainers and adopters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
PLATFORMS = ("claude", "claude-code", "codex", "cursor", "hermes")


def run_command(args: list[str], cwd: Path = ROOT, capture: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
        check=False,
    )


def gate(name: str, args: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    result = run_command(args, cwd=cwd, capture=True)
    status = "pass" if result.returncode == 0 else "fail"
    print(f"[{status.upper()}] {name}")
    if result.returncode != 0:
        output = (result.stdout + result.stderr).splitlines()
        for line in output[-20:]:
            print(f"  {line}")
    return {
        "name": name,
        "status": status,
        "exit_code": result.returncode,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def own_workspace(workspace: Path, registry: str) -> bool:
    return workspace == ROOT and registry == "skills.json"


def command_doctor(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    results: list[dict[str, Any]] = []
    if own_workspace(workspace, args.registry):
        checks = [
            ("registry", [PYTHON, "scripts/check_registry.py"]),
            ("security", [PYTHON, "scripts/security_scan.py"]),
            ("supply-chain", [PYTHON, "scripts/check_supply_chain.py"]),
            ("ecosystem", [PYTHON, "scripts/check_ecosystem.py"]),
            ("external-adoption", [PYTHON, "scripts/check_external_adoption.py"]),
        ]
        for name, command in checks:
            if name == "external-adoption" and not (ROOT / "scripts" / "check_external_adoption.py").exists():
                continue
            results.append(gate(name, command))
        if args.full:
            results.append(gate("full-release-verification", [PYTHON, "scripts/verify_release.py"]))
        if args.platform:
            marketplace = [
                PYTHON,
                "scripts/marketplace.py",
                "doctor",
                "--platform",
                args.platform,
                "--target-root",
                args.target_root,
            ]
            if args.skill:
                marketplace.extend(["--skill", args.skill])
            if args.strict:
                marketplace.append("--strict")
            results.append(gate("installed-state", marketplace))
    else:
        command = [
            PYTHON,
            str(ROOT / "scripts" / "external_repo_check.py"),
            "--workspace",
            str(workspace),
            "--registry",
            args.registry,
            "--mode",
            "quality",
            "--output",
            args.output,
        ]
        results.append(gate("external-repository", command, cwd=workspace))

    report_data = {
        "schema_version": 1,
        "kind": "our-skills-doctor-report",
        "workspace": str(workspace),
        "status": "pass" if results and all(row["status"] == "pass" for row in results) else "fail",
        "checks": results,
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[OK] Wrote doctor report: {output}")
    print(f"[{report_data['status'].upper()}] doctor completed with {len(results)} check(s)")
    return 0 if report_data["status"] == "pass" else 1


def command_verify(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve()
    if own_workspace(workspace, args.registry):
        return run_command([PYTHON, "scripts/verify_release.py"]).returncode
    command = [
        PYTHON,
        str(ROOT / "scripts" / "external_repo_check.py"),
        "--workspace",
        str(workspace),
        "--registry",
        args.registry,
        "--mode",
        "all",
        "--output",
        args.output,
        "--report",
        f"{args.output}/gate-report.json",
    ]
    return run_command(command, cwd=workspace).returncode


def marketplace_args(command: str, args: argparse.Namespace) -> list[str]:
    values = [PYTHON, "scripts/marketplace.py", command]
    if command != "list":
        values.extend(["--platform", args.platform, "--target-root", args.target_root])
    if getattr(args, "skill", None):
        values.extend(["--skill", args.skill])
    if getattr(args, "dry_run", False):
        values.append("--dry-run")
    if getattr(args, "apply", False):
        values.append("--apply")
    if getattr(args, "plan_output", None):
        values.extend(["--plan-output", args.plan_output])
    if getattr(args, "apply_plan", None):
        values.extend(["--apply-plan", args.apply_plan])
    if getattr(args, "transaction", None):
        values.extend(["--transaction", args.transaction])
    return values


def command_marketplace(command: str, args: argparse.Namespace) -> int:
    return run_command(marketplace_args(command, args)).returncode


def replay_skill(skill: str, case_type: str, output: Path | None = None) -> int:
    registry = load_json(ROOT / "skills.json")
    entries = {entry["name"]: entry for entry in registry["skills"]}
    if skill not in entries:
        print(f"[FAIL] unknown skill: {skill}")
        return 1
    traces = load_json(ROOT / "eval-runs" / "rigorbench-v1.3" / "traces.json")["traces"]
    matches = [trace for trace in traces if trace["skill"] == skill and trace["case_type"] == case_type]
    if len(matches) != 1:
        print(f"[FAIL] expected one {case_type} trace for {skill}, found {len(matches)}")
        return 1
    trace = matches[0]
    skill_file = ROOT / entries[skill]["path"] / "SKILL.md"
    actual_hash = hashlib.sha256(skill_file.read_bytes()).hexdigest()
    if trace["skill_sha256"] != actual_hash:
        print(f"[FAIL] replay trace is stale for {skill}")
        return 1
    score = trace.get("score", {})
    steps = trace.get("execution_steps", [])
    if not score.get("passed") or len(steps) < 3 or any(step.get("status") != "pass" for step in steps):
        print(f"[FAIL] replay evidence does not pass for {skill}/{case_type}")
        return 1
    run = {
        "schema_version": 1,
        "kind": "our-skills-local-replay",
        "mode": "deterministic recorded execution replay",
        "skill": skill,
        "skill_version": trace["skill_version"],
        "skill_sha256": actual_hash,
        "case_type": case_type,
        "task": trace["input_prompt"],
        "resources_read": trace["resources_read"],
        "execution_steps": steps,
        "final_output": trace["final_output"],
        "score": score,
        "status": "pass",
    }
    print(f"[RUN] {skill}/{case_type}: {run['task']}")
    for index, step in enumerate(steps, start=1):
        print(f"  {index}. [{step['status'].upper()}] {step['action']}")
    print(f"[PASS] {score['points']}/{score['max_points']} - {trace['final_output']['summary']}")
    if output:
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[OK] Wrote replay evidence: {output}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    return replay_skill(args.skill, args.case, Path(args.output) if args.output else None)


def command_quickstart(args: argparse.Namespace) -> int:
    target = Path(args.target_root).expanduser().resolve()
    preview = argparse.Namespace(
        platform=args.platform,
        target_root=str(target),
        skill=args.skill,
        dry_run=True,
        apply=False,
    )
    if command_marketplace("install", preview) != 0:
        return 1
    if not args.apply:
        print("[DRY-RUN] Re-run quickstart with --apply to install, doctor, and replay the skill.")
        return 0
    apply_args = argparse.Namespace(
        platform=args.platform,
        target_root=str(target),
        skill=args.skill,
        dry_run=False,
        apply=True,
    )
    if command_marketplace("install", apply_args) != 0:
        return 1
    doctor = run_command(
        [
            PYTHON,
            "scripts/marketplace.py",
            "doctor",
            "--platform",
            args.platform,
            "--target-root",
            str(target),
            "--skill",
            args.skill,
            "--strict",
        ]
    )
    if doctor.returncode != 0:
        return doctor.returncode
    replay_output = target / ".our-skills-quickstart-run.json"
    if replay_skill(args.skill, "success", replay_output) != 0:
        return 1
    print(f"[OK] Quickstart complete at {target}")
    return 0


def command_demo(args: argparse.Namespace) -> int:
    command = [PYTHON, "scripts/run_maintenance_demo.py"]
    if args.check:
        command.append("--check")
    if args.output:
        command.extend(["--output", args.output])
    return run_command(command).returncode


def add_marketplace_options(parser: argparse.ArgumentParser, rollback: bool = False) -> None:
    parser.add_argument("--platform", required=True, choices=PLATFORMS)
    parser.add_argument("--target-root", default=str(Path.home()))
    parser.add_argument("--skill")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    if rollback:
        parser.add_argument("--transaction")
    else:
        parser.add_argument("--plan-output")
        parser.add_argument("--apply-plan")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="our-skills", description=__doc__)
    parser.add_argument("--version", action="version", version=f"our-skills {load_json(ROOT / 'skills.json')['version']}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List registered first-party skills")

    doctor = sub.add_parser("doctor", help="Diagnose this repository, an installation, or an external skill repository")
    doctor.add_argument("--workspace", default=str(ROOT))
    doctor.add_argument("--registry", default="skills.json")
    doctor.add_argument("--output", default=".our-skills-dist")
    doctor.add_argument("--platform", choices=PLATFORMS)
    doctor.add_argument("--target-root", default=str(Path.home()))
    doctor.add_argument("--skill")
    doctor.add_argument("--strict", action="store_true")
    doctor.add_argument("--full", action="store_true", help="Include the complete release verification chain")
    doctor.add_argument("--json-output")

    verify = sub.add_parser("verify", help="Run full local verification or an external repository quality/release gate")
    verify.add_argument("--workspace", default=str(ROOT))
    verify.add_argument("--registry", default="skills.json")
    verify.add_argument("--output", default=".our-skills-dist")

    for command in ("install", "update"):
        child = sub.add_parser(command, help=f"{command} one or all first-party skills")
        add_marketplace_options(child)
    rollback = sub.add_parser("rollback", help="Roll back one skill or a complete transaction")
    add_marketplace_options(rollback, rollback=True)

    run_parser = sub.add_parser("run", help="Replay one recorded skill execution with hash-bound evidence")
    run_parser.add_argument("--skill", required=True)
    run_parser.add_argument("--case", choices=("success", "failure", "boundary"), default="success")
    run_parser.add_argument("--output")

    quickstart = sub.add_parser("quickstart", help="Install, diagnose, and replay one skill")
    quickstart.add_argument("--platform", choices=PLATFORMS, default="codex")
    quickstart.add_argument("--target-root", default=str(Path.cwd() / ".our-skills-quickstart"))
    quickstart.add_argument("--skill", default="code-review-workflow")
    quickstart.add_argument("--apply", action="store_true")

    demo = sub.add_parser("demo", help="Run the issue-to-review-to-release maintenance demo")
    demo.add_argument("--check", action="store_true")
    demo.add_argument("--output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "list":
        return command_marketplace("list", args)
    if args.command == "doctor":
        return command_doctor(args)
    if args.command == "verify":
        return command_verify(args)
    if args.command in {"install", "update", "rollback"}:
        return command_marketplace(args.command, args)
    if args.command == "run":
        return command_run(args)
    if args.command == "quickstart":
        return command_quickstart(args)
    if args.command == "demo":
        return command_demo(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
