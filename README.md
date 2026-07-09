# Agent Skills Pipeline

[![CI](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/release-v3.0.0-blue)](releases/v3.0.0/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An open-source infrastructure layer for Codex-style coding agents.

`our-skills` turns agent skills from loose prompt snippets into governed, testable,
installable assets. It combines a skill registry, replayable execution evidence,
security gates, release provenance, marketplace-style installation, and
contributor review automation.

## Why Maintainers Should Care

Coding agents are already asked to review pull requests, debug failures, design
tests, clarify requirements, prepare releases, reason about incidents, and keep
security-sensitive work inside guardrails. Those jobs need more than a good
prompt. They need a repeatable operating layer:

- a single registry of what skills exist and where they install;
- trigger and formatting checks before a skill is trusted;
- replayable evidence that each skill works on success, failure, and boundary
  cases;
- security regression tests for secrets, dangerous commands, and external-model
  redaction;
- signed release artifacts with manifest, checksum, SBOM, and provenance;
- dry-run-first installation, update, rollback, doctor checks, and audit logs;
- contributor gates that let new skills enter the ecosystem without lowering the
  bar.

## Current Release

**v3.0.0** is the ecosystem-ready baseline.

It includes:

- 14 active first-party skills in `skills.json`;
- 42 replayable RigorBench traces in `eval-runs/rigorbench-v1.3/traces.json`;
- public docs, task library, replay dataset, and third-party skill intake spec;
- deterministic multi-model replay rows for Codex, Claude, Gemini, and a local
  model adapter;
- release artifacts in `releases/v3.0.0/` with manifest, checksum, SBOM,
  provenance, signature, marketplace index, quality dashboard, skill graph, and
  model-eval sidecars.

For a reviewer-focused one-page summary, see [OSS_REVIEW.md](OSS_REVIEW.md).

## One-Command Verification

Fresh clone, one command:

```bash
python scripts/verify_release.py
```

That command runs the registry, skill format, fixture, security, RigorBench,
graph, platform, ecosystem, release archive, publication-readiness, packaging,
artifact, marketplace, install/update/rollback, and review-bot gates.

For a lighter public-upload check:

```bash
python scripts/check_publication_ready.py
```

## What Reviewers Can Verify Quickly

| Claim | Evidence |
|---|---|
| Active skill system | `skills.json` lists 14 active skills. |
| Real execution coverage | `eval-runs/rigorbench-v1.3/traces.json` has success, failure, and boundary traces for every skill. |
| Replayable scoring | `scripts/run_rigorbench.py` checks trace evidence, stale skill hashes, and regression history. |
| Security posture | `scripts/security_scan.py`, `security/dangerous-command-policy.json`, and redaction regression cases are included. |
| Trusted distribution | `releases/v3.0.0/` includes zip, manifest, checksum, SBOM, provenance, signature, and ecosystem sidecars. |
| Safe installation | `scripts/marketplace.py` and `scripts/install.sh` default to dry-run and support auditable rollback. |
| Community readiness | MIT license, contributing guide, security policy, code of conduct, CLA, CI, review bot, issue templates, PR template, and CODEOWNERS are present. |

## Skill Registry

| # | Skill | Category | Maintainer Workflow |
|---:|---|---|---|
| 1 | `skill-authoring-workflow` | meta | Create or revise `SKILL.md` files from requirements. |
| 2 | `skill-review-workflow` | review | Review finished skills with a checklist and quality scorecard. |
| 3 | `agent-security-guard` | security | Gate secrets, risky commands, injection risks, and sensitive dispatch. |
| 4 | `cross-model-verification` | testing | Run redacted second-opinion checks and degraded-mode handling. |
| 5 | `skill-pipeline-orchestrator` | workflow | Coordinate authoring, review, security, verification, package, and deploy stages. |
| 6 | `git-workflow-for-agents` | git | Standardize agent git workflows from status checks through PR creation. |
| 7 | `agent-config-reference` | reference | Explain portable agent config, skill paths, migration, and troubleshooting. |
| 8 | `code-review-workflow` | code review | Review code, diffs, patches, and PRs for bugs, risks, and missing tests. |
| 9 | `systematic-debugging` | debugging | Reproduce, isolate, fix, and verify failures without guessing. |
| 10 | `test-design-workflow` | testing | Design risk-based success, failure, boundary, and regression tests. |
| 11 | `requirements-clarifier` | requirements | Turn vague requests into testable acceptance criteria. |
| 12 | `planning-workflow` | planning | Plan migrations, refactors, releases, and risky multi-step work with validation gates. |
| 13 | `observability-workflow` | observability | Design logs, metrics, traces, alerts, dashboards, and health checks around failure modes. |
| 14 | `incident-retro-workflow` | incident retro | Create blameless retros with timelines, impact, root causes, and verified action items. |

## Evidence Model

The project treats every skill like a small software component.

1. **Registry contract**: `skills.json` is the source of truth for name, path,
   version, category, owner, lifecycle status, and migration policy.
2. **Static quality**: `scripts/validate-skill.py` checks frontmatter and
   structural requirements across every `SKILL.md`.
3. **Execution evidence**: RigorBench replay traces record input prompt,
   triggered skill, resources read, execution steps, final output, score, and
   the `SKILL.md` hash used by the trace.
4. **Security evidence**: secret scanning, dangerous-command policy, and
   redaction cases are regression-tested.
5. **Graph evidence**: dependency reports check dead links, isolated skills,
   hard cycles, and stage coverage.
6. **Distribution evidence**: release artifacts include manifest, checksum,
   SBOM, provenance, and signature sidecars.

## Marketplace and Install Safety

List available skills:

```bash
python scripts/marketplace.py list
```

Preview an install without writing:

```bash
python scripts/marketplace.py install --platform codex --target-root ~
```

Apply an install only after reviewing the diff:

```bash
python scripts/marketplace.py install --platform codex --target-root ~ --apply
```

Check installed state:

```bash
python scripts/marketplace.py doctor --platform codex --target-root ~ --strict
```

Rollback a skill:

```bash
python scripts/marketplace.py rollback --platform codex --target-root ~ --skill skill-review-workflow --apply
```

`scripts/install.sh` follows the same dry-run-first philosophy:

```bash
bash scripts/install.sh --dry-run
bash scripts/install.sh --apply
```

## Release Policy

The release version is defined by `skills.json` and
`release_policy.current_release`. A release is considered publishable only when:

1. every registered `SKILL.md` frontmatter version is synchronized with
   `skills.json`;
2. `python scripts/verify_release.py` passes;
3. `scripts/create_release.py` writes the artifact, manifest, checksum, SBOM,
   provenance, signature, marketplace index, quality dashboard, graph report,
   and model-eval report;
4. the artifact can be installed, updated, and rolled back through the
   marketplace flow;
5. the official skill count matches the registry. v3.0.0 contains 14 active
   first-party skills.

Generate the retained release artifact:

```bash
python scripts/create_release.py --output ./releases/v3.0.0
```

## Repository Map

```text
our-skills/
|-- skills.json                              # registry and release policy
|-- eval-runs/rigorbench-v1.3/traces.json    # replayable execution traces
|-- benchmarks/                              # RigorBench config and regression history
|-- fixtures/                                # static end-to-end task contracts
|-- graphs/                                  # skill dependency graph
|-- marketplace/                             # local marketplace metadata
|-- platforms/                               # platform compatibility matrix
|-- reports/                                 # quality, graph, and model-eval reports
|-- docs/                                    # public docs and third-party skill spec
|-- examples/                                # task library and replay dataset
|-- evals/                                   # model replay matrix
|-- releases/v3.0.0/                         # retained release artifact and sidecars
|-- security/                                # command policy and redaction regressions
|-- templates/third-party-skill/             # starter template and intake metadata
|-- scripts/                                 # validators, release, marketplace, review bot
|-- *-workflow/SKILL.md                      # first-party agent skills
```

## Codex for OSS Fit

This repository is built around the maintenance work where Codex can help most:

- PR and diff review with risk-first findings;
- systematic debugging and test design;
- issue and requirement clarification;
- release planning and rollback readiness;
- observability and incident review;
- security checks before data leaves the local workspace;
- repeatable packaging and verification for agent-facing assets.

The project is intentionally small enough to inspect, but complete enough to
show how an agent skill ecosystem can be governed like software instead of
copied around as isolated prompts.

## Roadmap

| Milestone | Goal | Verification Signal |
|---|---|---|
| v1.1 | Baseline skill pipeline | 7 official skills, package/install scripts, validation. |
| v1.3 | Real E2E harness | At least 3 replay traces per skill: success, failure, boundary. |
| v1.5 | Security and supply chain hardening | Signed artifacts, SBOM, dry-run installer, redaction and command-policy regressions. |
| v2.0 | Skill platform | Marketplace index, doctor, quality dashboard, graph report, lifecycle policy. |
| v3.0 | Ecosystem entry | Docs site, third-party spec, review bot, multi-model replay, community gates. |

## Limitations

- The current multi-model report uses deterministic replay adapters, not live
  API calls. That keeps CI reproducible and avoids requiring provider secrets.
- The signature is a deterministic SHA-256 signature over canonical provenance,
  not yet a hardware-backed or Sigstore identity.
- The marketplace installer is local-first. Remote registry federation is a
  future direction.

## License

MIT. See [LICENSE](LICENSE).
