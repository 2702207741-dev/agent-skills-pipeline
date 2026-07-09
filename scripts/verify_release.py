#!/usr/bin/env python3
"""Run the full one-command release verification gate."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(args: list[str], cwd: Path = ROOT) -> None:
    print("+ " + " ".join(args))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(args, cwd=cwd, check=True, env=env)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text_variants(path: Path) -> set[str]:
    hashes = {sha256(path)}
    if path.suffix not in {".json", ".sha256", ".sig"}:
        return hashes
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return hashes
    lf = text.replace("\r\n", "\n").replace("\r", "\n")
    crlf = lf.replace("\n", "\r\n")
    hashes.add(hashlib.sha256(lf.encode("utf-8")).hexdigest())
    hashes.add(hashlib.sha256(crlf.encode("utf-8")).hexdigest())
    return hashes


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def registry_skill_paths() -> list[str]:
    registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    return [entry["path"] for entry in registry["skills"]]


def registry_skill_count() -> int:
    registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    return len(registry["skills"])


def release_name() -> str:
    registry = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
    version = registry["version"]
    expected = f"v{version}"
    policy = registry.get("release_policy", {})
    if policy.get("current_release") != expected:
        raise AssertionError("release_policy.current_release must match skills.json version")
    return expected


def release_file(release: str, suffix: str) -> str:
    return f"our-skills-{release}.{suffix}"


def release_report_file(release: str, name: str) -> str:
    return f"our-skills-{release}.{name}.json"


def assert_registered_skills_only() -> None:
    expected = registry_skill_count()
    skill_files = sorted(path for path in ROOT.glob("*/SKILL.md"))
    if len(skill_files) != expected:
        raise AssertionError(f"expected {expected} formal skills, found {len(skill_files)}")
    legacy_skill = "cg-" + "extraction-workflow"
    if (ROOT / legacy_skill).exists():
        raise AssertionError("legacy unauthorized skill directory must not exist in the release baseline")


def verify_release_artifact(tmp: Path) -> Path:
    out = tmp / "dist-release"
    run([PYTHON, "scripts/create_release.py", "--output", str(out)])
    verify_release_directory(out)
    return out / release_file(release_name(), "zip")


def verify_release_directory(out: Path) -> None:
    release = release_name()
    artifact = out / release_file(release, "zip")
    manifest = out / release_file(release, "manifest.json")
    checksum = out / release_file(release, "sha256")
    sbom = out / release_file(release, "sbom.json")
    provenance = out / release_file(release, "provenance.json")
    signature = out / release_file(release, "sig")
    marketplace_index = out / release_report_file(release, "marketplace-index")
    quality_dashboard = out / release_report_file(release, "quality-dashboard")
    graph_report = out / release_report_file(release, "skill-graph-report")
    model_eval_report = out / release_report_file(release, "model-eval-report")
    report_sidecars = (marketplace_index, quality_dashboard, graph_report, model_eval_report)
    required = (artifact, manifest, checksum, sbom, provenance, signature, *report_sidecars)
    if not all(path.exists() for path in required):
        missing = [path.name for path in required if not path.exists()]
        raise AssertionError(f"release sidecars missing: {', '.join(missing)}")

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    actual = sha256(artifact)
    if manifest_data["sha256"] != actual:
        raise AssertionError("release manifest sha256 does not match artifact")
    if not checksum.read_text(encoding="utf-8").startswith(actual):
        raise AssertionError("sha256 file does not match artifact")
    sbom_data = json.loads(sbom.read_text(encoding="utf-8"))
    if sbom_data.get("format") != "our-skills-minimal-sbom":
        raise AssertionError("release SBOM format is not recognized")
    if sbom_data.get("component_count", 0) < registry_skill_count():
        raise AssertionError("release SBOM does not enumerate expected components")

    provenance_data = json.loads(provenance.read_text(encoding="utf-8"))
    subject = provenance_data.get("subject", {})
    source = provenance_data.get("source", {})
    reports = {row["name"]: row["sha256"] for row in subject.get("reports", [])}
    expected_subjects = {
        "artifact_sha256": sha256(artifact),
    }
    for field, value in expected_subjects.items():
        if subject.get(field) != value:
            raise AssertionError(f"release provenance {field} does not match sidecar")
    text_subjects = {
        "manifest_sha256": manifest,
        "checksum_sha256": checksum,
        "sbom_sha256": sbom,
    }
    for field, path in text_subjects.items():
        if subject.get(field) not in sha256_text_variants(path):
            raise AssertionError(f"release provenance {field} does not match sidecar")
    for report in report_sidecars:
        if reports.get(report.name) not in sha256_text_variants(report):
            raise AssertionError(f"release provenance report hash does not match {report.name}")
    if source.get("source_tree_sha256") != sbom_data.get("source_tree_sha256"):
        raise AssertionError("release provenance source_tree_sha256 does not match SBOM")
    if source.get("source_file_count") != sbom_data.get("source_file_count"):
        raise AssertionError("release provenance source_file_count does not match SBOM")
    if source.get("git_dirty") is not False:
        raise AssertionError("release provenance must be generated from a clean source tree")

    signature_data = json.loads(signature.read_text(encoding="utf-8"))
    expected_sig = hashlib.sha256(canonical_json(provenance_data)).hexdigest()
    if signature_data.get("signature") != expected_sig:
        raise AssertionError("release signature does not match canonical provenance")

    index_data = json.loads(marketplace_index.read_text(encoding="utf-8"))
    dashboard_data = json.loads(quality_dashboard.read_text(encoding="utf-8"))
    graph_data = json.loads(graph_report.read_text(encoding="utf-8"))
    model_eval_data = json.loads(model_eval_report.read_text(encoding="utf-8"))
    expected_count = registry_skill_count()
    if len(index_data.get("skills", [])) != expected_count:
        raise AssertionError("marketplace index does not enumerate every registered skill")
    if dashboard_data.get("summary", {}).get("skill_count") != expected_count:
        raise AssertionError("quality dashboard skill_count does not match registry")
    if graph_data.get("isolated_skills"):
        raise AssertionError("skill graph report contains isolated skills")
    if graph_data.get("hard_cycles"):
        raise AssertionError("skill graph report contains hard dependency cycles")
    if graph_data.get("stage_coverage", {}).get("missing"):
        raise AssertionError("skill graph report has missing stage coverage")
    required_models = {"codex", "claude", "gemini", "local-model"}
    model_ids = {model["id"] for model in model_eval_data.get("models", [])}
    if model_ids != required_models:
        raise AssertionError("model evaluation report does not cover required model set")
    if any(model.get("pass_rate", 0) < 1.0 for model in model_eval_data.get("models", [])):
        raise AssertionError("model evaluation report contains a pass-rate regression")


def verify_artifact_install_and_rollback(artifact: Path, tmp: Path) -> None:
    extracted = tmp / "artifact-root"
    with zipfile.ZipFile(artifact) as zipf:
        zipf.extractall(extracted)

    market_home = tmp / "market-home"
    run([PYTHON, "scripts/marketplace.py", "install", "--platform", "codex", "--target-root", str(market_home), "--apply"], cwd=extracted)
    run([PYTHON, "scripts/marketplace.py", "doctor", "--platform", "codex", "--target-root", str(market_home), "--strict"], cwd=extracted)
    installed = market_home / ".codex" / "skills" / "skill-review-workflow" / "SKILL.md"
    if not installed.exists():
        raise AssertionError("artifact install did not place skill-review-workflow")

    fresh_install_target = market_home / ".codex" / "skills" / "agent-security-guard"
    if not fresh_install_target.exists():
        raise AssertionError("artifact install did not place agent-security-guard")
    run([PYTHON, "scripts/marketplace.py", "rollback", "--platform", "codex", "--target-root", str(market_home), "--skill", "agent-security-guard", "--apply"], cwd=extracted)
    if fresh_install_target.exists():
        raise AssertionError("fresh-install rollback did not remove created agent-security-guard target")

    run([PYTHON, "scripts/marketplace.py", "update", "--platform", "codex", "--target-root", str(market_home), "--skill", "skill-review-workflow", "--apply"], cwd=extracted)
    run([PYTHON, "scripts/marketplace.py", "rollback", "--platform", "codex", "--target-root", str(market_home), "--skill", "skill-review-workflow", "--apply"], cwd=extracted)
    audit_log = market_home / ".our-skills-audit" / "events.jsonl"
    if not audit_log.exists():
        raise AssertionError("marketplace install/update/rollback did not create an audit log")
    audit_actions = [json.loads(line)["action"] for line in audit_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    for action in ("install", "update", "rollback"):
        if action not in audit_actions:
            raise AssertionError(f"marketplace audit log missing action: {action}")


def main() -> int:
    try:
        assert_registered_skills_only()
        run([PYTHON, "scripts/check_registry.py"])
        run([PYTHON, "scripts/validate-skill.py", *registry_skill_paths()])
        run([PYTHON, "scripts/run_fixture_checks.py"])
        run([PYTHON, "scripts/security_scan.py"])
        run([PYTHON, "scripts/run_rigorbench.py"])
        run([PYTHON, "scripts/check_skill_graph.py"])
        run([PYTHON, "scripts/generate_platform_reports.py", "--check"])
        run([PYTHON, "scripts/generate_example_dataset.py", "--check"])
        run([PYTHON, "scripts/run_model_eval.py", "--check"])
        run([PYTHON, "scripts/check_ecosystem.py"])
        run([PYTHON, "scripts/check_release_archive.py"])
        run([PYTHON, "scripts/check_publication_ready.py"])

        with tempfile.TemporaryDirectory(prefix="our-skills-release-verify-") as tmp_dir:
            tmp = Path(tmp_dir)
            package_out = tmp / "packages"
            run([PYTHON, "scripts/package_skill.py", "--all", str(package_out)])
            expected_packages = registry_skill_count()
            if len(list(package_out.glob("*.zip"))) != expected_packages:
                raise AssertionError(f"package --all did not produce {expected_packages} zip files")

            artifact = verify_release_artifact(tmp)
            verify_artifact_install_and_rollback(artifact, tmp)

        verify_release_directory(ROOT / "releases" / release_name())
        run([PYTHON, "scripts/marketplace.py", "list"])
        run([PYTHON, "scripts/review_bot.py", "--all", "--check", "--output", str(Path(tempfile.gettempdir()) / "our-skills-review-bot-report.json")])
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("[OK] Full release verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
