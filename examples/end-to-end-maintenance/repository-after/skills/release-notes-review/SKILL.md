---
name: release-notes-review
description: Review release-note behavior, regression evidence, and package readiness for this repository before a release.
version: 1.0.0
license: MIT
---

# Release Notes Review

Use issue evidence and local tests to decide whether a release-notes change can
pass the repository release gate.

## When to Use

- Release-note parsing or formatting changes.
- A release gate needs regression and rollback evidence.
- A maintainer reviews a patch tied to a release-note issue.

## Workflow

1. Read the issue and acceptance criteria.
2. Reproduce the old behavior without network access.
3. Review the patch for compatibility and unsafe side effects.
4. Run the full local unit test suite.
5. Approve only when the regression is fixed and the package gate passes.

## Verification Checklist

- [ ] The issue is reproducible before the patch.
- [ ] The acceptance criteria map to tests.
- [ ] The fixed suite passes.
- [ ] No network, secret, or destructive command is introduced.
- [ ] The release artifact, manifest, and checksum verify.
