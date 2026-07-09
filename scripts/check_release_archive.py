#!/usr/bin/env python3
"""Validate retained release artifacts and their sidecars."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "releases"
ARCHIVE_POLICY = RELEASES / "archive-policy.json"
RELEASE_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def release_dirs() -> list[Path]:
    if not RELEASES.exists():
        raise AssertionError("releases directory is missing")
    dirs = sorted(path for path in RELEASES.iterdir() if path.is_dir() and RELEASE_RE.match(path.name))
    if not dirs:
        raise AssertionError("no versioned release directories found")
    return dirs


def archive_policy() -> dict[str, dict[str, Any]]:
    if not ARCHIVE_POLICY.exists():
        raise AssertionError("releases/archive-policy.json is missing")
    data = load_json(ARCHIVE_POLICY)
    baselines = data.get("release_baselines", [])
    policy = {entry["release"]: entry for entry in baselines}
    if len(policy) != len(baselines):
        raise AssertionError("release archive policy contains duplicate release entries")
    return policy


def top_level_skill_paths(artifact: Path) -> set[str]:
    with zipfile.ZipFile(artifact) as zipf:
        paths = set()
        for name in zipf.namelist():
            parts = Path(name).parts
            if len(parts) == 2 and parts[1] == "SKILL.md":
                paths.add(parts[0])
        return paths


def check_sidecar_hash(subject: dict[str, Any], field: str, path: Path) -> None:
    recorded = subject.get(field)
    if recorded not in sha256_text_variants(path):
        raise AssertionError(f"{path.name}: provenance {field} does not match file hash")


def check_release_dir(release_dir: Path, policy: dict[str, Any]) -> None:
    release = release_dir.name
    version = release[1:]
    manifest = release_dir / f"our-skills-{release}.manifest.json"
    artifact = release_dir / f"our-skills-{release}.zip"
    checksum = release_dir / f"our-skills-{release}.sha256"
    sbom = release_dir / f"our-skills-{release}.sbom.json"
    provenance = release_dir / f"our-skills-{release}.provenance.json"
    signature = release_dir / f"our-skills-{release}.sig"
    release_json = release_dir / "release.json"

    required = [release_json, manifest, artifact, checksum]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise AssertionError(f"{release}: missing required files: {', '.join(missing)}")

    release_data = load_json(release_json)
    manifest_data = load_json(manifest)
    if release_data.get("release") != release:
        raise AssertionError(f"{release}: release.json release does not match directory")
    if release_data.get("semver", version) != version:
        raise AssertionError(f"{release}: release.json semver does not match directory")
    if manifest_data.get("release") != release or manifest_data.get("version") != version:
        raise AssertionError(f"{release}: manifest release/version does not match directory")
    if manifest_data.get("artifact") != artifact.name:
        raise AssertionError(f"{release}: manifest artifact name does not match zip")

    artifact_hash = sha256(artifact)
    if manifest_data.get("sha256") != artifact_hash:
        raise AssertionError(f"{release}: manifest sha256 does not match artifact")
    checksum_text = checksum.read_text(encoding="utf-8-sig").strip()
    if not checksum_text.startswith(artifact_hash):
        raise AssertionError(f"{release}: checksum file does not match artifact")

    manifest_paths = {entry["path"] for entry in manifest_data.get("skills", [])}
    if not manifest_paths:
        raise AssertionError(f"{release}: manifest has no skills")
    expected_formal_skills = policy.get("expected_formal_skills")
    if expected_formal_skills is None:
        raise AssertionError(f"{release}: archive policy is missing expected_formal_skills")
    if len(manifest_paths) != expected_formal_skills:
        raise AssertionError(
            f"{release}: expected {expected_formal_skills} formal skills, found {len(manifest_paths)}"
        )
    forbidden_paths = set(policy.get("required_absent_paths", []))
    forbidden_present = sorted(manifest_paths & forbidden_paths)
    if forbidden_present:
        raise AssertionError(f"{release}: forbidden skill paths present in manifest: {forbidden_present}")
    archive_skill_paths = top_level_skill_paths(artifact)
    if archive_skill_paths != manifest_paths:
        extra = sorted(archive_skill_paths - manifest_paths)
        missing_paths = sorted(manifest_paths - archive_skill_paths)
        raise AssertionError(
            f"{release}: top-level skill dirs do not match manifest "
            f"(extra={extra}, missing={missing_paths})"
        )
    forbidden_in_artifact = sorted(archive_skill_paths & forbidden_paths)
    if forbidden_in_artifact:
        raise AssertionError(f"{release}: forbidden skill paths present in artifact: {forbidden_in_artifact}")

    optional_sidecars = [sbom, provenance, signature]
    if any(path.exists() for path in optional_sidecars) and not all(path.exists() for path in optional_sidecars):
        missing_sidecars = [path.name for path in optional_sidecars if not path.exists()]
        raise AssertionError(f"{release}: incomplete trust sidecars: {', '.join(missing_sidecars)}")

    if sbom.exists():
        sbom_data = load_json(sbom)
        sbom_skills = {entry["path"] for entry in sbom_data.get("components", []) if entry.get("type") == "skill"}
        if sbom_skills != manifest_paths:
            extra = sorted(sbom_skills - manifest_paths)
            missing_paths = sorted(manifest_paths - sbom_skills)
            raise AssertionError(f"{release}: SBOM skills do not match manifest (extra={extra}, missing={missing_paths})")

    report_sidecars = {
        path.name: path
        for path in release_dir.glob(f"our-skills-{release}.*.json")
        if path.name not in {manifest.name, sbom.name, provenance.name}
    }
    if provenance.exists():
        provenance_data = load_json(provenance)
        subject = provenance_data.get("subject", {})
        check_sidecar_hash(subject, "artifact_sha256", artifact)
        check_sidecar_hash(subject, "manifest_sha256", manifest)
        check_sidecar_hash(subject, "checksum_sha256", checksum)
        if sbom.exists():
            check_sidecar_hash(subject, "sbom_sha256", sbom)
        reported = {row["name"]: row["sha256"] for row in subject.get("reports", [])}
        for name, path in report_sidecars.items():
            if reported.get(name) not in sha256_text_variants(path):
                raise AssertionError(f"{release}: provenance report hash does not match {name}")

    if signature.exists():
        signature_data = load_json(signature)
        provenance_data = load_json(provenance)
        expected_signature = hashlib.sha256(canonical_json(provenance_data)).hexdigest()
        if signature_data.get("signature") != expected_signature:
            raise AssertionError(f"{release}: signature does not match canonical provenance")

    print(f"[OK] {release}: {len(manifest_paths)} skills, artifact and sidecars consistent")


def main() -> int:
    try:
        dirs = release_dirs()
        policies = archive_policy()
        release_names = {path.name for path in dirs}
        policy_names = set(policies)
        if release_names != policy_names:
            raise AssertionError(
                "release archive policy must match release directories "
                f"(missing_policy={sorted(release_names - policy_names)}, "
                f"missing_directory={sorted(policy_names - release_names)})"
            )
        for release_dir in dirs:
            check_release_dir(release_dir, policies[release_dir.name])
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1
    print("[OK] Release archive is internally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
