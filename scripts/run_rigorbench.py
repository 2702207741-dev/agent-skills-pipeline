#!/usr/bin/env python3
"""Replay saved E2E agent traces for registered skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from check_maintenance_evidence import REQUIRED_WORKFLOWS, run_maintenance_evidence


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
BENCH = ROOT / "benchmarks" / "rigorbench.json"
HISTORY = ROOT / "benchmarks" / "regression-history.json"

REQUIRED_CASE_TYPES = {"success", "failure", "boundary"}
SCORE_DIMENSIONS = ("trigger", "resources", "execution", "final_output", "score_record")
OUTPUT_DECISIONS = {
    "success": {"completed"},
    "failure": {"blocked_expected_failure", "request_changes", "refused"},
    "boundary": {"completed_with_caveat", "degraded"},
}
STEP_STATUSES = {"pass", "warn", "blocked"}
MAINTENANCE_RUNS_FILE = "eval-runs/codex-maintenance/traces.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {display_path(path)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def as_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def resource_exists(resource: dict[str, Any]) -> bool:
    path = resource.get("path")
    return as_nonempty_string(path) and (ROOT / path).exists()


def score_trace(trace: dict[str, Any], registered: dict[str, dict[str, Any]]) -> tuple[bool, int, list[str]]:
    failures: list[str] = []
    skill = trace.get("skill")
    if skill not in registered:
        return False, 0, [f"unknown registered skill: {skill}"]

    entry = registered[skill]
    skill_file = ROOT / entry["path"] / "SKILL.md"
    current_hash = sha256(skill_file)
    if trace.get("skill_version") != entry["version"]:
        failures.append("trace skill_version does not match skills.json")
    if trace.get("skill_sha256") != current_hash:
        failures.append("trace skill_sha256 is stale for current SKILL.md")

    case_type = trace.get("case_type")
    if case_type not in REQUIRED_CASE_TYPES:
        failures.append(f"case_type must be one of {sorted(REQUIRED_CASE_TYPES)}")

    prompt = trace.get("input_prompt")
    triggered = trace.get("triggered_skill", {})
    trigger_ok = (
        as_nonempty_string(prompt)
        and len(prompt.strip()) >= 20
        and triggered.get("name") == skill
        and triggered.get("decision") == "load"
        and isinstance(triggered.get("evidence"), list)
        and bool(triggered["evidence"])
    )
    if not trigger_ok:
        failures.append("trigger evidence is incomplete")

    resources = trace.get("resources_read", [])
    resources_ok = isinstance(resources, list) and bool(resources) and all(
        isinstance(resource, dict) and resource_exists(resource) for resource in resources
    )
    if not resources_ok:
        failures.append("resources_read must reference existing repo files")

    steps = trace.get("execution_steps", [])
    execution_ok = (
        isinstance(steps, list)
        and len(steps) >= 3
        and all(isinstance(step, dict) and step.get("status") in STEP_STATUSES for step in steps)
    )
    if not execution_ok:
        failures.append("execution_steps must contain at least 3 replayable non-failing steps")

    final_output = trace.get("final_output", {})
    decision = final_output.get("decision")
    output_ok = (
        isinstance(final_output, dict)
        and as_nonempty_string(final_output.get("summary"))
        and len(final_output["summary"].strip()) >= 30
        and case_type in OUTPUT_DECISIONS
        and decision in OUTPUT_DECISIONS.get(case_type, set())
    )
    if not output_ok:
        failures.append("final_output decision or summary does not match case_type")

    computed = {
        "trigger": trigger_ok,
        "resources": resources_ok,
        "execution": execution_ok,
        "final_output": output_ok,
    }
    score = trace.get("score", {})
    score_dimensions = score.get("dimensions", {})
    score_record_ok = (
        isinstance(score, dict)
        and score.get("max_points") == len(SCORE_DIMENSIONS)
        and as_nonempty_string(score.get("rationale"))
        and isinstance(score_dimensions, dict)
        and all(score_dimensions.get(name) is computed[name] for name in computed)
    )
    computed["score_record"] = score_record_ok
    if not score_record_ok:
        failures.append("score record does not match replayed dimensions")

    points = sum(1 for passed in computed.values() if passed)
    expected_passed = points == len(SCORE_DIMENSIONS)
    if score.get("points") != points:
        failures.append(f"recorded score.points {score.get('points')} != replayed {points}")
    if score.get("passed") is not expected_passed:
        failures.append("recorded score.passed does not match replayed result")

    return expected_passed and not failures, points, failures


def load_runs_file(bench: dict[str, Any], override: str | None) -> tuple[Path, dict[str, Any]]:
    source = override or bench.get("source_runs_file")
    if not as_nonempty_string(source):
        raise AssertionError("rigorbench must define source_runs_file")
    path = ROOT / source
    data = load_json(path)
    if data.get("schema_version") != 1:
        raise AssertionError("eval-runs schema_version must be 1")
    if data.get("suite") != bench.get("suite"):
        raise AssertionError("eval-runs suite must match benchmarks/rigorbench.json")
    traces = data.get("traces")
    if not isinstance(traces, list) or not traces:
        raise AssertionError("eval-runs traces must be a non-empty list")
    return path, data


def run_benchmark(runs_file: str | None = None, include_maintenance: bool = True) -> dict[str, Any]:
    registry = load_json(REGISTRY)
    bench = load_json(BENCH)
    history = load_json(HISTORY)
    source_path, runs = load_runs_file(bench, runs_file)
    if bench.get("maintainer_workflow_runs_file") != MAINTENANCE_RUNS_FILE:
        raise AssertionError("rigorbench maintainer_workflow_runs_file is not configured")

    registered = {entry["name"]: entry for entry in registry["skills"]}
    by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    duplicate_ids = [trace_id for trace_id, count in Counter(trace.get("id") for trace in runs["traces"]).items() if count > 1]
    if duplicate_ids:
        raise AssertionError(f"duplicate trace ids: {', '.join(sorted(duplicate_ids))}")

    for trace in runs["traces"]:
        by_skill[trace.get("skill")].append(trace)

    results: dict[str, Any] = {}
    for skill in registered:
        traces = by_skill.get(skill, [])
        case_types = {trace.get("case_type") for trace in traces}
        missing_types = sorted(REQUIRED_CASE_TYPES - case_types)
        if len(traces) < 3 or missing_types:
            raise AssertionError(f"{skill} needs at least 3 traces covering success/failure/boundary")

        passed = 0
        failures: list[dict[str, Any]] = []
        for trace in traces:
            ok, points, trace_failures = score_trace(trace, registered)
            if ok:
                passed += 1
            else:
                failures.append({"trace": trace.get("id", "<missing id>"), "points": points, "failures": trace_failures})

        total = len(traces)
        results[skill] = {
            "passed": passed,
            "total": total,
            "pass_rate": round(passed / total, 4),
            "case_types": sorted(case_types),
            "failures": failures,
        }

    latest = history["history"][-1]["results"]
    regressions = []
    for skill, result in results.items():
        baseline = latest.get(skill)
        if baseline is None:
            regressions.append(f"{skill}: missing baseline")
            continue
        if result["total"] < baseline["total"]:
            regressions.append(f"{skill}: trace count {result['total']} < baseline {baseline['total']}")
        if result["pass_rate"] < baseline["pass_rate"]:
            regressions.append(f"{skill}: pass rate {result['pass_rate']} < baseline {baseline['pass_rate']}")

    maintenance = (
        run_maintenance_evidence(replay=True)
        if include_maintenance
        else {
            "suite": "our-skills-maintainer-rigorbench",
            "replay": False,
            "workflows": {},
            "record_count": 0,
            "failures": [],
            "passed": True,
            "skipped": "platform report generation only consumes per-skill replay results",
        }
    )
    return {
        "suite": bench["suite"],
        "release": registry["release_policy"]["current_release"],
        "source_runs_file": display_path(source_path),
        "results": results,
        "regressions": regressions,
        "maintainer_workflows": maintenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-file", help="Override benchmarks/rigorbench.json source_runs_file")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result JSON")
    args = parser.parse_args()

    try:
        report = run_benchmark(args.runs_file)
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    has_trace_failures = any(result["failures"] for result in report["results"].values())
    has_regressions = bool(report["regressions"])
    maintenance = report["maintainer_workflows"]
    has_maintenance_failures = not maintenance["passed"]

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if has_trace_failures or has_regressions or has_maintenance_failures:
            return 1
    else:
        for skill, result in report["results"].items():
            types = ",".join(result["case_types"])
            print(f"{skill}: {result['passed']}/{result['total']} pass_rate={result['pass_rate']:.2f} cases={types}")
        if has_trace_failures:
            print("[FAIL] Trace replay failures:")
            for skill, result in report["results"].items():
                for failure in result["failures"]:
                    print(f"  - {skill}/{failure['trace']} ({failure['points']}/5)")
                    for reason in failure["failures"]:
                        print(f"    * {reason}")
            return 1
        if has_regressions:
            print("[FAIL] Regressions detected:")
            for regression in report["regressions"]:
                print(f"  - {regression}")
            return 1
        for workflow in REQUIRED_WORKFLOWS:
            result = maintenance["workflows"].get(workflow, {"passed": 0, "total": 0})
            print(f"maintainer/{workflow}: {result['passed']}/{result['total']} passing")
        if has_maintenance_failures:
            print("[FAIL] Maintainer workflow replay failures:")
            for failure in maintenance["failures"]:
                print(f"  - {failure}")
            return 1
        print(f"[OK] RigorBench replayed {report['source_runs_file']} and Codex maintainer workflows with no regressions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
