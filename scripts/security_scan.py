#!/usr/bin/env python3
"""Scan for likely secrets, dangerous shell patterns, and redaction gate drift."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".json", ".py", ".sh", ".yml", ".yaml", ".txt"}
SHELL_SUFFIXES = {".sh", ".bash", ".zsh", ".ps1", ".yml", ".yaml"}
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", "dist", "temp", "tmp"}
POLICY = ROOT / "security" / "dangerous-command-policy.json"
DANGEROUS_REGRESSION_CASES = ROOT / "security" / "dangerous-command-regression-cases.json"
REDACTION_REGRESSION_CASES = ROOT / "security" / "redaction-regression-cases.json"

SECRET_PATTERNS = [
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("openai_or_stripe_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    (
        "generic_secret_assignment",
        re.compile(r"\b(password|secret|api[_-]?key|token)\s*[:=]\s*['\"]?([A-Za-z0-9_./+=-]{16,})", re.IGNORECASE),
    ),
]

SAFE_EXAMPLE_MARKERS = (
    "...",
    "<SECRET",
    "<token>",
    "sk-xxx",
    "placeholder",
    "example",
    "regex",
    "pattern",
)

REDACTION_TERMS = ("redact", "redaction", "local-only", "safe-to-dispatch", "abort")


def load_json(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_dangerous_policy() -> dict[str, list[tuple[str, re.Pattern[str]]]]:
    data = load_json(POLICY)
    denylist = data.get("denylist", [])
    allowlist = data.get("allowlist", [])
    if not denylist or not allowlist:
        raise AssertionError("dangerous command policy must define denylist and allowlist")

    compiled: dict[str, list[tuple[str, re.Pattern[str]]]] = {"denylist": [], "allowlist": []}
    for section in ("denylist", "allowlist"):
        seen: set[str] = set()
        for entry in data[section]:
            entry_id = entry.get("id")
            pattern = entry.get("pattern")
            rationale = entry.get("rationale")
            if not isinstance(entry_id, str) or not entry_id:
                raise AssertionError(f"{section} entry missing id")
            if entry_id in seen:
                raise AssertionError(f"duplicate {section} id: {entry_id}")
            seen.add(entry_id)
            if not isinstance(pattern, str) or not pattern:
                raise AssertionError(f"{entry_id} missing regex pattern")
            if not isinstance(rationale, str) or len(rationale.strip()) < 20:
                raise AssertionError(f"{entry_id} needs a specific rationale")
            compiled[section].append((entry_id, re.compile(pattern, re.IGNORECASE)))
    return compiled


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def is_safe_example(line: str) -> bool:
    folded = line.casefold()
    return any(marker.casefold() in folded for marker in SAFE_EXAMPLE_MARKERS)


def scan_secrets(files: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in files:
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(read_lines(path), start=1):
            if is_safe_example(line):
                continue
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{line_no}: {name}")
    return findings


def dangerous_matches(line: str, policy: dict[str, list[tuple[str, re.Pattern[str]]]]) -> list[str]:
    if any(pattern.search(line) for _, pattern in policy["allowlist"]):
        return []
    return [entry_id for entry_id, pattern in policy["denylist"] if pattern.search(line)]


def scan_dangerous_shell(files: list[Path], policy: dict[str, list[tuple[str, re.Pattern[str]]]]) -> list[str]:
    findings: list[str] = []
    for path in files:
        if path.suffix.lower() not in SHELL_SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(read_lines(path), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for name in dangerous_matches(stripped, policy):
                findings.append(f"{rel}:{line_no}: {name}")
    return findings


def check_redaction_gate() -> list[str]:
    findings: list[str] = []
    skill_file = ROOT / "cross-model-verification" / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8").casefold()
    for term in ("redact", "local-only", "abort"):
        if term not in content:
            findings.append(f"cross-model-verification/SKILL.md missing redaction gate term: {term}")

    fixture_file = ROOT / "fixtures" / "skill_e2e_cases.json"
    if not fixture_file.exists():
        findings.append("fixtures/skill_e2e_cases.json missing; cannot verify external-model redaction cases")
        return findings

    data = json.loads(fixture_file.read_text(encoding="utf-8"))
    cases = [case for case in data.get("cases", []) if case.get("skill") == "cross-model-verification"]
    if not cases:
        findings.append("cross-model-verification fixtures missing")
        return findings

    for case in cases:
        blob = json.dumps(case, ensure_ascii=False).casefold()
        if not any(term in blob for term in REDACTION_TERMS):
            findings.append(f"cross-model fixture {case.get('id', '<missing id>')} lacks redaction/degraded-mode contract")
    return findings


def classify_redaction_sample(artifact: str) -> str:
    folded = artifact.casefold()
    if "private key material" in folded or "without approval" in folded:
        return "abort"
    if "regulated customer data" in folded or "cannot be removed" in folded:
        return "local-only"
    if "api_key" in folded or "<secret" in folded or "internal host" in folded or "<internal_host>" in folded:
        return "redacted"
    return "safe-to-dispatch"


def check_redaction_regression_cases() -> list[str]:
    findings: list[str] = []
    data = load_json(REDACTION_REGRESSION_CASES)
    cases = data.get("cases", [])
    decisions = {case.get("expected_decision") for case in cases}
    required = {"safe-to-dispatch", "redacted", "local-only", "abort"}
    missing = sorted(required - decisions)
    if missing:
        findings.append(f"redaction regression cases missing decisions: {', '.join(missing)}")
    for case in cases:
        case_id = case.get("id", "<missing id>")
        rationale = case.get("rationale", "")
        if not isinstance(rationale, str) or len(rationale.strip()) < 20:
            findings.append(f"redaction case {case_id} needs an explanatory rationale")
        actual = classify_redaction_sample(str(case.get("artifact", "")))
        if actual != case.get("expected_decision"):
            findings.append(f"redaction case {case_id}: expected {case.get('expected_decision')}, got {actual}")
    return findings


def check_dangerous_command_regression_cases(policy: dict[str, list[tuple[str, re.Pattern[str]]]]) -> list[str]:
    findings: list[str] = []
    data = load_json(DANGEROUS_REGRESSION_CASES)
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return ["dangerous command regression cases must be non-empty"]
    for case in cases:
        case_id = case.get("id", "<missing id>")
        sample = str(case.get("sample", ""))
        expected_policy = case.get("expected_policy")
        matches = dangerous_matches(sample, policy)
        if case.get("kind") == "deny":
            if expected_policy not in matches:
                findings.append(f"dangerous case {case_id}: expected deny policy {expected_policy}, got {matches}")
        elif case.get("kind") == "allow":
            rationale = case.get("rationale", "")
            if not isinstance(rationale, str) or len(rationale.strip()) < 20:
                findings.append(f"allow case {case_id} needs a false-positive rationale")
            if matches:
                findings.append(f"allow case {case_id}: expected no deny match, got {matches}")
        else:
            findings.append(f"dangerous case {case_id}: kind must be allow or deny")
    return findings


def main() -> int:
    try:
        policy = load_dangerous_policy()
        files = iter_text_files()
        findings: list[str] = []
        findings.extend(scan_secrets(files))
        findings.extend(scan_dangerous_shell(files, policy))
        findings.extend(check_redaction_gate())
        findings.extend(check_redaction_regression_cases())
        findings.extend(check_dangerous_command_regression_cases(policy))
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1

    if findings:
        print("[FAIL] Security scan found issues:")
        for finding in findings:
            print(f"  - {finding}")
        return 1

    print(f"[OK] Security scan passed across {len(files)} text files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
