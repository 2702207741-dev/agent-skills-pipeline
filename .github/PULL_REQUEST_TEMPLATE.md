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
- [ ] Public Action, unified CLI, external adoption, or maintenance demo

## Evidence

Describe the changed behavior, inputs exercised, and expected output. Link the
fixture, replay record, report, or manual validation that proves the change.

- [ ] `python scripts/review_bot.py --all --check`
- [ ] `python scripts/verify_release.py`
- [ ] `python scripts/check_supply_chain.py` when workflows, dependencies, signing, provenance, or release behavior changed
- [ ] `python scripts/check_external_adoption.py` when Action, CLI, quickstart, examples, or demo behavior changed
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

- [ ] I completed `docs/security-review-checklist.md` or documented why it is not applicable
- [ ] No secrets, private logs, or regulated data are included
- [ ] Data classification is stated: public, internal, or restricted
- [ ] Outbound data and external model/network dispatch are documented, redacted, approved, or absent
- [ ] Dangerous commands are policy-checked, scoped, and reversible where possible
- [ ] Installation writes are dry-run-first, explicit, and audited
- [ ] Rollback behavior and retained recovery data are tested
- [ ] Supply-chain changes keep full-SHA Action pins, least privilege, provenance, and identity verification
- [ ] Consumer-controlled paths remain inside the external workspace and tampering fails closed
- [ ] `security/dangerous-command-policy.json` was followed or the change is not applicable

## Release Impact

- [ ] No release or tag is requested by this PR
- [ ] A release is requested and the version, manifest, checksum, SLSA provenance, Sigstore bundle, GitHub attestation, and rollback plan are included

## CLA

- [ ] I agree to the project CLA.
