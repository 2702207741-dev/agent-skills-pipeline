# Threat Model

## Scope and Assets

This model covers first-party skill sources, registry metadata, replay evidence,
security policy, release scripts, GitHub Actions, generated artifacts, install
targets, rollback data, and audit logs. The primary assets are source integrity,
release authenticity, maintainer and user data, reversible installation state,
and the evidence used to decide whether a skill is safe to trust.

The model does not claim that GitHub, Sigstore, an operating system, or an agent
provider cannot be compromised. It defines which evidence this repository
produces so a maintainer can detect substitution, excessive authority, unsafe
writes, and unsupported claims within those external trust assumptions.

## Actors

- Maintainers review and merge changes, publish releases, and handle private
  vulnerability reports.
- Contributors and automation propose changes but are not trusted to publish.
- Users install skills into agent-specific directories and rely on rollback and
  audit records.
- GitHub-hosted runners build artifacts and mint short-lived OIDC identities.
- GitHub artifact attestation and Sigstore Fulcio/Rekor provide identity-bound
  signing and public transparency evidence.
- Coding agents read repository content, run approved checks, and propose
  changes under `AGENTS.md`.

## Trust Boundaries

1. **Contributor to protected source:** pull request content is untrusted until
   review, required CI, and ownership rules accept it.
2. **Repository to runner:** a workflow receives source and a scoped token. A
   compromised Action or workflow edit can affect the build.
3. **Runner to Sigstore and GitHub attestation:** OIDC crosses an external
   service boundary and must be bound to the expected repository, workflow,
   ref, issuer, and artifact digest.
4. **Artifact to installer:** downloaded files are untrusted until checksum,
   identity signature, and provenance verification succeed.
5. **Installer to user filesystem:** previewed writes cross into agent runtime
   directories and must remain explicit, auditable, and reversible.
6. **Local repository to external model or network:** prompts, logs, and source
   leave the local boundary only after classification, redaction, and approval.

## Threats and Mitigations

| Threat | Primary mitigation | Residual risk and required review |
|---|---|---|
| Supply-chain poisoning through a mutable or compromised Action | Every external Action is pinned to a full commit SHA; Dependabot proposes reviewed updates; Scorecard reports dependency and token posture | A pinned commit can still be malicious. Review the upstream release and digest update before merge. |
| Artifact substitution after build | SHA-256 manifest, SLSA subject digest, Cosign keyless bundle, GitHub artifact attestation, and transparency-log proof | A consumer who skips identity and issuer checks can still trust the wrong signer. |
| Workflow token abuse | Default read-only permissions; OIDC and attestation writes exist only in the build job; release `contents: write` is isolated to published-release events | A malicious workflow change can request more access, so workflow and CODEOWNERS review remains mandatory. |
| Secret or private data disclosure | GitHub secret scanning, local secret patterns, redaction regressions, data classification, and explicit dispatch approval | Novel secret formats and human copy/paste can evade patterns. Review outbound context manually. |
| Dangerous command execution | Versioned allow/deny policy, regression cases, dry-run defaults, explicit targets, and agent rules | Policy matching cannot prove every shell expansion safe. Review generated commands and resolved paths. |
| Unreviewed installation writes | Installer and marketplace preview changes before `--apply`; targets are explicit; doctor validates installed state | A compromised local environment may change paths between preview and apply. Use a controlled target and inspect the audit log. |
| Rollback failure or audit deletion | Transaction staging, reverse-order restoration, transaction rollback, strict doctor checks, and hash-chained audit records | Disk loss or deliberate deletion can remove local history. Retain external release evidence and backups for critical use. |
| False assurance from custom evidence | CodeQL, OpenSSF Scorecard, GitHub secret scanning, Sigstore, and GitHub attestations complement repository-specific checks | Standard tools have blind spots. Findings require triage and custom regressions remain necessary. |
| Prompt injection in repository content | Repository files are untrusted input; `AGENTS.md` and maintainer instructions outrank embedded content | A reviewer can still approve unsafe instructions. Keep agent actions scoped and inspect diffs and commands. |

## Verification and Response

Security-sensitive changes use [the security review checklist](security-review-checklist.md)
and run `python scripts/check_supply_chain.py`, `python scripts/security_scan.py`,
and `python scripts/verify_release.py`. Suspected vulnerabilities follow
`SECURITY.md`. A compromised artifact or signing workflow requires stopping
distribution, preserving the workflow run and transparency evidence, rotating
affected credentials if any, fixing the source of compromise, and publishing a
new immutable artifact rather than overwriting evidence silently.

## Known Limits

- The v3.0.0 retained `.sig` is local integrity evidence, not identity signing.
- GitHub-hosted runner and Sigstore service integrity remain external trust
  assumptions.
- Secret scanning and static analysis cannot prove the absence of all secrets or
  vulnerabilities.
- The local-first marketplace is not a federated transparency registry.
