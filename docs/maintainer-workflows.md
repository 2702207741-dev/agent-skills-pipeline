# Maintainer Workflows

These workflows define how Codex can assist repository maintenance without
replacing a maintainer's judgment. The agent prepares evidence and a clear
recommendation. A maintainer owns prioritization, merge, publishing, exception,
and disclosure decisions.

## Shared Operating Rules

- Start with the issue, pull request, or explicit maintainer task; do not widen
  scope silently.
- Read the relevant contract, fixture, policy, and previous evidence before
  changing files or recommending a decision.
- Preserve unrelated working-tree changes and never use a destructive reset to
  make validation convenient.
- Treat credentials, personal data, private logs, and proprietary source as
  restricted. Redact before external-model or public-issue use.
- Retain the task, inputs, resources read, commands, output, validation, and
  human decision for a meaningful maintenance action.

## Pull Request Review

**Use when:** a pull request, patch, or diff changes a skill, script, release
surface, installer, security rule, or contributor-facing behavior.

| Stage | Codex action | Evidence or handoff |
|---|---|---|
| Scope | Read the linked task, diff, affected contract, and nearby tests | Files examined and behavior expected to change |
| Risk review | Look first for regressions, unsafe defaults, missing failure paths, and version or compatibility drift | Findings ordered by severity with concrete locations |
| Verification | Select focused checks; require success, failure, and boundary evidence for behavioral changes | Commands, results, and remaining test gap |
| Recommendation | State approve, request changes, or defer | Rationale and the decision a maintainer still owns |

Suggested skills: `code-review-workflow`, `test-design-workflow`,
`systematic-debugging`, and `agent-security-guard`.

**Done means:** the review distinguishes proven defects from assumptions, names
the test evidence, and never treats a green formatter as sufficient evidence of
behavioral safety.

## Issue Triage

**Use when:** a report is incomplete, a behavior needs classification, or a
maintainer needs a reproducible next action.

| Stage | Codex action | Evidence or handoff |
|---|---|---|
| Intake | Check version, environment, minimal reproduction, impact, and data classification | Missing fields and safe reproduction boundary |
| Classification | Separate bug, documentation gap, feature request, configuration problem, and security report | Suggested labels, owner, and related skill or release |
| Reproduction | Reproduce only with public or approved context; reduce the case when possible | Exact command or fixture id and observed result |
| Next action | Propose a narrowly scoped fix, documentation change, or request for information | Acceptance criteria and priority rationale |

Suggested skills: `requirements-clarifier`, `systematic-debugging`,
`planning-workflow`, and `agent-security-guard`.

**Done means:** the issue has a safe, actionable next step. Security-sensitive
reports are redirected to `SECURITY.md`, not investigated through public logs.

## Release Workflow

**Use when:** a maintainer explicitly asks to prepare, verify, or publish a
versioned release.

| Stage | Codex action | Evidence or handoff |
|---|---|---|
| Preflight | Check registry version, every frontmatter version, release policy, changelog, and clean working tree | Exact version and any mismatch |
| Verification | Run `python scripts/verify_release.py` and investigate every failed gate | Full gate result and relevant reports |
| Package | Generate the artifact and review manifest, checksum, SBOM, provenance, signature, and reports | Artifact paths and hashes |
| Recovery | Exercise dry-run install, apply install in a temporary target, doctor, update, and rollback | Audit log and rollback result |
| Decision | Summarize release notes, limitations, and rollback plan | Explicit maintainer authorization before tag or publish |

Suggested skills: `planning-workflow`, `git-workflow-for-agents`,
`skill-pipeline-orchestrator`, and `agent-security-guard`.

**Done means:** publishing is still an explicit maintainer action. An agent does
not create a tag, overwrite `releases/v*/`, or make an external release merely
because the build is valid.

## Security Audit

**Use when:** a change touches secret handling, external dispatch, shell
commands, installation paths, release inputs, or a report raises a security
concern.

| Stage | Codex action | Evidence or handoff |
|---|---|---|
| Scope | Identify data classes, trust boundaries, write targets, and external calls | Audit scope and sensitive data excluded |
| Automated scan | Run the security scanner and policy regressions | Findings, rule ids, and safe-example context |
| Manual review | Inspect command construction, destructive actions, redaction, least privilege, and rollback | Risk explanation and remediation options |
| Escalation | Keep suspected vulnerabilities private and follow `SECURITY.md` | Maintainer-only disclosure recommendation |

Suggested skills: `agent-security-guard`, `cross-model-verification`,
`code-review-workflow`, and `observability-workflow`.

**Done means:** a policy hit is either remediated, documented as a reviewed safe
example, or escalated. It is never silently ignored to make a pipeline green.

## Evidence Replay

v3.2 records these four flows in
[`eval-runs/codex-maintenance/`](../eval-runs/codex-maintenance/). The suite has
three records for each workflow and every record includes the task, input
provenance, skills used, agent behavior, Git-pinned files read, fixed safe
commands, recorded output, final output, human conclusion, and adoption status.

Run the full replay with:

```bash
python scripts/check_maintenance_evidence.py
```

The checker validates commit ancestry and blob identity, then replays a small
allowlisted command set. `scripts/run_rigorbench.py`, CI, and
`python scripts/verify_release.py` all include this gate, so deleting evidence
or reducing any workflow below three passing records blocks the repository.
