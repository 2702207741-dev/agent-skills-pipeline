# Contributing

Contributions are welcome when they preserve portability, safety, and replayable evidence.

## Add or Update a Skill

1. Start from `templates/third-party-skill/SKILL.md`.
2. Fill out `templates/third-party-skill/intake.json` and validate it against `schemas/third-party-skill.schema.json`.
3. Add or update `skills.json` with owner, status, deprecation metadata, category, summary, and version.
4. Add success, failure, and boundary replay evidence.
5. Update graph dependencies when the skill loads or depends on another skill.
6. Regenerate platform reports and datasets.

## Required Local Checks

```bash
./our-skills doctor
./our-skills verify
```

## Improve External Adoption

Changes to `action.yml`, the unified CLI, quickstart, consumer examples, or the
maintenance demo must also pass:

```bash
python scripts/check_external_adoption.py
```

Consumer fixtures stay repository-independent: they own their own `skills.json`
under `schemas/external-skills.schema.json`, must work from a fresh temporary
copy, and may not import project-internal Python modules. Do not add an adopter
claim without a public workflow and maintainer consent.

## Pull Request Expectations

- Explain user-facing behavior.
- Link replay evidence.
- Declare platform compatibility.
- Include security notes for secrets, destructive actions, external network use, and data classification.
- For public-interface changes, document compatibility, immutable Action pins,
  deterministic artifact evidence, and a negative failure case.
- Confirm CLA acceptance.

## Review Standard

The automated review bot is the minimum bar. Human review focuses on unclear triggers, unsafe behavior, missing evidence, and migration risk.
