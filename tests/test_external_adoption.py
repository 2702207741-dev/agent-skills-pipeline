from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import check_external_adoption
from scripts import external_repo_check


REPOSITORY = check_external_adoption.SELF_ACTION_REPOSITORY
VALID_SHA = "a" * 40


class SelfReferenceValidationTests(unittest.TestCase):
    def workflow(self, reference: str) -> Path:
        temp = tempfile.TemporaryDirectory(prefix="our-skills-self-reference-")
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        path = directory / "self-test.yml"
        path.write_text(
            "steps:\n"
            "  - uses: actions/checkout@" + ("b" * 40) + "\n"
            f"  - uses: {reference}\n",
            encoding="utf-8",
        )
        return path

    def test_accepts_any_reachable_full_sha(self) -> None:
        path = self.workflow(f"{REPOSITORY}@{VALID_SHA}")
        completed = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(check_external_adoption, "run", return_value=completed) as runner:
            failures = check_external_adoption.validate_self_test_reference(path)

        self.assertEqual(failures, [])
        runner.assert_called_once_with(["git", "cat-file", "-e", f"{VALID_SHA}:action.yml"])

    def test_rejects_mutable_reference(self) -> None:
        path = self.workflow(f"{REPOSITORY}@main")
        failures = check_external_adoption.validate_self_test_reference(path)
        self.assertEqual(
            failures,
            [f"action self-test reference is not pinned to a full commit SHA: {REPOSITORY}@main"],
        )

    def test_rejects_missing_repository_reference(self) -> None:
        path = self.workflow(f"example/other-action@{VALID_SHA}")
        failures = check_external_adoption.validate_self_test_reference(path)
        self.assertEqual(
            failures,
            [f"action self-test must contain exactly one {REPOSITORY} reference"],
        )

    def test_rejects_commit_without_action_contract(self) -> None:
        path = self.workflow(f"{REPOSITORY}@{VALID_SHA}")
        completed = subprocess.CompletedProcess([], 1, "", "missing")
        with mock.patch.object(check_external_adoption, "run", return_value=completed):
            failures = check_external_adoption.validate_self_test_reference(path)
        self.assertEqual(
            failures,
            [f"action self-test pins a commit that does not contain action.yml: {VALID_SHA}"],
        )


class ExternalRegistryContractTests(unittest.TestCase):
    def registry(self) -> dict:
        return {
            "project": "consumer-skills",
            "version": "1.0.0",
            "skills": [{"name": "review", "path": "skills/review", "version": "1.0.0"}],
        }

    def test_missing_schema_version_defaults_to_v1(self) -> None:
        problems = external_repo_check.validate_registry(self.registry())
        self.assertFalse(any(problem["code"] == "registry-schema" for problem in problems))

    def test_unknown_schema_version_fails_closed(self) -> None:
        registry = self.registry()
        registry["schema_version"] = 2
        problems = external_repo_check.validate_registry(registry)
        self.assertEqual([problem["code"] for problem in problems], ["registry-schema"])

    def test_repository_relative_path_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="our-skills-path-") as temp:
            workspace = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError, "safe repository-relative"):
                external_repo_check.relative_path(workspace, "../outside", "registry")


if __name__ == "__main__":
    unittest.main()
