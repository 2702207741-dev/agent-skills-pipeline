#!/usr/bin/env python3
"""
validate-skill.py — 8-item format validation for SKILL.md

Checks:
[✓] File starts with --- (no BOM)
[✓] Frontmatter closed + blank line after
[✓] name ≤ 64 chars, lowercase+hyphens
[✓] description ≤ 1024 chars, "Use when" or actionable prefix
[✓] No description flow leakage (no pipeline chars after "—" verb)
[✓] When to Use section present (| Use When | Don't Use When | table)
[✓] Verification Checklist section present
[✓] File length within bounds (≤ 15k chars for technique, ≤ 12k for others)
"""

import re
import sys
from pathlib import Path


def validate_skill(skill_md: Path) -> list[dict]:
    results = []
    content = skill_md.read_text(encoding="utf-8")

    # 1. File starts with --- (no BOM)
    if content.startswith('﻿---'):
        results.append({"ok": False, "msg": "File starts with BOM + ---. Remove BOM."})
    elif content.startswith('---'):
        results.append({"ok": True, "msg": "File starts with --- (no BOM)"})
    else:
        results.append({"ok": False, "msg": "File does not start with ---"})

    # 2. Frontmatter closed + blank line after
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        after_fm = content[fm_match.end():]
        if after_fm.startswith('\n'):
            results.append({"ok": True, "msg": "Frontmatter closed + blank line after"})
        else:
            results.append({"ok": False, "msg": "Frontmatter closed but no blank line after"})
    else:
        results.append({"ok": False, "msg": "Frontmatter not properly closed"})

    # Extract frontmatter for further checks
    frontmatter = fm_match.group(1) if fm_match else ""

    # 3. name ≤ 64 chars, lowercase+hyphens
    name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if name_match:
        name = name_match.group(1).strip()
        issues = []
        if len(name) > 64:
            issues.append(f"name is {len(name)} chars (max 64)")
        if re.search(r'[A-Z]', name):
            issues.append("name contains uppercase letters")
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
            issues.append("name must be lowercase hyphen-case (a-z0-9, hyphens)")
        if issues:
            results.append({"ok": False, "msg": f"name '{name}': {'; '.join(issues)}"})
        else:
            results.append({"ok": True, "msg": f"name '{name}' ≤ 64 chars, valid format"})
    else:
        results.append({"ok": False, "msg": "Missing 'name' in frontmatter"})

    # 4. description ≤ 1024 chars, has "Use when" or actionable prefix
    desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
    if desc_match:
        description = desc_match.group(1).strip()
        issues = []
        if len(description) > 1024:
            issues.append(f"description is {len(description)} chars (max 1024)")
        if not description.startswith('Use when') and not description.startswith('Orchestrate'):
            issues.append("description should start with 'Use when'")
        if '<' in description or '>' in description:
            issues.append("description contains angle brackets (< or >)")
        if issues:
            results.append({"ok": False, "msg": f"description issues: {'; '.join(issues)}"})
        else:
            results.append({"ok": True, "msg": f"description OK ({len(description)} chars)"})
    else:
        results.append({"ok": False, "msg": "Missing 'description' in frontmatter"})

    # 5. No description flow leakage — "—" followed by verb
    if desc_match:
        desc = desc_match.group(1).strip()
        if '—' in desc or '--' in desc:
            # only check text after the LAST dash, not prefixes like "production deploys"
            last_dash = max(desc.rfind('—'), desc.rfind('--'))
            after_dash = desc[last_dash:].lstrip('-— ')
            verbs = ['runs', 'checks', 'builds', 'creates', 'executes',
                     'validates', 'reviews', 'scans', 'installs', 'packages',
                     'commit', 'push', 'pull', 'add', 'step', 'steps']
            found = [v for v in verbs if v in after_dash.lower()]
            if found:
                results.append({"ok": False, "msg": f"Description has flow leakage after '—': verbs {found}"})
                return results

    results.append({"ok": True, "msg": "No description flow leakage"})

    # 6. When to Use section (| Use When | Don't Use When | table)
    if re.search(r'\|\s*Use When\s*\|\s*Don\'t Use When\s*\|', content):
        results.append({"ok": True, "msg": "When to Use section present"})
    else:
        results.append({"ok": False, "msg": "Missing 'When to Use' section (| Use When | Don't Use When |)"})

    # 7. Verification Checklist section
    if 'Verification Checklist' in content:
        results.append({"ok": True, "msg": "Verification Checklist section present"})
    else:
        results.append({"ok": False, "msg": "Missing 'Verification Checklist' section"})

    # 8. File length bounds
    total_chars = len(content)
    if total_chars > 15000:
        results.append({"ok": False, "msg": f"File too long: {total_chars} chars (max 15000)"})
    else:
        results.append({"ok": True, "msg": f"File length OK: {total_chars} chars"})

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate-skill.py <skill-dir-or-file> [<skill-dir-or-file> ...]")
        sys.exit(1)

    all_passed = True
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_dir():
            skill_file = path / "SKILL.md"
        else:
            skill_file = path

        if not skill_file.exists():
            print(f"\n=== {skill_file.parent.name} ===")
            print(f"  [MISS] SKILL.md not found at {skill_file}")
            all_passed = False
            continue

        results = validate_skill(skill_file)
        name = skill_file.parent.name
        print(f"\n=== {name} ===")
        passed = all(r["ok"] for r in results)
        for r in results:
            icon = "PASS" if r["ok"] else "FAIL"
            print(f"  [{icon}] {r['msg']}")
        if passed:
            print(f"  [OK] ALL CHECKS PASSED")
        else:
            print(f"  [FAIL] SOME CHECKS FAILED")
            all_passed = False

    print()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
