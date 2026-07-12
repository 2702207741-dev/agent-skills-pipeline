# Security Policy

## Reporting

Report suspected vulnerabilities privately to the repository maintainer before
opening a public issue. Use GitHub private vulnerability reporting when it is
available. Include the affected skill, script, workflow, platform, commit or
release, minimal reproduction, impact, and whether credentials or published
artifacts may be affected. Do not include a live secret in the report.

Public issues are appropriate only after sensitive details are removed and a
maintainer has confirmed the disclosure path. Maintainers should preserve the
report, workflow run, artifact digest, and signing evidence before remediation.

## Security Gates

Every contribution must pass the applicable gates:

- `python scripts/security_scan.py`
- `python scripts/check_supply_chain.py`
- `python scripts/review_bot.py --all --check`
- `python scripts/verify_release.py`
- `python scripts/marketplace.py doctor --platform codex --target-root <tmp> --strict`

Security-sensitive reviews use
[`docs/security-review-checklist.md`](docs/security-review-checklist.md) and the
trust boundaries in [`docs/threat-model.md`](docs/threat-model.md).

## Standard OSS Security Tooling

- **CodeQL** analyzes Python on pushes, pull requests, a weekly schedule, and
  manual runs. Results are uploaded to GitHub code scanning.
- **OpenSSF Scorecard** evaluates repository and workflow security posture,
  publishes a public result, and uploads SARIF to code scanning.
- **Dependabot** proposes weekly updates for GitHub Actions. Every Action remains
  pinned to a full commit SHA and requires human upstream-release review.
- **GitHub secret scanning** covers the public repository. The only configured
  exclusion is the exact synthetic redaction-regression fixture; the local
  security scanner still checks that file and CI rejects broader exclusions.
- **Sigstore and GitHub artifact attestations** bind CI-built release zips to the
  expected GitHub OIDC workflow identity, source commit, and subject digest.
- **External adoption gate** confines the consumer workspace to its repository,
  rejects traversal and symlinks, scans registry and skill text, and verifies
  every archive entry against a deterministic manifest.

These tools supplement rather than replace the project-specific dangerous
command, redaction, replay, installer, rollback, and release checks.

## Release Trust

The `Supply Chain` workflow builds from a clean checkout, uses full-SHA Action
pins, generates an inspectable SLSA provenance statement, creates a Cosign
keyless `.sigstore.json` bundle, verifies the exact workflow identity and GitHub
OIDC issuer, and creates a GitHub artifact attestation. Release write permission
exists only in the separate job triggered by a published release.

Verification instructions are in
[`docs/slsa-provenance.md`](docs/slsa-provenance.md). The retained v3.0.0 `.sig`
is explicitly local integrity evidence and must not be represented as an
identity-backed signature.

## Prohibited Content

- Live credentials, API keys, passwords, tokens, or private keys
- Unreviewed destructive shell commands
- Hidden external network or model dispatch
- Regulated data in examples, fixtures, replay traces, screenshots, or reports
- Mutable third-party Action tags in executable workflows
- Release artifacts whose source, digest, signer identity, or rollback path
  cannot be established

## External Model Dispatch

External-model evaluation must pass redaction gates and must not send private
repository context unless the data classification allows it and the maintainer
explicitly approves the named destination and data. Prohibited or unredactable
content remains local.

## Consumer Action Boundary

The root composite Action treats its inputs and the caller's repository as
untrusted. `workspace`, `registry`, output, and report paths must remain inside
`GITHUB_WORKSPACE`. The portable gate does not execute commands from consumer
files, follow symlinks, fetch dependencies, or use consumer secrets. Its
release bundle contains only the registry and registered skill files.

Consumers should pin this Action to a reviewed full commit SHA, grant only
`contents: read`, and attach their own OIDC signing policy when promoting the
portable zip to a public release.

## Response

For a suspected source or release compromise: stop publication and installation,
retain the affected commit, run, bundle, attestation, and transparency evidence,
identify the trust boundary that failed, rotate exposed credentials, add a
regression, and publish a new immutable artifact after review. Do not overwrite
or silently relabel retained evidence.
