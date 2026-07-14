#!/usr/bin/env python3
"""Validate and package an external repository's agent skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MAX_FILE_BYTES = 1024 * 1024

SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
)

DANGEROUS_PATTERNS = (
    ("root-delete", re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\s+/(?:\s|$)")),
    ("hard-reset", re.compile(r"\bgit\s+reset\s+--hard\b")),
    ("pipe-to-shell", re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba)?sh\b")),
    ("powershell-download-execute", re.compile(r"\bInvoke-WebRequest\b[^\n|]*\|\s*(?:iex|Invoke-Expression)\b", re.IGNORECASE)),
)

SAFE_EXAMPLE_MARKERS = (
    "do not",
    "don't",
    "never ",
    "forbidden",
    "blocked",
    "refuse",
    "deny",
    "synthetic",
    "placeholder",
    "safe example",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"severity": "error", "code": code, "path": path, "message": message}


def relative_path(workspace: Path, value: str, label: str) -> Path:
    if not value or "\\" in value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError(f"{label} must be a safe repository-relative path")
    candidate = workspace / value
    cursor = workspace
    for part in Path(value).parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ValueError(f"{label} must not traverse a symlink")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside the workspace") from exc
    return resolved


def repo_relative(workspace: Path, path: Path) -> str:
    return path.relative_to(workspace).as_posix()


def load_registry(workspace: Path, registry_value: str) -> tuple[Path, dict[str, Any]]:
    registry_path = relative_path(workspace, registry_value, "registry")
    if not registry_path.is_file():
        raise ValueError(f"registry does not exist: {registry_value}")
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"registry is not valid UTF-8 JSON: {registry_value}") from exc
    if not isinstance(registry, dict):
        raise ValueError("registry root must be an object")
    return registry_path, registry


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    content = path.read_text(encoding="utf-8")
    if content.startswith("\ufeff"):
        raise ValueError("SKILL.md must not contain a UTF-8 BOM")
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with a frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"\'')
    return fields, content


def is_safe_example(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in SAFE_EXAMPLE_MARKERS)


def scan_text(path: str, content: str) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if is_safe_example(line):
            continue
        for rule, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                problems.append(issue(rule, f"{path}:{line_number}", "secret-like material is not allowed"))
        for rule, pattern in DANGEROUS_PATTERNS:
            if pattern.search(line):
                problems.append(issue(rule, f"{path}:{line_number}", "dangerous command requires an explicit safe-example marker"))
    return problems


def validate_registry(registry: dict[str, Any]) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    schema_version = registry.get("schema_version", 1)
    project = registry.get("project")
    version = registry.get("version")
    skills = registry.get("skills")
    if schema_version != 1:
        problems.append(issue("registry-schema", "skills.json", "schema_version must be 1 when present"))
    if not isinstance(project, str) or not PROJECT_RE.fullmatch(project):
        problems.append(issue("registry-project", "skills.json", "project must be a portable slug"))
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        problems.append(issue("registry-version", "skills.json", "version must be semantic versioning"))
    if not isinstance(skills, list) or not skills:
        problems.append(issue("registry-skills", "skills.json", "skills must be a non-empty array"))
    elif len(skills) > 200:
        problems.append(issue("registry-size", "skills.json", "registry exceeds the 200-skill gate limit"))
    return problems


def validate_skills(workspace: Path, registry_path: Path, registry: dict[str, Any]) -> tuple[list[dict[str, str]], list[Path]]:
    problems = validate_registry(registry)
    problems.extend(scan_text(repo_relative(workspace, registry_path), registry_path.read_text(encoding="utf-8")))
    skills = registry.get("skills") if isinstance(registry.get("skills"), list) else []
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    package_files: set[Path] = set()

    for index, entry in enumerate(skills):
        label = f"skills[{index}]"
        if not isinstance(entry, dict):
            problems.append(issue("registry-entry", label, "skill entry must be an object"))
            continue
        name = entry.get("name")
        version = entry.get("version")
        path_value = entry.get("path")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            problems.append(issue("skill-name", label, "name must use lowercase kebab-case"))
            continue
        if name in seen_names:
            problems.append(issue("duplicate-name", label, f"duplicate skill name: {name}"))
        seen_names.add(name)
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            problems.append(issue("skill-version", label, "version must be semantic versioning"))
        if not isinstance(path_value, str):
            problems.append(issue("skill-path", label, "path must be a repository-relative string"))
            continue
        if path_value in seen_paths:
            problems.append(issue("duplicate-path", label, f"duplicate skill path: {path_value}"))
        seen_paths.add(path_value)
        try:
            skill_dir = relative_path(workspace, path_value, f"{label}.path")
        except ValueError as exc:
            problems.append(issue("skill-path", label, str(exc)))
            continue
        if skill_dir.is_symlink():
            problems.append(issue("symlink", path_value, "skill directory must not be a symlink"))
            continue
        if not skill_dir.is_dir():
            problems.append(issue("skill-directory", path_value, "skill directory does not exist"))
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            problems.append(issue("skill-file", path_value, "SKILL.md is missing"))
            continue
        try:
            fields, content = parse_frontmatter(skill_file)
        except (UnicodeDecodeError, ValueError) as exc:
            problems.append(issue("frontmatter", repo_relative(workspace, skill_file), str(exc)))
            continue
        if fields.get("name") != name:
            problems.append(issue("frontmatter-name", repo_relative(workspace, skill_file), f"frontmatter name must be {name}"))
        if fields.get("version") != version:
            problems.append(issue("frontmatter-version", repo_relative(workspace, skill_file), f"frontmatter version must be {version}"))
        description = fields.get("description", "")
        if len(description) < 20 or len(description) > 1024:
            problems.append(issue("frontmatter-description", repo_relative(workspace, skill_file), "description must be 20-1024 characters"))
        for heading in ("## When to Use", "## Verification Checklist"):
            if heading not in content:
                problems.append(issue("required-section", repo_relative(workspace, skill_file), f"missing section: {heading}"))

        for file in sorted(skill_dir.rglob("*")):
            rel = repo_relative(workspace, file)
            if file.is_symlink():
                problems.append(issue("symlink", rel, "symlinks are not packaged"))
                continue
            if not file.is_file():
                continue
            if file.stat().st_size > MAX_FILE_BYTES:
                problems.append(issue("file-size", rel, f"file exceeds {MAX_FILE_BYTES} bytes"))
                continue
            package_files.add(file)
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            problems.extend(scan_text(rel, text))

    return problems, sorted(package_files, key=lambda path: repo_relative(workspace, path))


def write_zip(workspace: Path, registry_path: Path, files: list[Path], output_dir: Path, registry: dict[str, Any]) -> tuple[Path, Path, Path]:
    project = registry["project"]
    version = registry["version"]
    artifact = output_dir / f"{project}-v{version}.zip"
    manifest = output_dir / f"{project}-v{version}.manifest.json"
    checksum = output_dir / f"{project}-v{version}.sha256"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files = sorted({registry_path, *files}, key=lambda path: repo_relative(workspace, path))
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in all_files:
            arcname = repo_relative(workspace, path)
            info = zipfile.ZipInfo(arcname, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    file_rows = [
        {
            "path": repo_relative(workspace, path),
            "sha256": sha256(path),
            "size": path.stat().st_size,
        }
        for path in all_files
    ]
    artifact_hash = sha256(artifact)
    manifest_data = {
        "schema_version": 1,
        "kind": "our-skills-external-release-manifest",
        "project": project,
        "version": version,
        "skill_count": len(registry["skills"]),
        "artifact": artifact.name,
        "artifact_sha256": artifact_hash,
        "files": file_rows,
    }
    manifest.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checksum.write_text(f"{artifact_hash}  {artifact.name}\n", encoding="utf-8")
    return artifact, manifest, checksum


def verify_release(artifact: Path, manifest: Path, checksum: Path) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    expected_hash = data["artifact_sha256"]
    if sha256(artifact) != expected_hash:
        raise AssertionError("artifact digest does not match manifest")
    if checksum.read_text(encoding="utf-8").strip() != f"{expected_hash}  {artifact.name}":
        raise AssertionError("checksum sidecar does not match artifact")
    expected_files = {row["path"]: row["sha256"] for row in data["files"]}
    with zipfile.ZipFile(artifact) as archive:
        if set(archive.namelist()) != set(expected_files):
            raise AssertionError("archive entries do not match manifest")
        for name, expected in expected_files.items():
            actual = hashlib.sha256(archive.read(name)).hexdigest()
            if actual != expected:
                raise AssertionError(f"archive entry digest mismatch: {name}")


def ensure_output_isolated(workspace: Path, output_dir: Path, registry_path: Path, registry: dict[str, Any]) -> None:
    sources = [registry_path]
    for index, entry in enumerate(registry.get("skills", [])):
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            sources.append(relative_path(workspace, entry["path"], f"skills[{index}].path"))
    for source in sources:
        if source == output_dir or source in output_dir.parents or output_dir in source.parents:
            raise ValueError("output directory must not overlap the registry or a registered skill path")


def github_output(values: dict[str, str]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".", help="External repository root")
    parser.add_argument("--repository-root", help="Optional boundary that must contain the workspace")
    parser.add_argument("--registry", default="skills.json", help="Registry path relative to the workspace")
    parser.add_argument("--mode", choices=("quality", "release", "all"), default="all")
    parser.add_argument("--output", default=".our-skills-dist", help="Output directory relative to the workspace")
    parser.add_argument("--report", help="Optional JSON report path relative to the workspace")
    args = parser.parse_args()

    try:
        workspace = Path(args.workspace).expanduser().resolve()
        if not workspace.is_dir():
            raise ValueError(f"workspace does not exist: {workspace}")
        repository_root = Path(args.repository_root).expanduser().resolve() if args.repository_root else workspace
        try:
            workspace.relative_to(repository_root)
        except ValueError as exc:
            raise ValueError("workspace resolves outside the repository root") from exc
        registry_path, registry = load_registry(workspace, args.registry)
        problems, files = validate_skills(workspace, registry_path, registry)
        output_dir = relative_path(workspace, args.output, "output")
        ensure_output_isolated(workspace, output_dir, registry_path, registry)
        artifact: Path | None = None
        manifest: Path | None = None
        checksum: Path | None = None
        if not problems and args.mode in {"release", "all"}:
            artifact, manifest, checksum = write_zip(workspace, registry_path, files, output_dir, registry)
            verify_release(artifact, manifest, checksum)

        report = {
            "schema_version": 1,
            "interface_version": 1,
            "kind": "our-skills-external-gate-report",
            "mode": args.mode,
            "status": "pass" if not problems else "fail",
            "project": registry.get("project"),
            "version": registry.get("version"),
            "skill_count": len(registry.get("skills", [])) if isinstance(registry.get("skills"), list) else 0,
            "issue_count": len(problems),
            "issues": problems,
            "release": {
                "artifact": repo_relative(workspace, artifact) if artifact else None,
                "manifest": repo_relative(workspace, manifest) if manifest else None,
                "checksum": repo_relative(workspace, checksum) if checksum else None,
                "verified": bool(artifact),
            },
        }
        report_path: Path | None = None
        if args.report:
            report_path = relative_path(workspace, args.report, "report")
            try:
                report_path.relative_to(output_dir)
            except ValueError as exc:
                raise ValueError("report must be written inside the isolated output directory") from exc
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        values = {
            "interface-version": "1",
            "status": report["status"],
            "skill-count": str(report["skill_count"]),
            "report-path": str(report_path or ""),
            "artifact-path": str(artifact or ""),
            "manifest-path": str(manifest or ""),
            "checksum-path": str(checksum or ""),
        }
        github_output(values)
        if problems:
            for problem in problems:
                print(f"[FAIL] {problem['code']} {problem['path']}: {problem['message']}")
            return 1
        print(f"[OK] External skill quality passed for {report['skill_count']} skill(s)")
        if artifact:
            print(f"[OK] Verified release artifact: {artifact}")
        if report_path:
            print(f"[OK] Wrote report: {report_path}")
        return 0
    except Exception as exc:
        print(f"[FAIL] {exc}")
        github_output(
            {
                "interface-version": "1",
                "status": "fail",
                "skill-count": "0",
                "report-path": "",
                "artifact-path": "",
                "manifest-path": "",
                "checksum-path": "",
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
