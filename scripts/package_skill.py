#!/usr/bin/env python3
"""
Skill Packager - Creates a distributable zip file of a skill folder

Usage:
    python scripts/package_skill.py <path/to/skill-folder> [output-directory]
    python scripts/package_skill.py --all [output-directory]

Example:
    python scripts/package_skill.py skill-authoring-workflow
    python scripts/package_skill.py skill-authoring-workflow ./dist
    python scripts/package_skill.py --all ./dist
"""

import json
import zipfile
from pathlib import Path
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("validate_skill", str(Path(__file__).parent / "validate-skill.py"))
validate_skill_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_skill_module)
validate_skill = validate_skill_module.validate_skill
ROOT = Path(__file__).resolve().parents[1]


def package_skill(skill_path, output_dir=None):
    """
    Package a skill folder into a zip file.

    Args:
        skill_path: Path to the skill folder
        output_dir: Optional output directory for the zip file (defaults to current directory)

    Returns:
        Path to the created zip file, or None if error
    """
    skill_path = Path(skill_path).resolve()

    # Validate skill folder exists
    if not skill_path.exists():
        print(f"Error: Skill folder not found: {skill_path}")
        return None

    if not skill_path.is_dir():
        print(f"Error: Path is not a directory: {skill_path}")
        return None

    # Validate SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"Error: SKILL.md not found in {skill_path}")
        return None

    # Run validation before packaging
    print("Validating skill...")
    results = validate_skill(skill_md)
    failed = [result for result in results if not result["ok"]]
    if failed:
        print("Validation failed:")
        for result in failed:
            print(f"  [FAIL] {result['msg']}")
        print("   Please fix the validation errors before packaging.")
        return None
    print("Validation passed\n")

    # Determine output location
    skill_name = skill_path.name
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd()

    zip_filename = output_path / f"{skill_name}.zip"

    # Create the zip file
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the skill directory
            for file_path in skill_path.rglob('*'):
                if file_path.is_file() and should_include(file_path):
                    # Calculate the relative path within the zip
                    arcname = file_path.relative_to(skill_path.parent)
                    zipf.write(file_path, arcname)
                    print(f"  Added: {arcname}")

        print(f"\nSuccessfully packaged skill to: {zip_filename}")
        return zip_filename

    except Exception as e:
        print(f"Error creating zip file: {e}")
    return None


def should_include(file_path):
    excluded_parts = {"__pycache__", ".git", ".pytest_cache"}
    if any(part in excluded_parts for part in file_path.parts):
        return False
    if file_path.suffix in {".pyc", ".pyo"}:
        return False
    return True


def package_registered_skills(output_dir=None):
    registry_path = ROOT / "skills.json"
    if not registry_path.exists():
        print(f"Error: registry not found: {registry_path}")
        return False

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    skills = registry.get("skills", [])
    if not skills:
        print("Error: registry has no skills")
        return False

    ok = True
    for entry in skills:
        skill_path = ROOT / entry["path"]
        result = package_skill(skill_path, output_dir)
        if not result:
            ok = False
    if ok:
        print(f"\nPackaged {len(skills)} registered skills")
    return ok


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/package_skill.py <path/to/skill-folder> [output-directory]")
        print("       python scripts/package_skill.py --all [output-directory]")
        print("\nExample:")
        print("  python scripts/package_skill.py skill-authoring-workflow")
        print("  python scripts/package_skill.py skill-authoring-workflow ./dist")
        print("  python scripts/package_skill.py --all ./dist")
        sys.exit(1)

    if sys.argv[1] == "--all":
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(0 if package_registered_skills(output_dir) else 1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Packaging skill: {skill_path}")
    if output_dir:
        print(f"   Output directory: {output_dir}")
    print()

    result = package_skill(skill_path, output_dir)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
