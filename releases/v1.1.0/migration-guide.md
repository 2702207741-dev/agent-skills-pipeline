# Migration Guide: v1.0.0 to v1.1.0

## Who Should Migrate

Migrate if you use the repository as a skill registry, package source, or installer source. v1.1.0 keeps the same 7 official skills and adds stricter release, evaluation, marketplace, and graph checks.

## Breaking Changes

None for skill consumers. Skill paths and `name` fields stay stable.

## Required Maintainer Actions

1. Treat `skills.json` as the source of truth for project version, skill versions, paths, and categories.
2. Run the full validation gate before publishing a release artifact:

```bash
python scripts/check_registry.py
python scripts/validate-skill.py */SKILL.md
python scripts/run_fixture_checks.py
python scripts/security_scan.py
python scripts/run_rigorbench.py
python scripts/check_skill_graph.py
python scripts/create_release.py --output ./dist-release
```

3. Use `python scripts/marketplace.py list` to preview installable skills.
4. Use `python scripts/marketplace.py install --platform codex --target-root <temp-or-home>` for installer smoke tests.

## Rollback

Use the marketplace rollback command when a prior install backup exists:

```bash
python scripts/marketplace.py rollback --platform codex --skill <skill-name> --target-root <target-root>
```

If no marketplace backup exists, reinstall the previous release artifact manually from the archived zip.

## Verification

The migration is complete when `create_release.py` produces `our-skills-v1.1.0.zip`, `run_rigorbench.py` reports all registered skills at or above baseline, and `check_skill_graph.py` reports no dead links, isolated skills, dependency cycles, or uncovered required stages.
