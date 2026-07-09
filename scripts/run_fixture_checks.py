#!/usr/bin/env python3
"""Validate end-to-end fixture contracts for all registered skills."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills.json"
FIXTURES = ROOT / "fixtures" / "skill_e2e_cases.json"
DOMAINS = ROOT / "roadmap" / "agent_skill_domains.json"
PLATFORM_MATRIX = ROOT / "platforms" / "platform_test_matrix.json"

REQUIRED_DOMAINS = {
    "planning",
    "debugging",
    "testing",
    "code-review",
    "requirements",
    "observability",
    "incident-retro",
}

REQUIRED_PLATFORMS = {"hermes", "claude-code", "codex", "cursor"}


def load_json(path: Path) -> Any:
    if not path.exists():
        raise AssertionError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_nonempty_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise AssertionError(f"{label} must be a non-empty list")
    return value


def contains_any(content: str, terms: list[Any]) -> bool:
    folded = content.casefold()
    return any(str(term).casefold() in folded for term in terms)


def check_fixtures() -> None:
    registry = load_json(REGISTRY)
    fixtures = load_json(FIXTURES)

    registered = {entry["name"]: entry for entry in registry.get("skills", [])}
    if not registered:
        raise AssertionError("registry has no skills")

    cases = require_nonempty_list(fixtures.get("cases"), "fixtures.cases")
    ids = [case.get("id") for case in cases]
    duplicate_ids = [case_id for case_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        raise AssertionError(f"duplicate fixture ids: {', '.join(sorted(duplicate_ids))}")

    by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        skill = case.get("skill")
        if skill not in registered:
            raise AssertionError(f"fixture {case.get('id', '<missing id>')} references unregistered skill: {skill}")
        by_skill[skill].append(case)

    missing = sorted(set(registered) - set(by_skill))
    if missing:
        raise AssertionError(f"registered skills missing fixtures: {', '.join(missing)}")

    for skill, skill_cases in by_skill.items():
        if not 1 <= len(skill_cases) <= 3:
            raise AssertionError(f"{skill} has {len(skill_cases)} fixtures; expected 1-3")

        skill_file = ROOT / registered[skill]["path"] / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        for case in skill_cases:
            case_id = case.get("id", "<missing id>")
            label = f"{skill}/{case_id}"
            prompt = case.get("user_prompt")
            if not isinstance(prompt, str) or len(prompt.strip()) < 10:
                raise AssertionError(f"{label} needs a realistic user_prompt")

            trigger = case.get("trigger")
            if not isinstance(trigger, dict) or trigger.get("expected") != "load":
                raise AssertionError(f"{label} trigger.expected must be 'load'")

            prompt_terms = require_nonempty_list(trigger.get("must_match_prompt_terms"), f"{label} trigger.must_match_prompt_terms")
            skill_terms = require_nonempty_list(trigger.get("must_exist_in_skill_terms"), f"{label} trigger.must_exist_in_skill_terms")
            if not contains_any(prompt, prompt_terms):
                raise AssertionError(f"{label} prompt does not contain any trigger term: {prompt_terms}")
            if not contains_any(content, skill_terms):
                raise AssertionError(f"{label} SKILL.md does not contain any trigger term: {skill_terms}")

            require_nonempty_list(case.get("execution_contract"), f"{label} execution_contract")
            require_nonempty_list(case.get("output_contract"), f"{label} output_contract")

            failure = case.get("failure_branch")
            if not isinstance(failure, dict):
                raise AssertionError(f"{label} failure_branch must be an object")
            for field in ("condition", "expected_behavior"):
                value = failure.get(field)
                if not isinstance(value, str) or len(value.strip()) < 20:
                    raise AssertionError(f"{label} failure_branch.{field} must be specific")

    print(f"[OK] Fixture contracts cover {len(registered)} registered skills with {len(cases)} cases")


def check_blank_domains() -> None:
    registry = load_json(REGISTRY)
    registered = {entry["name"] for entry in registry.get("skills", [])}
    data = load_json(DOMAINS)
    domains = require_nonempty_list(data.get("domains"), "domains")
    found = {entry.get("domain") for entry in domains}
    missing = sorted(REQUIRED_DOMAINS - found)
    extra = sorted(found - REQUIRED_DOMAINS)
    if missing:
        raise AssertionError(f"blank domains missing: {', '.join(missing)}")
    if extra:
        raise AssertionError(f"unexpected blank domains: {', '.join(extra)}")

    for entry in domains:
        domain = entry["domain"]
        status = entry.get("status")
        if status not in {"blank-domain", "registered"}:
            raise AssertionError(f"{domain} status must be blank-domain or registered")
        if not isinstance(entry.get("candidate_skill_name"), str) or not entry["candidate_skill_name"]:
            raise AssertionError(f"{domain} missing candidate_skill_name")
        if status == "registered":
            registered_skill = entry.get("registered_skill") or entry["candidate_skill_name"]
            if registered_skill not in registered:
                raise AssertionError(f"{domain} registered_skill is not in skills.json: {registered_skill}")
        if not isinstance(entry.get("why_missing"), str) or len(entry["why_missing"].strip()) < 20:
            raise AssertionError(f"{domain} needs a specific status rationale")
        require_nonempty_list(entry.get("trigger_prompts"), f"{domain} trigger_prompts")
        require_nonempty_list(entry.get("success_contract"), f"{domain} success_contract")
        require_nonempty_list(entry.get("first_fixture_ideas"), f"{domain} first_fixture_ideas")

    registered_count = sum(1 for entry in domains if entry.get("status") == "registered")
    print(f"[OK] Domain roadmap covers {len(REQUIRED_DOMAINS)} common agent domains ({registered_count} registered)")


def check_platform_matrix() -> None:
    data = load_json(PLATFORM_MATRIX)
    platforms = require_nonempty_list(data.get("platforms"), "platforms")
    found = {entry.get("id") for entry in platforms}
    missing = sorted(REQUIRED_PLATFORMS - found)
    extra = sorted(found - REQUIRED_PLATFORMS)
    if missing:
        raise AssertionError(f"platform matrix missing: {', '.join(missing)}")
    if extra:
        raise AssertionError(f"unexpected platforms: {', '.join(extra)}")

    if "all entries in skills.json" not in data.get("coverage_policy", ""):
        raise AssertionError("platform matrix coverage_policy must apply to all registry entries")

    for entry in platforms:
        platform = entry["id"]
        template = entry.get("install_path_template")
        if not isinstance(template, str) or "SKILL.md" not in template:
            raise AssertionError(f"{platform} needs an install_path_template ending at SKILL.md")
        require_nonempty_list(entry.get("install_verification"), f"{platform} install_verification")
        require_nonempty_list(entry.get("trigger_verification"), f"{platform} trigger_verification")
        require_nonempty_list(entry.get("known_limits"), f"{platform} known_limits")
        failure = entry.get("failure_branch")
        if not isinstance(failure, str) or len(failure.strip()) < 20:
            raise AssertionError(f"{platform} needs a specific failure_branch")

    print(f"[OK] Platform matrix covers {len(REQUIRED_PLATFORMS)} platforms")


def main() -> int:
    try:
        check_fixtures()
        check_blank_domains()
        check_platform_matrix()
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
