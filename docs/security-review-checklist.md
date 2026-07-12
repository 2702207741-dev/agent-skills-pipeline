# Security Review Checklist

Use this checklist for workflow, release, installer, marketplace, security
policy, external-model, and dependency changes. Record `yes`, `not applicable`,
or a concrete follow-up for every item; an unchecked item is not evidence.

## Outbound Data

- [ ] Every network or external-model destination is named and necessary.
- [ ] Inputs are classified as public, internal, restricted, or prohibited.
- [ ] Credentials, personal data, private source, production logs, and regulated
  data are removed or the operation is stopped.
- [ ] Redaction regression cases cover any newly handled secret or identifier.
- [ ] Human approval exists before restricted context crosses a trust boundary.

## Dangerous Commands

- [ ] Commands are compared with `security/dangerous-command-policy.json`.
- [ ] Shell interpolation, globbing, symlinks, and resolved target paths are
  reviewed, not only the visible command string.
- [ ] Destructive behavior is denied by default or protected by explicit scope,
  confirmation, and recovery evidence.
- [ ] Any policy exception is narrow, documented, owned, and regression-tested.

## Installation Writes

- [ ] Dry-run is the default and shows source, destination, create/replace
  actions, and conflicts before writing.
- [ ] `--apply` is explicit and cannot silently broaden the target root.
- [ ] Existing files are preserved before replacement and partial failure leaves
  a diagnosable state.
- [ ] Doctor checks validate the exact installed content after apply.
- [ ] Install and update events are appended to the audit log.

## Rollback

- [ ] Fresh-install rollback removes only files created by that operation.
- [ ] Update rollback restores the recorded prior content and metadata.
- [ ] Rollback is tested after both a successful operation and an interrupted or
  invalid operation.
- [ ] The recovery command, backup location, and residual manual steps are
  visible before release approval.

## Supply-Chain Poisoning

- [ ] External GitHub Actions use full commit SHAs and least-privilege tokens.
- [ ] Dependency or Action updates link to an upstream release and receive human
  review; mutable tag changes alone are not trusted.
- [ ] The artifact digest matches manifest, SLSA subject, Sigstore bundle, and
  GitHub artifact attestation.
- [ ] Cosign verification checks both the exact workflow identity and GitHub
  OIDC issuer.
- [ ] Provenance resolves the expected source repository, commit, workflow,
  builder, and invocation.
- [ ] Release upload permission is isolated from the unprivileged build job.

## Evidence to Retain

- [ ] `python scripts/security_scan.py` output
- [ ] `python scripts/check_supply_chain.py` output
- [ ] `python scripts/verify_release.py` output
- [ ] CodeQL and OpenSSF Scorecard run links or SARIF artifacts
- [ ] Cosign bundle, GitHub attestation, manifest, checksum, SBOM, and SLSA
  statement for the exact artifact
- [ ] Reviewer conclusion, accepted residual risk, rollback owner, and final
  maintainer decision
