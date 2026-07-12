# Codex for OSS Case Study

`our-skills` is a governed skill system for the work that keeps an open-source
repository healthy: reviewing changes, diagnosing failures, designing tests,
clarifying requirements, planning releases, and keeping sensitive operations
inside explicit safety boundaries.

## The Maintainer Problem

Coding agents are useful in OSS only when their work can be inspected and
repeated. A helpful answer is not enough for a maintainer deciding whether to
merge a change, publish an artifact, or trust an installer. The missing layer
is governance around the agent behavior itself:

- Which skill should trigger for a maintainer task?
- What makes the result reviewable instead of persuasive prose?
- How do success, failure, and boundary cases remain visible after a change?
- How do secret handling, dangerous commands, installation, and rollback stay
  auditable?

`our-skills` answers those questions with registry contracts, replay evidence,
security policy, release artifacts, and contributor gates.

## Why Codex Fits

Codex is well suited to the repetitive, evidence-heavy loops that dominate OSS
maintenance. The project gives those loops a durable contract rather than
asking each maintainer to reinvent prompts and safety boundaries.

| Maintainer work | Codex contribution | Maintainer control |
|---|---|---|
| Pull request review | Inspect changed behavior, identify risk, propose focused tests | Decide whether to approve or request changes |
| Issue triage | Reproduce safely, classify scope, find missing context | Prioritize, label, and close issues |
| Release workflow | Check version sync, generate evidence, verify install and rollback | Authorize tags, publishing, and retained artifacts |
| Security audit | Scan for secrets and risky commands, explain policy hits | Decide disclosure, exceptions, and remediation |

[AGENTS.md](../AGENTS.md) makes these boundaries explicit, while
[Maintainer Workflows](maintainer-workflows.md) turns them into repeatable
operating procedures.

## Evidence Already in This Repository

| Claim | Evidence | What a reviewer can verify |
|---|---|---|
| Official skill surface is governed | [`skills.json`](../skills.json) registers 14 active first-party skills | Registry paths, owners, lifecycle fields, and frontmatter versions match |
| Skill behavior has replay coverage | [`traces.json`](../eval-runs/rigorbench-v1.3/traces.json) contains 42 success, failure, and boundary records | Every active skill has three documented outcomes and a checked skill hash |
| Codex is used for maintenance | [`codex-maintenance/traces.json`](../eval-runs/codex-maintenance/traces.json) contains 12 review, triage, release, and security records | Each record pins files to Git blobs, replays an allowlisted command, and records adoption evidence |
| Release distribution is inspectable | [v3.0.0 GitHub Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v3.0.0) plus the [`Supply Chain` workflow](../.github/workflows/supply-chain.yml) | Legacy sidecars remain immutable; new CI builds add SLSA provenance, a GitHub OIDC Cosign bundle, and GitHub artifact attestation |
| Safety rules are executable | [`security/`](../security/), [`scripts/security_scan.py`](../scripts/security_scan.py), and [`scripts/check_supply_chain.py`](../scripts/check_supply_chain.py) | Custom regressions, CodeQL, OpenSSF Scorecard, GitHub secret scanning, and full-SHA Action pins are checked in CI |
| Installation can be recovered | [`scripts/marketplace.py`](../scripts/marketplace.py) and [`scripts/install.sh`](../scripts/install.sh) | Dry-run-first install, doctor, update, audit log, and rollback are exercised |
| Governance is part of the repo | [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`SECURITY.md`](../SECURITY.md), templates, and CODEOWNERS | Contributors must describe evidence, compatibility, security, and ownership |

The fastest reproducible check is:

```bash
python scripts/verify_release.py
```

It runs the registry, format, fixture, security, skill and maintainer-workflow
RigorBench, graph, platform, ecosystem, release archive, publication, packaging,
marketplace, rollback, and review-bot gates in one command.

## What Is Deliberately Not Claimed Yet

The current skill RigorBench and multi-model data are deterministic replay
evidence. The maintenance suite adds real repository-history and live-command
evidence, but it is not a claim of broad external adoption. Older direct-push
changes are explicitly labeled as PR-style reviews rather than assigned invented
GitHub PR numbers. The v3.0.0 `.sig` is a deterministic SHA-256 integrity check
over canonical provenance, not a Sigstore identity. The v3.3 workflow does not
rewrite that release; it creates new identity-backed evidence for its own build.

Those limits are documented so a reviewer can distinguish measured capability
from future work.

## Real Codex Maintenance Evidence

The v3.2 maintenance suite records 12 Codex-assisted repository tasks: three
each for PR-style review, issue triage, release workflow, and security or
code-quality audit. Each record retains:

- the task and prompt provenance;
- skills used, agent behavior, and Git-pinned files read;
- an allowlisted command, recorded output excerpt, and replay marker;
- final output plus a transparent maintainer conclusion and adoption status.

[`scripts/check_maintenance_evidence.py`](../scripts/check_maintenance_evidence.py)
checks structure, coverage, Git ancestry, blob identities, conclusions, and
command replay. [`scripts/run_rigorbench.py`](../scripts/run_rigorbench.py)
includes this suite, so missing or stale maintenance evidence fails CI and the
one-command release gate.

## Stronger Supply-Chain Evidence

The v3.3 trust milestone adds GitHub OIDC signing, Cosign bundles, GitHub
artifact attestations, SLSA provenance, CodeQL, OpenSSF Scorecard, Dependabot,
secret-scanning policy, and a threat model. The remaining next step is external
adopter evidence: prove that another repository can consume these gates without
copying the project structure wholesale.

## Reviewer Path

1. Start from the [README](../README.md) for the three commands and three
   evidence links.
2. Read [AGENTS.md](../AGENTS.md) for review, release, and security behavior.
3. Inspect [Codex Maintenance Evidence](../eval-runs/codex-maintenance/README.md)
   and replay `python scripts/check_maintenance_evidence.py`.
4. Use [Maintainer Workflows](maintainer-workflows.md) to inspect the four
   operational flows.
5. Run `python scripts/check_supply_chain.py` and
   `python scripts/verify_release.py`, then inspect the
   [v3.0.0 release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v3.0.0).
