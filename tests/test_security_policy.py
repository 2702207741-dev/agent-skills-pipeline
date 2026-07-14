from __future__ import annotations

import unittest

from scripts import security_scan


class SecurityPolicyRegressionTests(unittest.TestCase):
    def test_dangerous_command_policy_cases(self) -> None:
        policy = security_scan.load_dangerous_policy()
        data = security_scan.load_json(security_scan.DANGEROUS_REGRESSION_CASES)
        for case in data["cases"]:
            with self.subTest(case=case["id"]):
                matches = security_scan.dangerous_matches(case["sample"], policy)
                if case["kind"] == "deny":
                    self.assertIn(case["expected_policy"], matches)
                else:
                    self.assertEqual(matches, [])

    def test_redaction_decision_cases(self) -> None:
        data = security_scan.load_json(security_scan.REDACTION_REGRESSION_CASES)
        for case in data["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    security_scan.classify_redaction_sample(case["artifact"]),
                    case["expected_decision"],
                )


if __name__ == "__main__":
    unittest.main()
