#!/usr/bin/env python3
"""Prove the quickstart, composite Action, external gate, CLI, and demo work."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
EXAMPLE = ROOT / "examples" / "external-repos" / "python-library"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_FILES = (
    "action.yml",
    "our-skills",
    "our-skills.cmd",
    "docs/quickstart.md",
    "docs/github-action.md",
    "docs/roadmap-to-ecosystem.md",
    "examples/external-repos/README.md",
    "examples/external-repos/python-library/README.md",
    "examples/external-repos/python-library/skills.json",
    "examples/external-repos/python-library/skills/python-library-review/SKILL.md",
    "examples/external-repos/python-library/.github/workflows/our-skills.yml",
    "examples/end-to-end-maintenance/README.md",
    "examples/end-to-end-maintenance/expected-report.json",
    "scripts/external_repo_check.py",
    "scripts/our_skills.py",
    "scripts/run_maintenance_demo.py",
    "schemas/external-skills.schema.json",
)

ACTION_MARKERS = (
    "using: composite",
    "Run external repository gate",
    "Upload verified release bundle",
    "artifact-path:",
    "manifest-path:",
    "checksum-path:",
    "GITHUB_ACTION_PATH",
    "GITHUB_WORKSPACE",
    '--repository-root "$GITHUB_WORKSPACE"',
)

QUICKSTART_MARKERS = (
    "# Five-Minute Quickstart",
    "./our-skills quickstart",
    "--apply",
    ".our-skills-quickstart-run.json",
    "our-skills.cmd quickstart",
)

ROADMAP_MARKERS = (
    "## Ecosystem Layers",
    "## Federation Model",
    "## Adoption Phases",
    "## Governance",
    "## Codex for OSS Narrative",
)


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    process_env = os.environ.copy()
    process_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        process_env.update(env)
    return subprocess.run(
        args,
        cwd=cwd,
        env=process_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def action_references(path: Path) -> list[tuple[str, str]]:
    refs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:") and not stripped.startswith("- uses:"):
            continue
        value = stripped.split("uses:", 1)[1].split("#", 1)[0].strip().strip("'\"")
        if value.startswith("./"):
            continue
        if "@" not in value:
            refs.append((value, ""))
            continue
        refs.append(tuple(value.rsplit("@", 1)))
    return refs


def parse_github_output(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def run_external_gate(workspace: Path, output_name: str, github_output: Path | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    command = [
        PYTHON,
        "scripts/external_repo_check.py",
        "--workspace",
        str(workspace),
        "--registry",
        "skills.json",
        "--mode",
        "all",
        "--output",
        output_name,
        "--report",
        f"{output_name}/gate-report.json",
    ]
    env = {"GITHUB_OUTPUT": str(github_output)} if github_output else None
    result = run(command, env=env)
    if result.returncode != 0:
        raise AssertionError(f"external repository gate failed: {result.stdout}{result.stderr}")
    report = json.loads((workspace / output_name / "gate-report.json").read_text(encoding="utf-8"))
    outputs = parse_github_output(github_output) if github_output else {}
    return report, outputs


def check_static_contracts(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            failures.append(f"missing external-adoption file: {rel}")

    action = ROOT / "action.yml"
    if action.is_file():
        content = action.read_text(encoding="utf-8")
        for marker in ACTION_MARKERS:
            if marker not in content:
                failures.append(f"action.yml missing marker: {marker}")
        for name, ref in action_references(action):
            if not SHA_RE.fullmatch(ref):
                failures.append(f"action.yml dependency is not pinned to a full commit SHA: {name}@{ref}")

    quickstart = ROOT / "docs" / "quickstart.md"
    if quickstart.is_file():
        content = quickstart.read_text(encoding="utf-8")
        for marker in QUICKSTART_MARKERS:
            if marker not in content:
                failures.append(f"docs/quickstart.md missing marker: {marker}")

    roadmap = ROOT / "docs" / "roadmap-to-ecosystem.md"
    if roadmap.is_file():
        content = roadmap.read_text(encoding="utf-8")
        for marker in ROADMAP_MARKERS:
            if marker not in content:
                failures.append(f"docs/roadmap-to-ecosystem.md missing marker: {marker}")

    launcher = ROOT / "our-skills"
    if launcher.is_file() and not launcher.read_text(encoding="utf-8").startswith("#!/usr/bin/env sh"):
        failures.append("our-skills launcher must have a portable POSIX shell shebang")

    schema_path = ROOT / "schemas" / "external-skills.schema.json"
    if schema_path.is_file():
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                failures.append("external registry schema must use JSON Schema 2020-12")
            if set(schema.get("required", [])) != {"project", "version", "skills"}:
                failures.append("external registry schema required fields do not match the portable gate")
        except json.JSONDecodeError:
            failures.append("schemas/external-skills.schema.json is not valid JSON")

    consumer_workflow = EXAMPLE / ".github" / "workflows" / "our-skills.yml"
    if consumer_workflow.is_file():
        refs = action_references(consumer_workflow)
        bases = {"/".join(name.split("/")[:2]) for name, _ in refs}
        expected = {"actions/checkout", "2702207741-dev/agent-skills-pipeline"}
        if bases != expected:
            failures.append(f"external consumer workflow action set is invalid: {sorted(bases ^ expected)}")
        for name, ref in refs:
            if not SHA_RE.fullmatch(ref):
                failures.append(f"external consumer dependency is not pinned to a full commit SHA: {name}@{ref}")
                continue
            if name == "2702207741-dev/agent-skills-pipeline":
                result = run(["git", "cat-file", "-e", f"{ref}:action.yml"])
                if result.returncode != 0:
                    failures.append("external consumer pins a commit that does not contain action.yml")


def check_runtime_contracts(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="our-skills-external-adoption-") as tmp_dir:
        tmp = Path(tmp_dir)
        first = tmp / "consumer-one"
        second = tmp / "consumer-two"
        tampered = tmp / "consumer-tampered"
        shutil.copytree(EXAMPLE, first)
        shutil.copytree(EXAMPLE, second)
        shutil.copytree(EXAMPLE, tampered)

        tests = run([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=first)
        if tests.returncode != 0:
            failures.append(f"external example unit tests failed: {tests.stdout}{tests.stderr}")

        github_output = tmp / "github-output.txt"
        first_report, outputs = run_external_gate(first, ".gate-one", github_output)
        second_report, _ = run_external_gate(second, ".gate-two")
        if first_report.get("status") != "pass" or first_report.get("skill_count") != 1:
            failures.append("external gate report does not prove one passing skill")
        if second_report.get("status") != "pass":
            failures.append("second external gate run did not pass")

        first_artifact = first / first_report["release"]["artifact"]
        second_artifact = second / second_report["release"]["artifact"]
        if file_sha(first_artifact) != file_sha(second_artifact):
            failures.append("external release artifact is not deterministic across clean workspaces")
        required_outputs = {"status", "skill-count", "report-path", "artifact-path", "manifest-path", "checksum-path"}
        if set(outputs) != required_outputs or outputs.get("status") != "pass" or outputs.get("skill-count") != "1":
            failures.append("GitHub Action output contract is incomplete")
        for key in ("report-path", "artifact-path", "manifest-path", "checksum-path"):
            if not Path(outputs.get(key, "")).is_file():
                failures.append(f"GitHub Action output does not point to a file: {key}")

        skill_file = tampered / "skills" / "python-library-review" / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        skill_file.write_text(text.replace("name: python-library-review", "name: tampered-review", 1), encoding="utf-8")
        negative = run(
            [
                PYTHON,
                "scripts/external_repo_check.py",
                "--workspace",
                str(tampered),
                "--registry",
                "skills.json",
                "--mode",
                "quality",
            ]
        )
        if negative.returncode == 0 or "frontmatter-name" not in negative.stdout:
            failures.append("external gate did not fail closed on a tampered frontmatter name")

        traversal = run(
            [
                PYTHON,
                "scripts/external_repo_check.py",
                "--workspace",
                str(first),
                "--repository-root",
                str(second),
                "--registry",
                "skills.json",
                "--mode",
                "quality",
            ]
        )
        if traversal.returncode == 0 or "outside the repository root" not in traversal.stdout:
            failures.append("external gate did not reject a workspace outside the declared repository boundary")

        overlap = run(
            [
                PYTHON,
                "scripts/external_repo_check.py",
                "--workspace",
                str(first),
                "--registry",
                "skills.json",
                "--mode",
                "all",
                "--output",
                "skills/python-library-review",
            ]
        )
        if overlap.returncode == 0 or "must not overlap" not in overlap.stdout:
            failures.append("external gate did not reject output that overlaps a registered skill")

        external_doctor = run(
            [
                PYTHON,
                "scripts/our_skills.py",
                "doctor",
                "--workspace",
                str(first),
                "--registry",
                "skills.json",
            ]
        )
        if external_doctor.returncode != 0 or "[PASS] doctor completed" not in external_doctor.stdout:
            failures.append(f"unified external doctor failed: {external_doctor.stdout}{external_doctor.stderr}")

        quickstart_home = tmp / "quickstart-home"
        quickstart = run(
            [
                PYTHON,
                "scripts/our_skills.py",
                "quickstart",
                "--platform",
                "codex",
                "--target-root",
                str(quickstart_home),
                "--skill",
                "code-review-workflow",
                "--apply",
            ]
        )
        installed = quickstart_home / ".codex" / "skills" / "code-review-workflow" / "SKILL.md"
        replay = quickstart_home / ".our-skills-quickstart-run.json"
        if quickstart.returncode != 0 or not installed.is_file() or not replay.is_file():
            failures.append(f"five-minute quickstart failed: {quickstart.stdout}{quickstart.stderr}")

        demo = run([PYTHON, "scripts/run_maintenance_demo.py", "--check"])
        if demo.returncode != 0:
            failures.append(f"maintenance demo failed: {demo.stdout}{demo.stderr}")


def main() -> int:
    failures: list[str] = []
    check_static_contracts(failures)
    try:
        check_runtime_contracts(failures)
    except Exception as exc:
        failures.append(str(exc))
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("[OK] External adoption gate passed: Action, CLI, quickstart, deterministic release, tamper rejection, and demo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
