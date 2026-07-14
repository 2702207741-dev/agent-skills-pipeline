# OSS Reviewer Brief

`our-skills` is an adoptable maintenance layer for coding-agent behavior. It
combines repository-owned skill contracts, replayable execution evidence,
security and release assurance, recoverable installation, and a reusable gate
for other OSS projects.

## One-Minute Path

1. Read the [root README](../README.md) for the three commands and evidence map.
2. Inspect [AGENTS.md](../AGENTS.md) for review, release, and security behavior.
3. Run the [Five-Minute Quickstart](quickstart.md).
4. Inspect the [external fixture suite](../examples/external-repos/)
   and run `./our-skills demo --check`.
5. Run `./our-skills verify`, then inspect the
   [v4.0.0 Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v4.0.0).

## Evidence

| Claim | Repository evidence |
|---|---|
| Governed skill system | [`skills.json`](../skills.json) lists 14 active skills with versions, owners, dependencies, and lifecycle state. |
| Skill execution coverage | [`traces.json`](../eval-runs/rigorbench-v1.3/traces.json) records success, failure, and boundary behavior for every skill. |
| Maintenance evidence | [`codex-maintenance`](../eval-runs/codex-maintenance/) separates 12 Git-pinned reconstructions from schema v2 observed sessions. |
| Standard security tooling | CodeQL, OpenSSF Scorecard, Dependabot, secret scanning, policy regressions, and a threat model run together. |
| Trusted distribution | The Supply Chain workflow emits SLSA provenance, a GitHub OIDC Cosign bundle, and GitHub artifact attestation. |
| External interface | [`action.yml`](../action.yml) runs against Python, JavaScript, and documentation fixtures on three operating systems and rejects tampering and traversal. |
| Recoverable writes | Marketplace install and update use content-bound plans, staged transactions, hash-chained audits, and transaction rollback. |

## Honest Boundaries

- Deterministic replay keeps CI reproducible but is not live provider API execution.
- Commit-derived maintenance reconstruction is not counted as an observed agent session.
- The external consumer is a verified fixture, not an unverified adopter claim.
- The retained local `.sig` is integrity evidence; identity assurance comes from
  the Sigstore bundle and GitHub attestation.
- Registry federation, dependency solving, and portable remote transactions
  remain roadmap work.

For the deeper narrative, continue with the
[Codex for OSS Case Study](codex-for-oss-case-study.md) and
[Maintainer Workflows](maintainer-workflows.md).
