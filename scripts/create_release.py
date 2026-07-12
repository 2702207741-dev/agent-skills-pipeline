#!/usr/bin/env python3
"""Create a versioned release artifact and release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from platform_reports import write_release_reports
from run_model_eval import write_release_model_eval_report


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
ZIP_TIMESTAMP = (2026, 7, 7, 0, 0, 0)


def load_registry() -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    version = registry.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        raise ValueError("skills.json version must be semver")
    expected_release = f"v{version}"
    release_policy = registry.get("release_policy", {})
    if release_policy.get("current_release") != expected_release:
        raise ValueError("release_policy.current_release must match skills.json version")
    for entry in registry.get("skills", []):
        skill_version = entry.get("version")
        if not isinstance(skill_version, str) or not SEMVER_RE.match(skill_version):
            raise ValueError(f"{entry.get('name')} missing semver skill version")
    return registry


def should_include(path: Path) -> bool:
    excluded = {".git", "__pycache__", ".pytest_cache", "dist", "dist-smoke", "dist-release", "tmp", "temp"}
    parts = set(path.relative_to(ROOT).parts)
    if parts & excluded:
        return False
    if path.suffix in {".pyc", ".pyo", ".zip", ".sha256", ".sig"}:
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".manifest.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".sbom.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".provenance.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".marketplace-index.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".quality-dashboard.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".skill-graph-report.json"):
        return False
    if path.name.startswith("our-skills-v") and path.name.endswith(".model-eval-report.json"):
        return False
    return True


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_today() -> str:
    """Use UTC dates so release metadata is independent of the builder's time zone."""
    return datetime.now(timezone.utc).date().isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    except Exception:
        return None
    return result.stdout.strip()


def git_dirty() -> bool | None:
    try:
        result = subprocess.run(["git", "status", "--short"], cwd=ROOT, check=True, capture_output=True, text=True)
    except Exception:
        return None
    return bool(result.stdout.strip())


def release_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*") if path.is_file() and should_include(path))


def source_tree_sha256(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def create_sbom(output_dir: Path, registry: dict[str, Any], release: str, files: list[Path]) -> Path:
    sbom = output_dir / f"our-skills-{release}.sbom.json"
    components: list[dict[str, Any]] = []

    for entry in registry["skills"]:
        skill_file = ROOT / entry["path"] / "SKILL.md"
        components.append(
            {
                "type": "skill",
                "name": entry["name"],
                "version": entry["version"],
                "path": entry["path"],
                "sha256": sha256(skill_file),
            }
        )

    for script in sorted((ROOT / "scripts").glob("*")):
        if script.is_file() and script.suffix in {".py", ".sh"}:
            components.append(
                {
                    "type": "script",
                    "name": script.name,
                    "path": script.relative_to(ROOT).as_posix(),
                    "runtime": "python-stdlib" if script.suffix == ".py" else "bash",
                    "sha256": sha256(script),
                }
            )

    sbom_data = {
        "schema_version": 1,
        "format": "our-skills-minimal-sbom",
        "release": release,
        "generated_at": utc_today(),
        "dependency_policy": "No third-party runtime packages are required; Python scripts use the standard library and install.sh uses Bash/coreutils.",
        "external_runtime_dependencies": [
            {"name": "python", "minimum": "3.10", "scope": "validation, release, marketplace, benchmark, graph"},
            {"name": "bash", "minimum": "4.x", "scope": "scripts/install.sh only"},
            {"name": "git", "minimum": "2.x", "scope": "optional provenance source metadata"},
        ],
        "component_count": len(components),
        "components": components,
        "source_file_count": len(files),
        "source_tree_sha256": source_tree_sha256(files),
    }
    sbom.write_text(json.dumps(sbom_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return sbom


def create_provenance(
    output_dir: Path,
    registry: dict[str, Any],
    release: str,
    artifact: Path,
    manifest: Path,
    checksum: Path,
    sbom: Path,
    source_dirty: bool | None,
    report_sidecars: list[Path],
) -> Path:
    provenance = output_dir / f"our-skills-{release}.provenance.json"
    source_commit = git_output("rev-parse", "HEAD")
    source_tag = git_output("tag", "--points-at", "HEAD")
    builder = ROOT / "scripts" / "create_release.py"
    sbom_data = json.loads(sbom.read_text(encoding="utf-8"))
    provenance_data = {
        "schema_version": 1,
        "predicate_type": "our-skills-release-provenance-v1",
        "release": release,
        "generated_at": utc_today(),
        "subject": {
            "artifact": artifact.name,
            "artifact_sha256": sha256(artifact),
            "manifest": manifest.name,
            "manifest_sha256": sha256(manifest),
            "checksum": checksum.name,
            "checksum_sha256": sha256(checksum),
            "sbom": sbom.name,
            "sbom_sha256": sha256(sbom),
            "reports": [
                {"name": report.name, "sha256": sha256(report)}
                for report in sorted(report_sidecars)
            ],
        },
        "source": {
            "project": registry["project"],
            "version": registry["version"],
            "registry_sha256": sha256(REGISTRY),
            "git_commit": source_commit,
            "git_tags_at_head": sorted(tag for tag in (source_tag or "").splitlines() if tag),
            "git_dirty": source_dirty,
            "source_file_count": sbom_data["source_file_count"],
            "source_tree_sha256": sbom_data["source_tree_sha256"],
        },
        "builder": {
            "script": builder.relative_to(ROOT).as_posix(),
            "script_sha256": sha256(builder),
            "python": sys.version.split()[0],
        },
    }
    provenance.write_text(json.dumps(provenance_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return provenance


def create_signature(output_dir: Path, release: str, provenance: Path) -> Path:
    signature = output_dir / f"our-skills-{release}.sig"
    provenance_data = json.loads(provenance.read_text(encoding="utf-8"))
    sig_data = {
        "schema_version": 1,
        "signature_type": "sha256-canonical-provenance-integrity-v1",
        "assurance": "local-integrity-only",
        "signed": provenance.name,
        "signature": sha256_bytes(canonical_json(provenance_data)),
        "verify": "Recompute SHA256 over canonical JSON of the provenance file, then verify all subject hashes.",
        "identity_signature": "The GitHub OIDC workflow writes a separate .sigstore.json bundle for cryptographic identity verification.",
    }
    signature.write_text(json.dumps(sig_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return signature


def create_artifact(output_dir: Path, registry: dict[str, Any]) -> tuple[Path, Path, Path, Path, Path, Path]:
    version = registry["version"]
    release = f"v{version}"
    release_dir = ROOT / "releases" / release
    for required in ("release.json", "migration-guide.md", "compatibility.md"):
        if not (release_dir / required).exists():
            raise ValueError(f"missing release doc: releases/{release}/{required}")

    source_dirty = git_dirty()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_sidecars = write_release_reports(output_dir, release)
    report_sidecars.append(write_release_model_eval_report(output_dir, release))
    artifact = output_dir / f"our-skills-{release}.zip"
    manifest = output_dir / f"our-skills-{release}.manifest.json"
    checksum = output_dir / f"our-skills-{release}.sha256"
    files = release_files()

    with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as zipf:
        for path in files:
            arcname = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(arcname, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zipf.writestr(info, path.read_bytes())

    release_manifest = {
        "schema_version": 1,
        "release": release,
        "version": version,
        "created_at": utc_today(),
        "artifact": artifact.name,
        "sha256": sha256(artifact),
        "skills": [
            {
                "name": entry["name"],
                "version": entry["version"],
                "path": entry["path"],
                "category": entry["category"],
                "status": entry.get("status", "active"),
                "deprecated": entry.get("deprecated", False),
            }
            for entry in registry["skills"]
        ],
        "reports": [
            {"name": report.name, "sha256": sha256(report)}
            for report in sorted(report_sidecars)
        ],
    }
    manifest.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checksum.write_text(f"{release_manifest['sha256']}  {artifact.name}\n", encoding="utf-8")
    sbom = create_sbom(output_dir, registry, release, files)
    provenance = create_provenance(output_dir, registry, release, artifact, manifest, checksum, sbom, source_dirty, report_sidecars)
    signature = create_signature(output_dir, release, provenance)
    return artifact, manifest, checksum, sbom, provenance, signature


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="dist-release", help="Directory for release artifact and manifest")
    parser.add_argument("--dry-run", action="store_true", help="Validate release metadata without writing artifacts")
    args = parser.parse_args()

    try:
        registry = load_registry()
        if args.dry_run:
            print(f"[OK] Release metadata valid for v{registry['version']}")
            return 0
        artifact, manifest, checksum, sbom, provenance, signature = create_artifact(Path(args.output), registry)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print(f"[OK] Created release artifact: {artifact}")
    print(f"[OK] Created release manifest: {manifest}")
    print(f"[OK] Created release checksum: {checksum}")
    print(f"[OK] Created release SBOM: {sbom}")
    print(f"[OK] Created release provenance: {provenance}")
    print(f"[OK] Created release signature: {signature}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
