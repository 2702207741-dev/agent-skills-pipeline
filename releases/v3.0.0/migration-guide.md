# Migration Guide: v2.0.0 to v3.0.0

## Scope

v3.0.0 adds ecosystem entry points. It prepares the repository for public contribution and publication, but does not push, tag, or publish without an explicit user request.

## Maintainer Actions

1. Regenerate examples and replay data after trace changes:

```bash
python scripts/generate_example_dataset.py
```

2. Regenerate multi-model replay reports after dataset or model-matrix changes:

```bash
python scripts/run_model_eval.py
```

3. Run the automatic review bot before merging:

```bash
python scripts/review_bot.py --all --check
```

4. Run the full release gate:

```bash
python scripts/verify_release.py
```

## Contributor Actions

1. Read `docs/third-party-skill-spec.md`.
2. Start from `templates/third-party-skill/SKILL.md`.
3. Fill `templates/third-party-skill/intake.json`.
4. Confirm CLA acceptance in the pull request.
5. Add success, failure, and boundary examples.
6. Pass the review bot.

## Compatibility

v3.0.0 keeps the same 14 first-party skill directories and adds ecosystem metadata, docs, examples, and automation around them.
