#!/usr/bin/env python3
"""Generate or check the public task library and replay dataset."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
TRACES = ROOT / "eval-runs" / "rigorbench-v1.3" / "traces.json"
EXAMPLES = ROOT / "examples"
TASK_LIBRARY = EXAMPLES / "task-library.json"
REPLAY_DATASET = EXAMPLES / "replay-dataset.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_outputs() -> dict[Path, str]:
    registry = load_json(REGISTRY)
    traces = load_json(TRACES)
    skills = {entry["name"]: entry for entry in registry["skills"]}
    tasks = []
    replay_cases = []

    for trace in traces["traces"]:
        skill = trace["skill"]
        if skill not in skills:
            raise AssertionError(f"trace references unregistered skill: {skill}")
        task = {
            "id": trace["id"],
            "skill": skill,
            "case_type": trace["case_type"],
            "prompt": trace["input_prompt"],
            "summary": trace["final_output"]["summary"],
            "expected_decision": trace["final_output"]["decision"],
            "trace": "eval-runs/rigorbench-v1.3/traces.json",
        }
        tasks.append(task)
        replay_cases.append(
            {
                "id": trace["id"],
                "skill": skill,
                "case_type": trace["case_type"],
                "input_prompt": trace["input_prompt"],
                "triggered_skill": trace["triggered_skill"]["name"],
                "resources_read": [resource["path"] for resource in trace.get("resources_read", [])],
                "execution_step_count": len(trace.get("execution_steps", [])),
                "expected_decision": trace["final_output"]["decision"],
                "score": trace["score"],
                "source_trace_sha256": trace["skill_sha256"],
            }
        )

    by_skill: dict[str, list[str]] = {name: [] for name in skills}
    for task in tasks:
        by_skill[task["skill"]].append(task["case_type"])
    for skill, case_types in by_skill.items():
        missing = sorted({"success", "failure", "boundary"} - set(case_types))
        if missing:
            raise AssertionError(f"{skill} missing example case types: {', '.join(missing)}")

    task_library = {
        "schema_version": 1,
        "kind": "our-skills-public-task-library",
        "version": registry["version"],
        "generated_at": date.today().isoformat(),
        "source_traces": "eval-runs/rigorbench-v1.3/traces.json",
        "coverage": {
            "skill_count": len(skills),
            "task_count": len(tasks),
            "case_types": ["success", "failure", "boundary"],
        },
        "tasks": tasks,
    }
    replay_dataset = {
        "schema_version": 1,
        "kind": "our-skills-replay-dataset",
        "version": registry["version"],
        "generated_at": date.today().isoformat(),
        "source_traces": "eval-runs/rigorbench-v1.3/traces.json",
        "model_eval_entrypoint": "python scripts/run_model_eval.py",
        "cases": replay_cases,
    }
    return {
        TASK_LIBRARY: json.dumps(task_library, indent=2, ensure_ascii=False) + "\n",
        REPLAY_DATASET: json.dumps(replay_dataset, indent=2, ensure_ascii=False) + "\n",
    }


def write_outputs() -> list[Path]:
    paths = []
    for path, content in build_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def check_outputs() -> list[str]:
    mismatches = []
    for path, expected in build_outputs().items():
        if not path.exists():
            mismatches.append(f"missing {path.relative_to(ROOT).as_posix()}")
            continue
        if path.read_text(encoding="utf-8") != expected:
            mismatches.append(f"stale {path.relative_to(ROOT).as_posix()}")
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated example data is missing or stale")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_outputs()
            if mismatches:
                for mismatch in mismatches:
                    print(f"[FAIL] {mismatch}")
                return 1
            print("[OK] Example task library and replay dataset are current")
            return 0
        paths = write_outputs()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1
    for path in paths:
        print(f"[OK] Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
