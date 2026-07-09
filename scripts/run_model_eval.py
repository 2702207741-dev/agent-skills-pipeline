#!/usr/bin/env python3
"""Run deterministic multi-model replay evaluation over the public dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "evals" / "model_matrix.json"
DATASET = ROOT / "examples" / "replay-dataset.json"
REPORT_JSON = ROOT / "reports" / "model-eval-report.json"
REPORT_MD = ROOT / "reports" / "model-eval-report.md"


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate() -> dict[str, Any]:
    matrix = load_json(MATRIX)
    dataset = load_json(DATASET)
    cases = dataset.get("cases", [])
    if not cases:
        raise AssertionError("replay dataset has no cases")

    model_results = []
    for model in matrix.get("models", []):
        passed = 0
        failures = []
        for case in cases:
            score = case.get("score", {})
            ok = bool(score.get("passed")) and case.get("execution_step_count", 0) >= 3
            if model.get("status") != "enabled":
                ok = False
            if ok:
                passed += 1
            else:
                failures.append(case["id"])
        total = len(cases)
        model_results.append(
            {
                "id": model["id"],
                "display_name": model["display_name"],
                "provider": model["provider"],
                "mode": model["mode"],
                "status": model["status"],
                "passed": passed,
                "total": total,
                "pass_rate": round(passed / total, 4),
                "failures": failures,
                "notes": model.get("notes", []),
            }
        )

    required = {"codex", "claude", "gemini", "local-model"}
    present = {model["id"] for model in model_results}
    missing = sorted(required - present)
    if missing:
        raise AssertionError(f"model matrix missing required models: {', '.join(missing)}")

    return {
        "schema_version": 1,
        "kind": "our-skills-multi-model-eval-report",
        "version": dataset["version"],
        "dataset": "examples/replay-dataset.json",
        "evaluation_mode": "deterministic replay of recorded agent traces",
        "case_count": len(cases),
        "models": model_results,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Multi-Model Evaluation: v{report['version']}",
        "",
        f"- Dataset: `{report['dataset']}`",
        f"- Mode: {report['evaluation_mode']}",
        f"- Cases: {report['case_count']}",
        "",
        "| Model | Provider | Mode | Status | Pass Rate | Failures |",
        "|---|---|---|---|---:|---:|",
    ]
    for model in report["models"]:
        lines.append(
            f"| {model['display_name']} | {model['provider']} | {model['mode']} | {model['status']} | {model['pass_rate']:.2f} | {len(model['failures'])} |"
        )
    lines.append("")
    lines.append("Live API adapters can replace replay-only scoring later; this report is intentionally deterministic for CI.")
    lines.append("")
    return "\n".join(lines)


def outputs() -> dict[Path, str]:
    report = evaluate()
    return {
        REPORT_JSON: json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        REPORT_MD: markdown(report),
    }


def write_reports() -> list[Path]:
    paths = []
    for path, content in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def check_reports() -> list[str]:
    mismatches = []
    for path, expected in outputs().items():
        if not path.exists():
            mismatches.append(f"missing {path.relative_to(ROOT).as_posix()}")
            continue
        if path.read_text(encoding="utf-8") != expected:
            mismatches.append(f"stale {path.relative_to(ROOT).as_posix()}")
    return mismatches


def write_release_model_eval_report(output_dir: Path, release: str) -> Path:
    report = evaluate()
    path = output_dir / f"our-skills-{release}.model-eval-report.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when checked-in model evaluation report is missing or stale")
    args = parser.parse_args()
    try:
        if args.check:
            mismatches = check_reports()
            if mismatches:
                for mismatch in mismatches:
                    print(f"[FAIL] {mismatch}")
                return 1
            print("[OK] Multi-model evaluation report is current")
            return 0
        paths = write_reports()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1
    for path in paths:
        print(f"[OK] Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
