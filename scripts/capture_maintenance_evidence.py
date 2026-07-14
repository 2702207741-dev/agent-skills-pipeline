#!/usr/bin/env python3
"""Safely append one redacted live maintainer-session record; dry-run by default."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from check_live_maintenance_evidence import (
        DEFAULT_RUNS_FILE,
        ID_RE,
        ROOT,
        run_live_maintenance_evidence,
        text_security_findings,
    )
except ModuleNotFoundError:  # Imported as scripts.capture_maintenance_evidence in unit tests.
    from scripts.check_live_maintenance_evidence import (
        DEFAULT_RUNS_FILE,
        ID_RE,
        ROOT,
        run_live_maintenance_evidence,
        text_security_findings,
    )


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return data


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def enrich_record(draft: dict[str, Any], transcript_text: str) -> dict[str, Any]:
    record = copy.deepcopy(draft)
    record_id = record.get("id")
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        raise ValueError("record draft id must use kebab-case")

    prompt = record.get("input", {}).get("prompt") if isinstance(record.get("input"), dict) else ""
    security_findings = text_security_findings(f"{record_id}:input", str(prompt))
    security_findings.extend(text_security_findings(f"{record_id}:transcript", transcript_text))

    commands = record.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("record draft needs at least one command")
    for command in commands:
        if not isinstance(command, dict):
            raise ValueError("command drafts must be objects")
        recorded_output = command.pop("recorded_output", None)
        if not isinstance(recorded_output, str):
            raise ValueError("each command draft needs recorded_output for hashing and redaction")
        security_findings.extend(text_security_findings(f"{record_id}:command", recorded_output))
        command["output_sha256"] = sha256_text(recorded_output)
        command.setdefault("recorded_output_excerpt", recorded_output[:1000])

    output = record.get("final_output")
    if not isinstance(output, dict) or not isinstance(output.get("summary"), str):
        raise ValueError("record draft needs final_output.summary")
    output["sha256"] = sha256_text(output["summary"])
    security_findings.extend(
        text_security_findings(
            f"{record_id}:record",
            json.dumps(record, sort_keys=True, ensure_ascii=False),
        )
    )

    if security_findings:
        raise ValueError("redaction gate rejected the capture:\n  - " + "\n  - ".join(security_findings))

    transcript_path = f"eval-runs/codex-maintenance/transcripts/{record_id}.txt"
    record["capture_kind"] = "live_agent_session"
    record["transcript"] = {
        "path": transcript_path,
        "sha256": sha256_text(transcript_text),
    }
    record["redaction"] = {
        "status": "passed",
        "scanner": "security_scan",
        "findings": 0,
    }
    return record


def append_record(runs_file: Path, record: dict[str, Any], transcript_text: str) -> None:
    data = load_object(runs_file)
    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError("live evidence file records must be a list")
    if any(item.get("id") == record["id"] for item in records if isinstance(item, dict)):
        raise ValueError(f"duplicate live evidence id: {record['id']}")

    transcript_path = ROOT / record["transcript"]["path"]
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    previous_runs = runs_file.read_bytes()
    previous_transcript = transcript_path.read_bytes() if transcript_path.exists() else None
    try:
        transcript_path.write_bytes(transcript_text.encode("utf-8"))
        records.append(record)
        runs_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report = run_live_maintenance_evidence(runs_file, replay=False, require_coverage=False)
        if not report["passed"]:
            raise ValueError("captured record failed validation:\n  - " + "\n  - ".join(report["failures"]))
    except Exception:
        runs_file.write_bytes(previous_runs)
        if previous_transcript is None:
            transcript_path.unlink(missing_ok=True)
        else:
            transcript_path.write_bytes(previous_transcript)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, required=True, help="JSON draft with provenance and captured command output")
    parser.add_argument("--transcript", type=Path, required=True, help="Already-redacted UTF-8 transcript")
    parser.add_argument("--runs-file", type=Path, default=DEFAULT_RUNS_FILE)
    parser.add_argument("--apply", action="store_true", help="Write the transcript and append the record")
    args = parser.parse_args()

    try:
        record = enrich_record(load_object(args.record), args.transcript.read_text(encoding="utf-8-sig"))
        if not args.apply:
            print("[DRY-RUN] Capture passed redaction and enrichment; no files were written")
            print(json.dumps(record, indent=2, ensure_ascii=False))
            return 0
        append_record(args.runs_file.resolve(), record, args.transcript.read_text(encoding="utf-8-sig"))
        print(f"[OK] Captured live maintenance evidence: {record['id']}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
