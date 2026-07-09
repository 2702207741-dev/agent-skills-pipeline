# Third-Party Skill Specification

Third-party skills must be portable, reviewable, and safe by default. A contribution contains one skill directory with `SKILL.md`, optional `references/`, optional `scripts/`, examples, and an intake record matching `schemas/third-party-skill.schema.json`.

## Required Files

- `SKILL.md` with valid frontmatter: `name`, `description`, and `version`
- At least one success, failure, and boundary example
- Intake metadata using `templates/third-party-skill/intake.json`
- Security notes for secrets, destructive actions, external network use, and data classification

## Frontmatter Rules

- `name` must be lowercase kebab-case and match the directory name.
- `description` must describe trigger conditions, not implementation steps.
- `version` must be semver.

## Compatibility

The skill must declare compatible platforms from:

- `hermes`
- `claude-code`
- `codex`
- `cursor`

Platform-specific behavior must be documented in the skill body or references.

## Evidence Requirements

Before review, run:

```bash
python scripts/review_bot.py --all --check
python scripts/marketplace.py doctor --platform codex --target-root <tmp> --strict
python scripts/run_model_eval.py --check
```

## Deprecation

Deprecated skills must set `status: deprecated`, `deprecated: true`, `replaced_by`, and `migration_path` in `skills.json`.
