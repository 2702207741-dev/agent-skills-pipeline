from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.capture_maintenance_evidence import enrich_record
from scripts.check_live_maintenance_evidence import expected_coverage, run_live_maintenance_evidence


class LiveEvidenceTests(unittest.TestCase):
    def empty_suite(self) -> dict:
        return {
            "schema_version": 2,
            "suite": "our-skills-live-maintainer-evidence",
            "capture_policy": {
                "purpose": "Store redacted evidence captured from actual maintainer agent sessions without conflating reconstruction.",
                "privacy_rule": "Only explicitly redacted transcripts may be committed and raw private sessions remain local.",
                "replay_rule": "Required CI replays allowlisted local commands and never calls an external model provider.",
            },
            "coverage_requirements": expected_coverage(),
            "records": [],
        }

    def write_suite(self) -> Path:
        temp = tempfile.TemporaryDirectory(prefix="our-skills-live-suite-")
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "live-traces.json"
        path.write_text(json.dumps(self.empty_suite()), encoding="utf-8")
        return path

    def test_empty_suite_is_honest_advisory_state(self) -> None:
        report = run_live_maintenance_evidence(self.write_suite(), replay=False, require_coverage=False)
        self.assertTrue(report["passed"])
        self.assertFalse(report["coverage_met"])
        self.assertEqual(report["record_count"], 0)
        self.assertEqual(len(report["missing_coverage"]), 12)

    def test_empty_suite_fails_when_coverage_is_required(self) -> None:
        report = run_live_maintenance_evidence(self.write_suite(), replay=False, require_coverage=True)
        self.assertFalse(report["passed"])
        self.assertIn("coverage is incomplete", report["failures"][-1])

    def test_capture_rejects_secret_like_transcript(self) -> None:
        draft = {
            "id": "security-secret-rejection",
            "input": {"prompt": "Review this maintenance task using only public repository evidence."},
            "commands": [{"recorded_output": "[OK] safe"}],
            "final_output": {"summary": "The task was rejected because the transcript crossed the secret boundary."},
        }
        with self.assertRaisesRegex(ValueError, "redaction gate rejected"):
            enrich_record(draft, "token=" + ("a" * 24))

    def test_capture_rejects_path_like_record_id(self) -> None:
        draft = {
            "id": "../../outside",
            "input": {"prompt": "Review this maintenance task using only public repository evidence."},
            "commands": [{"recorded_output": "[OK] safe"}],
            "final_output": {"summary": "The task retained a safe, redacted final maintenance conclusion."},
        }
        with self.assertRaisesRegex(ValueError, "kebab-case"):
            enrich_record(draft, "This transcript contains only public repository evidence.")

    def test_capture_rejects_secret_like_final_output(self) -> None:
        draft = {
            "id": "security-final-output-rejection",
            "input": {"prompt": "Review this maintenance task using only public repository evidence."},
            "commands": [{"recorded_output": "[OK] safe"}],
            "final_output": {"summary": "Do not publish token=" + ("b" * 24)},
        }
        with self.assertRaisesRegex(ValueError, "redaction gate rejected"):
            enrich_record(draft, "This transcript contains only public repository evidence.")


if __name__ == "__main__":
    unittest.main()
