#!/usr/bin/env python3
"""Validate and replay auditable Codex maintainer-workflow evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DEFAULT_RUNS_FILE = ROOT / "eval-runs" / "codex-maintenance" / "traces.json"
REPOSITORY_URL = "https://github.com/2702207741-dev/agent-skills-pipeline"

REQUIRED_WORKFLOWS = {
    "pr_review": 3,
    "issue_triage": 3,
    "release_workflow": 3,
    "security_audit": 3,
}
SCORE_DIMENSIONS = (
    "task",
    "agent_behavior",
    "file_provenance",
    "command_replay",
    "output_record",
    "human_conclusion",
)
ACTION_KINDS = {"read_file", "inspect_history", "run_command", "produce_output"}
PROMPT_SOURCES = {"verbatim_maintainer_request", "commit_derived_reconstruction"}
CONCLUSION_STATUSES = {
    "adopted_on_main",
    "accepted_by_release",
    "accepted_by_gate",
    "pending_maintainer_review",
    "not_adopted",
}
ADOPTED_STATUSES = {"adopted_on_main", "accepted_by_release", "accepted_by_gate"}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
BLOB_RE = re.compile(r"^[0-9a-f]{40,64}$")


def is_nonempty_string(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise AssertionError(f"missing required file: {display_path(path)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def safe_repo_path(value: Any) -> str | None:
    if not is_nonempty_string(value) or "\\" in value:
        return None
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def git_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


@lru_cache(maxsize=None)
def git_commit_exists(commit: str) -> bool:
    return git_run(["cat-file", "-e", f"{commit}^{{commit}}"]).returncode == 0


@lru_cache(maxsize=None)
def git_commit_is_reachable(commit: str) -> bool:
    return git_run(["merge-base", "--is-ancestor", commit, "HEAD"]).returncode == 0


@lru_cache(maxsize=None)
def git_blob_for(commit: str, path: str) -> str | None:
    result = git_run(["rev-parse", f"{commit}:{path}"])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def replay_command(command_id: str) -> tuple[str, list[str]]:
    """Return a fixed command only; traces never get arbitrary shell execution."""

    commands = {
        "check_registry": ("python scripts/check_registry.py", [PYTHON, "scripts/check_registry.py"]),
        "check_ecosystem": ("python scripts/check_ecosystem.py", [PYTHON, "scripts/check_ecosystem.py"]),
        "check_release_archive": ("python scripts/check_release_archive.py", [PYTHON, "scripts/check_release_archive.py"]),
        "git_diff_check": ("git diff --check", ["git", "diff", "--check"]),
        "platform_reports": (
            "python scripts/generate_platform_reports.py --check",
            [PYTHON, "scripts/generate_platform_reports.py", "--check"],
        ),
        "marketplace_list": ("python scripts/marketplace.py list", [PYTHON, "scripts/marketplace.py", "list"]),
        "publication_ready": (
            "python scripts/check_publication_ready.py",
            [PYTHON, "scripts/check_publication_ready.py"],
        ),
        "security_scan": ("python scripts/security_scan.py", [PYTHON, "scripts/security_scan.py"]),
        "skill_graph": ("python scripts/check_skill_graph.py", [PYTHON, "scripts/check_skill_graph.py"]),
    }
    if command_id not in commands:
        raise AssertionError(f"unknown replay command id: {command_id}")
    display, args = commands[command_id]
    return display, args


def run_replay_command(command_id: str) -> dict[str, Any]:
    display, args = replay_command(command_id)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    return {
        "display": display,
        "exit_code": result.returncode,
        "output": result.stdout + result.stderr,
    }


def validate_source(trace_id: str, source: Any, failures: list[str]) -> tuple[bool, str | None]:
    if not isinstance(source, dict):
        failures.append(f"{trace_id}: source must be an object")
        return False, None
    commit = source.get("commit")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        failures.append(f"{trace_id}: source.commit must be a full git commit SHA")
        return False, None
    if source.get("commit_url") != f"{REPOSITORY_URL}/commit/{commit}":
        failures.append(f"{trace_id}: source.commit_url must point at its commit")
    if source.get("prompt_provenance") not in PROMPT_SOURCES:
        failures.append(f"{trace_id}: source.prompt_provenance is not recognized")
    if not is_nonempty_string(source.get("workflow_context"), 10):
        failures.append(f"{trace_id}: source.workflow_context is incomplete")
    if not git_commit_exists(commit):
        failures.append(f"{trace_id}: source commit is not available locally: {commit}")
    elif not git_commit_is_reachable(commit):
        failures.append(f"{trace_id}: source commit is not reachable from HEAD: {commit}")
    return not any(item.startswith(f"{trace_id}: source") for item in failures), commit


def validate_files(trace_id: str, files: Any, commit: str | None, failures: list[str]) -> bool:
    if not isinstance(files, list) or len(files) < 2:
        failures.append(f"{trace_id}: files_read must contain at least two tracked files")
        return False
    paths: set[str] = set()
    ok = True
    for file in files:
        if not isinstance(file, dict):
            failures.append(f"{trace_id}: files_read entries must be objects")
            ok = False
            continue
        path = safe_repo_path(file.get("path"))
        blob = file.get("git_blob")
        if path is None or not isinstance(blob, str) or not BLOB_RE.fullmatch(blob):
            failures.append(f"{trace_id}: files_read needs a safe path and git_blob")
            ok = False
            continue
        if not is_nonempty_string(file.get("purpose"), 10):
            failures.append(f"{trace_id}: files_read purpose is incomplete")
            ok = False
        if path in paths:
            failures.append(f"{trace_id}: duplicate files_read path: {path}")
            ok = False
        paths.add(path)
        if commit is not None:
            actual_blob = git_blob_for(commit, path)
            if actual_blob != blob:
                failures.append(f"{trace_id}: git blob does not match {commit}:{path}")
                ok = False
    return ok


def validate_skills_and_actions(trace_id: str, trace: dict[str, Any], registered: set[str], failures: list[str]) -> bool:
    ok = True
    skills = trace.get("skills_used")
    if not isinstance(skills, list) or not skills:
        failures.append(f"{trace_id}: skills_used must be a non-empty list")
        ok = False
    else:
        names = []
        for skill in skills:
            if not isinstance(skill, dict) or skill.get("name") not in registered or not is_nonempty_string(skill.get("role"), 8):
                failures.append(f"{trace_id}: skills_used entry is invalid or unregistered")
                ok = False
                continue
            names.append(skill["name"])
        if len(names) != len(set(names)):
            failures.append(f"{trace_id}: skills_used contains duplicate skills")
            ok = False

    actions = trace.get("agent_behavior")
    if not isinstance(actions, list) or len(actions) < 3:
        failures.append(f"{trace_id}: agent_behavior must contain at least three actions")
        return False
    kinds = set()
    for action in actions:
        if not isinstance(action, dict) or action.get("kind") not in ACTION_KINDS or not is_nonempty_string(action.get("detail"), 12):
            failures.append(f"{trace_id}: agent_behavior action is incomplete")
            ok = False
            continue
        kinds.add(action["kind"])
    required = {"read_file", "run_command", "produce_output"}
    if not required.issubset(kinds):
        failures.append(f"{trace_id}: agent_behavior must read, run, and produce output")
        ok = False
    return ok


def validate_task(trace_id: str, trace: dict[str, Any], failures: list[str]) -> bool:
    task = trace.get("task")
    input_data = trace.get("input")
    final_output = trace.get("final_output")
    ok = is_nonempty_string(task, 20)
    ok = ok and isinstance(input_data, dict) and is_nonempty_string(input_data.get("prompt"), 20)
    ok = ok and input_data.get("source") in PROMPT_SOURCES
    ok = ok and isinstance(final_output, dict) and final_output.get("decision") in {"accepted", "changes_requested", "verified"}
    ok = ok and is_nonempty_string(final_output.get("summary"), 30)
    if not ok:
        failures.append(f"{trace_id}: task, input prompt, or final output is incomplete")
    return ok


def validate_commands(
    trace_id: str,
    commands: Any,
    replay: bool,
    replay_cache: dict[str, dict[str, Any]],
    failures: list[str],
) -> tuple[bool, bool]:
    if not isinstance(commands, list) or not commands:
        failures.append(f"{trace_id}: commands must be a non-empty list")
        return False, False
    structure_ok = True
    output_ok = True
    replay_ok = True
    for command in commands:
        if not isinstance(command, dict):
            failures.append(f"{trace_id}: command entry must be an object")
            structure_ok = False
            continue
        command_id = command.get("id")
        try:
            display, _ = replay_command(command_id)
        except AssertionError as exc:
            failures.append(f"{trace_id}: {exc}")
            structure_ok = False
            continue
        if command.get("command") != display:
            failures.append(f"{trace_id}: command text does not match approved replay command")
            structure_ok = False
        if command.get("exit_code") != 0:
            failures.append(f"{trace_id}: recorded command exit_code must be 0")
            structure_ok = False
        excerpt = command.get("recorded_output_excerpt")
        interpretation = command.get("interpretation")
        markers = command.get("replay_markers")
        if not isinstance(excerpt, str) or not is_nonempty_string(interpretation, 12):
            failures.append(f"{trace_id}: command output excerpt or interpretation is incomplete")
            output_ok = False
        if not isinstance(markers, list) or any(not is_nonempty_string(marker, 4) for marker in markers):
            failures.append(f"{trace_id}: command replay_markers are invalid")
            output_ok = False
            markers = []
        if command_id == "git_diff_check":
            if markers:
                failures.append(f"{trace_id}: git_diff_check must preserve its empty-output contract")
                output_ok = False
        elif not markers:
            failures.append(f"{trace_id}: command must retain at least one replay marker")
            output_ok = False
        if isinstance(excerpt, str) and any(marker not in excerpt for marker in markers):
            failures.append(f"{trace_id}: recorded output excerpt is missing a replay marker")
            output_ok = False
        if replay and structure_ok:
            if command_id not in replay_cache:
                replay_cache[command_id] = run_replay_command(command_id)
            replay_result = replay_cache[command_id]
            if replay_result["exit_code"] != command.get("exit_code"):
                failures.append(f"{trace_id}: replay command {command_id} returned {replay_result['exit_code']}")
                replay_ok = False
            missing = [marker for marker in markers if marker not in replay_result["output"]]
            if missing:
                failures.append(f"{trace_id}: replay command {command_id} missing markers: {', '.join(missing)}")
                replay_ok = False
    return structure_ok and replay_ok, output_ok


def validate_human_conclusion(trace_id: str, conclusion: Any, failures: list[str]) -> bool:
    if not isinstance(conclusion, dict):
        failures.append(f"{trace_id}: human_conclusion must be an object")
        return False
    status = conclusion.get("status")
    adopted = conclusion.get("adopted")
    commit = conclusion.get("adoption_commit")
    ok = status in CONCLUSION_STATUSES and isinstance(adopted, bool) and is_nonempty_string(conclusion.get("summary"), 30)
    if adopted and status not in ADOPTED_STATUSES:
        ok = False
    if not adopted and status in ADOPTED_STATUSES:
        ok = False
    if adopted:
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit) or not git_commit_exists(commit) or not git_commit_is_reachable(commit):
            failures.append(f"{trace_id}: adopted conclusion needs a reachable adoption_commit")
            ok = False
    if not ok:
        failures.append(f"{trace_id}: human_conclusion status, adoption, or summary is invalid")
    return ok


def validate_score(trace_id: str, score: Any, computed: dict[str, bool], failures: list[str]) -> bool:
    if not isinstance(score, dict):
        failures.append(f"{trace_id}: score must be an object")
        return False
    dimensions = score.get("dimensions")
    if not isinstance(dimensions, dict):
        failures.append(f"{trace_id}: score.dimensions must be an object")
        return False
    ok = True
    for dimension, value in computed.items():
        if dimensions.get(dimension) is not value:
            failures.append(f"{trace_id}: score dimension {dimension} does not match replay")
            ok = False
    points = sum(1 for value in computed.values() if value)
    if score.get("max_points") != len(SCORE_DIMENSIONS) or score.get("points") != points or score.get("passed") is not (points == len(SCORE_DIMENSIONS)):
        failures.append(f"{trace_id}: score totals do not match replay")
        ok = False
    if not is_nonempty_string(score.get("rationale"), 30):
        failures.append(f"{trace_id}: score rationale is incomplete")
        ok = False
    return ok


def validate_trace(
    trace: Any,
    registered: set[str],
    replay: bool,
    replay_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    trace_id = trace.get("id", "<missing-id>") if isinstance(trace, dict) else "<invalid-trace>"
    failures: list[str] = []
    if not isinstance(trace, dict) or not is_nonempty_string(trace.get("id"), 8):
        return {"id": trace_id, "passed": False, "failures": [f"{trace_id}: trace id is invalid"]}
    if trace.get("workflow") not in REQUIRED_WORKFLOWS:
        failures.append(f"{trace_id}: workflow is not recognized")
    if not is_nonempty_string(trace.get("recorded_at"), 10):
        failures.append(f"{trace_id}: recorded_at is missing")

    source = trace.get("source")
    source_ok, commit = validate_source(trace_id, source, failures)
    task_ok = validate_task(trace_id, trace, failures)
    input_data = trace.get("input")
    if (
        isinstance(source, dict)
        and isinstance(input_data, dict)
        and input_data.get("source") != source.get("prompt_provenance")
    ):
        failures.append(f"{trace_id}: input source does not match source.prompt_provenance")
        task_ok = False
    computed = {
        "task": task_ok,
        "agent_behavior": validate_skills_and_actions(trace_id, trace, registered, failures),
        "file_provenance": validate_files(trace_id, trace.get("files_read"), commit, failures) and source_ok,
    }
    command_ok, output_ok = validate_commands(trace_id, trace.get("commands"), replay, replay_cache, failures)
    computed["command_replay"] = command_ok
    computed["output_record"] = output_ok
    computed["human_conclusion"] = validate_human_conclusion(trace_id, trace.get("human_conclusion"), failures)
    score_ok = validate_score(trace_id, trace.get("score"), computed, failures)
    return {
        "id": trace_id,
        "workflow": trace.get("workflow"),
        "passed": all(computed.values()) and score_ok and not failures,
        "failures": failures,
    }


def run_maintenance_evidence(runs_file: Path | None = None, replay: bool = True) -> dict[str, Any]:
    path = runs_file or DEFAULT_RUNS_FILE
    try:
        data = load_json(path)
    except (AssertionError, json.JSONDecodeError) as exc:
        return {"suite": "<unavailable>", "source_runs_file": display_path(path), "workflows": {}, "failures": [str(exc)], "passed": False}
    if not isinstance(data, dict):
        return {
            "suite": "<unavailable>",
            "source_runs_file": display_path(path),
            "workflows": {},
            "failures": ["maintenance evidence root must be an object"],
            "passed": False,
        }

    failures: list[str] = []
    if data.get("schema_version") != 1:
        failures.append("maintenance evidence schema_version must be 1")
    if data.get("suite") != "our-skills-maintainer-rigorbench":
        failures.append("maintenance evidence suite name is not recognized")
    if data.get("coverage_requirements") != REQUIRED_WORKFLOWS:
        failures.append("maintenance evidence coverage_requirements do not match the enforced matrix")
    policy = data.get("capture_policy")
    if not isinstance(policy, dict) or any(
        not is_nonempty_string(policy.get(field), 30)
        for field in ("purpose", "prompt_rule", "adoption_rule")
    ):
        failures.append("maintenance evidence capture_policy is incomplete")
    traces = data.get("records")
    if not isinstance(traces, list):
        failures.append("maintenance evidence records must be a list")
        traces = []

    registry = load_json(ROOT / "skills.json")
    registered = {entry["name"] for entry in registry.get("skills", [])}
    trace_ids = [
        trace["id"]
        for trace in traces
        if isinstance(trace, dict) and is_nonempty_string(trace.get("id"))
    ]
    duplicate_ids = [trace_id for trace_id, count in Counter(trace_ids).items() if count > 1]
    if duplicate_ids:
        failures.append(f"duplicate maintenance evidence ids: {', '.join(sorted(duplicate_ids))}")

    replay_cache: dict[str, dict[str, Any]] = {}
    results = [validate_trace(trace, registered, replay, replay_cache) for trace in traces]
    by_workflow: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        if result.get("workflow") in REQUIRED_WORKFLOWS:
            by_workflow[result["workflow"]].append(result)

    summary: dict[str, Any] = {}
    for workflow, minimum in REQUIRED_WORKFLOWS.items():
        entries = by_workflow[workflow]
        passed = sum(1 for entry in entries if entry["passed"])
        summary[workflow] = {"passed": passed, "total": len(entries), "minimum": minimum}
        if len(entries) < minimum:
            failures.append(f"{workflow}: {len(entries)} records, need at least {minimum}")
        if passed < minimum:
            failures.append(f"{workflow}: only {passed} replayed records pass, need {minimum}")

    for result in results:
        failures.extend(result["failures"])

    return {
        "suite": data.get("suite"),
        "source_runs_file": display_path(path),
        "replay": replay,
        "workflows": summary,
        "record_count": len(traces),
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-file", type=Path, help="Override eval-runs/codex-maintenance/traces.json")
    parser.add_argument("--no-replay", action="store_true", help="Validate format and provenance without rerunning approved commands")
    parser.add_argument("--json", action="store_true", help="Print machine-readable results")
    args = parser.parse_args()

    report = run_maintenance_evidence(args.runs_file, replay=not args.no_replay)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for workflow in REQUIRED_WORKFLOWS:
            result = report["workflows"].get(workflow, {"passed": 0, "total": 0, "minimum": REQUIRED_WORKFLOWS[workflow]})
            print(f"{workflow}: {result['passed']}/{result['total']} passing (minimum {result['minimum']})")
        if report["failures"]:
            print("[FAIL] Maintenance evidence failures:")
            for failure in report["failures"]:
                print(f"  - {failure}")
        else:
            mode = "replayed" if report["replay"] else "validated"
            print(f"[OK] Codex maintenance evidence {mode}: {report['record_count']} records")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
