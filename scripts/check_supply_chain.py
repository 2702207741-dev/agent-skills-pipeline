#!/usr/bin/env python3
"""Validate v3.3 supply-chain workflows, policy, and provenance generation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SHA_REF_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_FILES = (
    ".github/workflows/supply-chain.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/scorecard.yml",
    ".github/dependabot.yml",
    ".github/secret_scanning.yml",
    "docs/slsa-provenance.md",
    "docs/threat-model.md",
    "docs/security-review-checklist.md",
    "scripts/generate_slsa_provenance.py",
)

REQUIRED_ACTIONS = {
    "actions/attest",
    "actions/checkout",
    "actions/download-artifact",
    "actions/setup-python",
    "actions/upload-artifact",
    "github/codeql-action",
    "ossf/scorecard-action",
    "sigstore/cosign-installer",
}

REQUIRED_MARKERS = {
    ".github/workflows/supply-chain.yml": (
        "id-token: write",
        "attestations: write",
        "artifact-metadata: write",
        "cosign sign-blob --yes --bundle",
        "cosign verify-blob",
        "actions/attest@",
        "gh release upload",
        "github.event_name == 'release'",
    ),
    ".github/workflows/codeql.yml": (
        "github/codeql-action/init@",
        "github/codeql-action/analyze@",
        "languages: python",
        "security-events: write",
    ),
    ".github/workflows/scorecard.yml": (
        "ossf/scorecard-action@",
        "publish_results: true",
        "github/codeql-action/upload-sarif@",
        "security-events: write",
        "id-token: write",
    ),
    ".github/dependabot.yml": (
        'package-ecosystem: "github-actions"',
        'interval: "weekly"',
    ),
    "docs/slsa-provenance.md": (
        "cosign verify-blob",
        "gh attestation verify",
        "Legacy local integrity sidecar",
    ),
    "docs/threat-model.md": (
        "## Trust Boundaries",
        "## Threats and Mitigations",
        "Supply-chain poisoning",
    ),
    "docs/security-review-checklist.md": (
        "## Outbound Data",
        "## Dangerous Commands",
        "## Installation Writes",
        "## Rollback",
        "## Supply-Chain Poisoning",
    ),
}


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            failures.append(f"missing required supply-chain file: {rel}")


def action_reference(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped.startswith("uses:") and not stripped.startswith("- uses:"):
        return None
    value = stripped.split("uses:", 1)[1].split("#", 1)[0].strip().strip("'\"")
    if value.startswith("./") or value.startswith("docker://"):
        return None
    if "@" not in value:
        return value, ""
    action, ref = value.rsplit("@", 1)
    return action, ref


def check_action_pins(failures: list[str]) -> None:
    seen: set[str] = set()
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
            reference = action_reference(line)
            if reference is None:
                continue
            action, ref = reference
            base = "/".join(action.split("/")[:2])
            seen.add(base)
            if not SHA_REF_RE.fullmatch(ref):
                failures.append(
                    f"{workflow.relative_to(ROOT).as_posix()}:{line_number} action is not pinned to a full commit SHA: {action}@{ref}"
                )
    missing = REQUIRED_ACTIONS - seen
    if missing:
        failures.append(f"required supply-chain actions are missing: {sorted(missing)}")

    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        content = workflow.read_text(encoding="utf-8")
        checkout_count = content.count("actions/checkout@")
        if checkout_count and content.count("persist-credentials: false") < checkout_count:
            failures.append(f"{workflow.relative_to(ROOT).as_posix()} must disable persisted checkout credentials")


def check_markers(failures: list[str]) -> None:
    for rel, markers in REQUIRED_MARKERS.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"{rel} missing supply-chain marker: {marker}")


def check_secret_scanning_config(failures: list[str]) -> None:
    path = ROOT / ".github" / "secret_scanning.yml"
    if not path.is_file():
        return
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            entries.append(stripped[2:].strip().strip("'\""))
    expected = ["security/redaction-regression-cases.json"]
    if entries != expected:
        failures.append(f"secret scanning exclusions must remain the single reviewed fixture path: {expected}")
    if "synthetic" not in path.read_text(encoding="utf-8").lower():
        failures.append("secret scanning exclusion must explain that its content is synthetic")


def check_scorecard_restrictions(failures: list[str]) -> None:
    path = ROOT / ".github" / "workflows" / "scorecard.yml"
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    if re.search(r"^env:\s*$", content, flags=re.MULTILINE):
        failures.append("scorecard workflow must not define a top-level env block")
    if re.search(r"^\s+-\s+run:\s*", content, flags=re.MULTILINE):
        failures.append("scorecard job may only use actions approved by the Scorecard publisher")


def check_release_immutability(failures: list[str]) -> None:
    content = text(".github/workflows/supply-chain.yml")
    if "--clobber" in content or "--force" in content:
        failures.append("release upload must fail instead of overwriting retained evidence")


def check_legacy_integrity_label(failures: list[str]) -> None:
    content = text("scripts/create_release.py")
    if '"assurance": "local-integrity-only"' not in content:
        failures.append("legacy .sig sidecar must be labeled local-integrity-only")
    if "sigstore.json" not in content:
        failures.append("legacy .sig sidecar must point users to the Sigstore identity bundle")


def check_generated_provenance(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="our-skills-slsa-check-") as tmp_dir:
        tmp = Path(tmp_dir)
        artifact = tmp / "our-skills-v0.0.0.zip"
        byproduct = tmp / "our-skills-v0.0.0.manifest.json"
        output = tmp / "our-skills-v0.0.0.slsa-provenance.json"
        artifact.write_bytes(b"deterministic supply-chain fixture\n")
        byproduct.write_text('{"fixture": true}\n', encoding="utf-8")
        commit = "a" * 40
        result = subprocess.run(
            [
                PYTHON,
                "scripts/generate_slsa_provenance.py",
                "--artifact",
                str(artifact),
                "--output",
                str(output),
                "--source-uri",
                "https://github.com/example/our-skills",
                "--source-commit",
                commit,
                "--workflow-ref",
                "example/our-skills/.github/workflows/supply-chain.yml@refs/heads/main",
                "--invocation-id",
                "https://github.com/example/our-skills/actions/runs/1/attempts/1",
                "--started-on",
                "2026-01-01T00:00:00Z",
                "--finished-on",
                "2026-01-01T00:00:01Z",
                "--byproduct",
                str(byproduct),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"SLSA provenance generator failed: {result.stdout}{result.stderr}".strip())
            return
        statement = json.loads(output.read_text(encoding="utf-8"))
        expected_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if statement.get("_type") != "https://in-toto.io/Statement/v1":
            failures.append("SLSA statement _type is invalid")
        if statement.get("predicateType") != "https://slsa.dev/provenance/v1":
            failures.append("SLSA statement predicateType is invalid")
        subjects = statement.get("subject", [])
        if len(subjects) != 1 or subjects[0].get("digest", {}).get("sha256") != expected_digest:
            failures.append("SLSA statement subject digest does not match the artifact")
        predicate = statement.get("predicate", {})
        build = predicate.get("buildDefinition", {})
        run = predicate.get("runDetails", {})
        if build.get("buildType") != "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1":
            failures.append("SLSA statement buildType is invalid")
        dependencies = build.get("resolvedDependencies", [])
        if not dependencies or dependencies[0].get("digest", {}).get("gitCommit") != commit:
            failures.append("SLSA statement does not resolve the source Git commit")
        if run.get("builder", {}).get("id") != "https://github.com/actions/runner/github-hosted":
            failures.append("SLSA statement builder id is invalid")
        if len(run.get("byproducts", [])) != 1:
            failures.append("SLSA statement does not enumerate build byproducts")


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_action_pins(failures)
    check_markers(failures)
    check_secret_scanning_config(failures)
    check_scorecard_restrictions(failures)
    check_release_immutability(failures)
    check_legacy_integrity_label(failures)
    check_generated_provenance(failures)
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    workflow_count = len(list((ROOT / ".github" / "workflows").glob("*.yml")))
    print(f"[OK] Supply-chain assurance passed across {workflow_count} pinned workflows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
