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
python scripts/review_bot.py --all --check
python scripts/verify_release.py
```

## Pull Request Expectations

- Explain user-facing behavior.
- Link replay evidence.
- Declare platform compatibility.
- Include security notes for secrets, destructive actions, external network use, and data classification.
- Confirm CLA acceptance.

## Review Standard

The automated review bot is the minimum bar. Human review focuses on unclear triggers, unsafe behavior, missing evidence, and migration risk.
