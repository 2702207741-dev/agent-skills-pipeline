---
name: python-library-review
description: Review changes to this Python library for API compatibility, behavioral regressions, missing tests, and release readiness.
version: 1.0.0
license: MIT
---

# Python Library Review

Review changes to the sample library as a maintainer would review a pull
request. Findings come before summaries and every approval names its evidence.

## When to Use

- A pull request changes public Python functions or their error behavior.
- Tests, packaging metadata, or release notes change.
- A maintainer needs an approve or request-changes recommendation.

Do not use this skill to author a feature from scratch or to publish a release.

## Workflow

1. Read the issue, diff, public functions, and nearby tests.
2. Reproduce the reported behavior with the smallest safe command.
3. Check compatibility, failure handling, boundary cases, and release impact.
4. Run `python -m unittest discover -s tests -v`.
5. Report findings by severity, then state approve or request changes.

## Verification Checklist

- [ ] The issue and affected public behavior are identified.
- [ ] Success, failure, and boundary behavior are covered.
- [ ] Tests pass without network access or credentials.
- [ ] Release impact and rollback are stated.
- [ ] The final recommendation is explicit.
