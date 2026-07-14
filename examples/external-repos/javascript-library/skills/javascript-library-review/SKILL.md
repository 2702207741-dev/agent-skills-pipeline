---
name: javascript-library-review
description: Review a JavaScript library for ESM compatibility, tests, public API changes, and release safety.
version: 1.0.0
---

# JavaScript Library Review

## When to Use

Use this skill when a JavaScript library change affects exported behavior,
runtime compatibility, tests, or release notes.

## Workflow

1. Read the package boundary and changed exports.
2. Run the repository-owned Node tests.
3. Compare behavior, compatibility, and release notes.
4. Return findings before the merge recommendation.

## Verification Checklist

- [ ] Exported behavior is covered by a test.
- [ ] The supported runtime remains explicit.
- [ ] Release-impacting changes are documented.
