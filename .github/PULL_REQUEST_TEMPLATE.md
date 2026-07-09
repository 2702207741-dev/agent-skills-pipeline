## Maintainer Context

- Linked issue or maintenance task:
- User or maintainer problem solved:
- Behavior intentionally unchanged:

## Change Classification

- [ ] Skill behavior or trigger
- [ ] Scripts, validation, packaging, or marketplace
- [ ] Documentation or governance only
- [ ] Security-sensitive behavior
- [ ] Release metadata or retained artifact

## Evidence

Describe the changed behavior, inputs exercised, and expected output. Link the
fixture, replay record, report, or manual validation that proves the change.

- [ ] `python scripts/review_bot.py --all --check`
- [ ] `python scripts/verify_release.py`
- [ ] Success, failure, and boundary evidence updated when skill behavior changed
- [ ] Graph, platform, dataset, and model-eval reports refreshed when applicable
- [ ] Marketplace doctor checked when install behavior changed
- [ ] Release artifact and sidecars refreshed only when a maintainer requested a release

## Review Result

- [ ] Findings are ordered by severity and include file/line evidence where relevant
- [ ] Acceptance criteria and regression risk are stated
- [ ] A maintainer decision is recorded: approve, request changes, or defer

## Compatibility

- [ ] Hermes or not applicable
- [ ] Claude Code or not applicable
- [ ] Codex or not applicable
- [ ] Cursor or not applicable
- [ ] Migration or rollback impact is documented

## Security and Data Handling

- [ ] No secrets, private logs, or regulated data are included
- [ ] Data classification is stated: public, internal, or restricted
- [ ] Destructive actions are documented, guarded, and reversible where possible
- [ ] External network or model dispatch is documented, redacted, or absent
- [ ] `security/dangerous-command-policy.json` was followed or the change is not applicable

## Release Impact

- [ ] No release or tag is requested by this PR
- [ ] A release is requested and the version, manifest, checksum, provenance, and rollback plan are included

## CLA

- [ ] I agree to the project CLA.
