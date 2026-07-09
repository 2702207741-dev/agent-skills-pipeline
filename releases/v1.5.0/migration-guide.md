# Migration Guide: v1.1.0 to v1.5.0

## Who Should Migrate

Migrate if you use this repository as a skill registry, package source, release artifact, or installer source. v1.5.0 promotes the general-agent workflow expansion to the release line and adds trusted-distribution checks.

## Breaking Changes

No breaking changes for existing skill consumers. The original seven skill paths remain stable. Seven additional skills are now formal registry entries, bringing the registry to 14 skills.

## Required Maintainer Actions

1. Treat `skills.json` as the source of truth for project version, skill versions, paths, and categories.
2. Run the one-command verification gate before publishing:

```bash
python scripts/verify_release.py
```

3. Rebuild release assets from the release source state:

```bash
python scripts/create_release.py --output ./releases/v1.5.0
```

4. Verify installer safety in dry-run and apply modes:

```bash
python scripts/marketplace.py install --platform codex --target-root <temp>
python scripts/marketplace.py install --platform codex --target-root <temp> --apply
python scripts/marketplace.py rollback --platform codex --target-root <temp> --skill skill-review-workflow --apply
```

## Rollback

Use marketplace rollback when an install/update audit event exists:

```bash
python scripts/marketplace.py rollback --platform codex --skill <skill-name> --target-root <target-root> --apply
```

Fresh installs can be rolled back by removing the created target. Updates restore the latest backup recorded under `.our-skills-backups`.

## Verification

The migration is complete when `verify_release.py` passes, `create_release.py` produces `our-skills-v1.5.0.zip` plus all five sidecars, RigorBench replays all 42 traces, and marketplace install/update/rollback writes an audit log.
