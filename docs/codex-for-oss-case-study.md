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
| Release distribution is inspectable | [v3.0.0 GitHub Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v3.0.0) includes artifact and trust sidecars | Manifest, checksum, SBOM, provenance, signature, and report sidecars are retained |
| Safety rules are executable | [`security/`](../security/) and [`scripts/security_scan.py`](../scripts/security_scan.py) | Redaction and dangerous-command regressions are checked in CI |
| Installation can be recovered | [`scripts/marketplace.py`](../scripts/marketplace.py) and [`scripts/install.sh`](../scripts/install.sh) | Dry-run-first install, doctor, update, audit log, and rollback are exercised |
| Governance is part of the repo | [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`SECURITY.md`](../SECURITY.md), templates, and CODEOWNERS | Contributors must describe evidence, compatibility, security, and ownership |

The fastest reproducible check is:

```bash
python scripts/verify_release.py
```

It runs the registry, format, fixture, security, RigorBench, graph, platform,
ecosystem, release archive, publication, packaging, marketplace, rollback, and
review-bot gates in one command.

## What Is Deliberately Not Claimed Yet

The current RigorBench and multi-model data are deterministic replay evidence.
They are valuable because CI can reproduce them without provider credentials,
but they are not presented as historical live Codex sessions or proof of broad
external adoption. The v3.0.0 provenance signature is a deterministic SHA-256
check over canonical provenance, not a Sigstore identity.

Those limits are documented so a reviewer can distinguish measured capability
from future work.

## Next: Real Maintenance Evidence

The next milestone, v3.2, will record at least 12 actual Codex-assisted
maintenance tasks: three each for PR review, issue triage, release workflow,
and security or code-quality audit. Each record will retain:

- the task and safe input context;
- skills triggered and resources read;
- commands and agent steps taken;
- output and verification result;
- a maintainer's adoption, revision, or rejection decision.

This turns the project from replayable skill contracts into a longitudinal,
auditable record of how Codex helps maintain a real OSS repository without
removing human ownership.

## Reviewer Path

1. Start from the [README](../README.md) for the three commands and three
   evidence links.
2. Read [AGENTS.md](../AGENTS.md) for review, release, and security behavior.
3. Use [Maintainer Workflows](maintainer-workflows.md) to inspect the four
   operational flows.
4. Run `python scripts/verify_release.py` and inspect the
   [v3.0.0 release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v3.0.0).
