#!/usr/bin/env python3
"""Validate and replay redacted evidence from actual maintainer agent sessions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from check_maintenance_evidence import (
        ADOPTED_STATUSES,
        CONCLUSION_STATUSES,
        REPOSITORY_URL,
        replay_command,
        run_replay_command,
    )
    from security_scan import SECRET_PATTERNS, classify_redaction_sample, is_safe_example
except ModuleNotFoundError:  # Imported as scripts.check_live_maintenance_evidence in unit tests.
    from scripts.check_maintenance_evidence import (
        ADOPTED_STATUSES,
        CONCLUSION_STATUSES,
        REPOSITORY_URL,
        replay_command,
        run_replay_command,
    )
    from scripts.security_scan import SECRET_PATTERNS, classify_redaction_sample, is_safe_example


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_FILE = ROOT / "eval-runs" / "codex-maintenance" / "live-traces.json"
TRANSCRIPT_ROOT = "eval-runs/codex-maintenance/transcripts/"
WORKFLOW_SCENARIOS = {
    "pr_review": ("success", "failure", "boundary"),
    "issue_triage": ("success", "failure", "boundary"),
    "release_workflow": ("success", "failure", "boundary"),
    "security_audit": ("success", "failure", "boundary"),
}
PRODUCTS = {"codex", "claude-code"}
DECISIONS = {"accepted", "changes_requested", "verified"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def is_nonempty_string(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def safe_repo_path(value: Any) -> str | None:
    if not is_nonempty_string(value) or "\\" in value or value.startswith("/"):
        return None
    if re.match(r"^[A-Za-z]:", value):
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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
    return result.stdout.strip() if result.returncode == 0 else None


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def text_security_findings(label: str, text: str) -> list[str]:
    findings: list[str] = []
    decision = classify_redaction_sample(text)
    if decision in {"local-only", "abort"}:
        findings.append(f"{label}: redaction classifier returned {decision}")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if is_safe_example(line):
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(f"{label}:{line_number}: secret-like material matches {name}")
    return findings


def validate_commit(trace_id: str, label: str, value: Any, failures: list[str], required: bool = True) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or not COMMIT_RE.fullmatch(value):
        failures.append(f"{trace_id}: {label} must be a full commit SHA")
        return None
    if not git_commit_exists(value):
        failures.append(f"{trace_id}: {label} is not available locally: {value}")
    elif not git_commit_is_reachable(value):
        failures.append(f"{trace_id}: {label} is not reachable from HEAD: {value}")
    return value


def validate_live_record(
    record: Any,
    replay: bool,
    replay_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    trace_id = record.get("id", "<missing-id>") if isinstance(record, dict) else "<invalid-record>"
    failures: list[str] = []
    if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not ID_RE.fullmatch(record["id"]):
        return {"id": trace_id, "passed": False, "failures": [f"{trace_id}: id must use kebab-case"]}

    workflow = record.get("workflow")
    scenario = record.get("scenario")
    if workflow not in WORKFLOW_SCENARIOS or scenario not in WORKFLOW_SCENARIOS.get(workflow, ()):
        failures.append(f"{trace_id}: workflow or scenario is not recognized")
    if record.get("capture_kind") != "live_agent_session":
        failures.append(f"{trace_id}: capture_kind must be live_agent_session")

    started = parse_timestamp(record.get("started_at"))
    finished = parse_timestamp(record.get("finished_at"))
    if started is None or finished is None or finished < started:
        failures.append(f"{trace_id}: started_at and finished_at must be ordered timezone-aware timestamps")

    agent = record.get("agent")
    if not isinstance(agent, dict) or agent.get("product") not in PRODUCTS or not all(
        is_nonempty_string(agent.get(field), 2) for field in ("provider", "model", "version")
    ):
        failures.append(f"{trace_id}: agent identity is incomplete")

    source = record.get("source")
    head_before = None
    head_after = None
    if not isinstance(source, dict):
        failures.append(f"{trace_id}: source must be an object")
    else:
        head_before = validate_commit(trace_id, "source.head_before", source.get("head_before"), failures)
        head_after = validate_commit(trace_id, "source.head_after", source.get("head_after"), failures, required=False)
        if not is_nonempty_string(source.get("branch"), 3):
            failures.append(f"{trace_id}: source.branch is incomplete")
        if not isinstance(source.get("session_id_sha256"), str) or not HASH_RE.fullmatch(source["session_id_sha256"]):
            failures.append(f"{trace_id}: source.session_id_sha256 is invalid")

    input_data = record.get("input")
    if not isinstance(input_data, dict) or input_data.get("source") != "redacted_maintainer_request" or not is_nonempty_string(
        input_data.get("prompt"), 20
    ):
        failures.append(f"{trace_id}: input must retain the redacted maintainer request")
    else:
        failures.extend(text_security_findings(f"{trace_id}:input", input_data["prompt"]))

    transcript = record.get("transcript")
    if not isinstance(transcript, dict):
        failures.append(f"{trace_id}: transcript must be an object")
    else:
        transcript_path = safe_repo_path(transcript.get("path"))
        digest = transcript.get("sha256")
        if transcript_path is None or not transcript_path.startswith(TRANSCRIPT_ROOT):
            failures.append(f"{trace_id}: transcript path must remain under {TRANSCRIPT_ROOT}")
        elif not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
            failures.append(f"{trace_id}: transcript sha256 is invalid")
        else:
            absolute = ROOT / transcript_path
            if not absolute.is_file():
                failures.append(f"{trace_id}: transcript file is missing: {transcript_path}")
            else:
                content = absolute.read_bytes()
                if sha256_bytes(content) != digest:
                    failures.append(f"{trace_id}: transcript digest does not match {transcript_path}")
                failures.extend(text_security_findings(f"{trace_id}:transcript", content.decode("utf-8", errors="replace")))

    files = record.get("files_read")
    if not isinstance(files, list) or len(files) < 2:
        failures.append(f"{trace_id}: files_read must contain at least two files")
    else:
        seen: set[tuple[str, str]] = set()
        for item in files:
            path = safe_repo_path(item.get("path")) if isinstance(item, dict) else None
            commit = item.get("commit") if isinstance(item, dict) else None
            blob = item.get("git_blob") if isinstance(item, dict) else None
            if path is None or commit not in {head_before, head_after} or not isinstance(blob, str):
                failures.append(f"{trace_id}: files_read entry has invalid path, commit, or blob")
                continue
            if (commit, path) in seen:
                failures.append(f"{trace_id}: duplicate files_read entry: {commit}:{path}")
            seen.add((commit, path))
            if git_blob_for(commit, path) != blob:
                failures.append(f"{trace_id}: git blob does not match {commit}:{path}")
            if not is_nonempty_string(item.get("purpose"), 10):
                failures.append(f"{trace_id}: files_read purpose is incomplete")

    commands = record.get("commands")
    if not isinstance(commands, list) or not commands:
        failures.append(f"{trace_id}: commands must be a non-empty list")
    else:
        for command in commands:
            command_id = command.get("id") if isinstance(command, dict) else None
            try:
                display, _ = replay_command(command_id)
            except AssertionError as exc:
                failures.append(f"{trace_id}: {exc}")
                continue
            if command.get("command") != display or command.get("exit_code") != 0:
                failures.append(f"{trace_id}: command must match its approved zero-exit replay contract")
            if not isinstance(command.get("output_sha256"), str) or not HASH_RE.fullmatch(command["output_sha256"]):
                failures.append(f"{trace_id}: command output_sha256 is invalid")
            markers = command.get("replay_markers")
            if not isinstance(markers, list) or any(not is_nonempty_string(marker, 4) for marker in markers):
                failures.append(f"{trace_id}: command replay_markers are invalid")
                markers = []
            excerpt = command.get("recorded_output_excerpt")
            if not isinstance(excerpt, str) or any(marker not in excerpt for marker in markers):
                failures.append(f"{trace_id}: command output excerpt is incomplete")
            if replay:
                if command_id not in replay_cache:
                    replay_cache[command_id] = run_replay_command(command_id)
                result = replay_cache[command_id]
                if result["exit_code"] != 0 or any(marker not in result["output"] for marker in markers):
                    failures.append(f"{trace_id}: replay command {command_id} no longer matches captured evidence")

    output = record.get("final_output")
    if not isinstance(output, dict) or output.get("decision") not in DECISIONS or not is_nonempty_string(output.get("summary"), 30):
        failures.append(f"{trace_id}: final_output is incomplete")
    elif not isinstance(output.get("sha256"), str) or not HASH_RE.fullmatch(output["sha256"]):
        failures.append(f"{trace_id}: final_output sha256 is invalid")
    elif sha256_bytes(output["summary"].encode("utf-8")) != output["sha256"]:
        failures.append(f"{trace_id}: final_output sha256 does not match its summary")
    else:
        failures.extend(text_security_findings(f"{trace_id}:final_output", output["summary"]))

    conclusion = record.get("human_conclusion")
    if not isinstance(conclusion, dict):
        failures.append(f"{trace_id}: human_conclusion must be an object")
    else:
        status = conclusion.get("status")
        adopted = conclusion.get("adopted")
        if status not in CONCLUSION_STATUSES or not isinstance(adopted, bool) or not is_nonempty_string(conclusion.get("summary"), 30):
            failures.append(f"{trace_id}: human_conclusion is incomplete")
        elif adopted != (status in ADOPTED_STATUSES):
            failures.append(f"{trace_id}: human_conclusion adoption does not match status")
        elif adopted:
            commit = validate_commit(trace_id, "human_conclusion.adoption_commit", conclusion.get("adoption_commit"), failures)
            if commit and conclusion.get("adoption_url") != f"{REPOSITORY_URL}/commit/{commit}":
                failures.append(f"{trace_id}: human_conclusion adoption_url does not match adoption_commit")

    redaction = record.get("redaction")
    if not isinstance(redaction, dict) or redaction.get("status") != "passed" or redaction.get("scanner") != "security_scan" or redaction.get(
        "findings"
    ) != 0:
        failures.append(f"{trace_id}: redaction gate did not pass cleanly")

    return {
        "id": trace_id,
        "workflow": workflow,
        "scenario": scenario,
        "passed": not failures,
        "failures": failures,
    }


def expected_coverage() -> dict[str, list[str]]:
    return {workflow: list(scenarios) for workflow, scenarios in WORKFLOW_SCENARIOS.items()}


def run_live_maintenance_evidence(
    runs_file: Path | None = None,
    replay: bool = True,
    require_coverage: bool = False,
) -> dict[str, Any]:
    path = runs_file or DEFAULT_RUNS_FILE
    failures: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"source_runs_file": str(path), "failures": [str(exc)], "passed": False, "coverage_met": False}

    if data.get("schema_version") != 2 or data.get("suite") != "our-skills-live-maintainer-evidence":
        failures.append("live maintenance evidence must use the recognized schema v2 suite")
    if data.get("coverage_requirements") != expected_coverage():
        failures.append("live maintenance evidence coverage_requirements do not match the 4x3 matrix")
    policy = data.get("capture_policy")
    if not isinstance(policy, dict) or any(
        not is_nonempty_string(policy.get(field), 30) for field in ("purpose", "privacy_rule", "replay_rule")
    ):
        failures.append("live maintenance evidence capture_policy is incomplete")
    records = data.get("records")
    if not isinstance(records, list):
        failures.append("live maintenance evidence records must be a list")
        records = []

    ids = [record.get("id") for record in records if isinstance(record, dict)]
    duplicates = sorted(item for item, count in Counter(ids).items() if item and count > 1)
    if duplicates:
        failures.append(f"duplicate live maintenance evidence ids: {', '.join(duplicates)}")

    replay_cache: dict[str, dict[str, Any]] = {}
    results = [validate_live_record(record, replay, replay_cache) for record in records]
    coverage: dict[str, dict[str, int]] = {
        workflow: {scenario: 0 for scenario in scenarios} for workflow, scenarios in WORKFLOW_SCENARIOS.items()
    }
    for result in results:
        if result["passed"] and result.get("workflow") in coverage and result.get("scenario") in coverage[result["workflow"]]:
            coverage[result["workflow"]][result["scenario"]] += 1
        failures.extend(result["failures"])

    missing = [
        f"{workflow}:{scenario}"
        for workflow, scenarios in coverage.items()
        for scenario, count in scenarios.items()
        if count < 1
    ]
    coverage_met = not missing
    if require_coverage and missing:
        failures.append(f"live maintenance evidence coverage is incomplete: {', '.join(missing)}")
    return {
        "suite": data.get("suite"),
        "source_runs_file": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
        "replay": replay,
        "require_coverage": require_coverage,
        "coverage": coverage,
        "coverage_met": coverage_met,
        "missing_coverage": missing,
        "record_count": len(records),
        "validated_count": sum(1 for result in results if result["passed"]),
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-file", type=Path, help="Override the live evidence file")
    parser.add_argument("--no-replay", action="store_true", help="Validate without rerunning allowlisted local commands")
    parser.add_argument("--require-coverage", action="store_true", help="Require all 12 workflow/scenario cells")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_live_maintenance_evidence(args.runs_file, not args.no_replay, args.require_coverage)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif report["passed"]:
        print(
            f"[OK] Live maintenance evidence validated: {report['validated_count']}/{report['record_count']} records; "
            f"coverage_met={str(report['coverage_met']).lower()}"
        )
        if report["missing_coverage"]:
            print(f"[INFO] Missing observed coverage: {', '.join(report['missing_coverage'])}")
    else:
        print("[FAIL] Live maintenance evidence:")
        for failure in report["failures"]:
            print(f"  - {failure}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
