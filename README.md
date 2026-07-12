# Agent Skills Pipeline

[![CI](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/ci.yml)
[![Supply Chain](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/supply-chain.yml/badge.svg?branch=main)](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/supply-chain.yml)
[![CodeQL](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/2702207741-dev/agent-skills-pipeline/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/2702207741-dev/agent-skills-pipeline/badge)](https://scorecard.dev/viewer/?uri=github.com/2702207741-dev/agent-skills-pipeline)
[![Release](https://img.shields.io/badge/release-v4.0.0-blue)](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v4.0.0)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Governed, replay-tested maintenance skills that OSS repositories can validate,
install, and ship.**

`our-skills` turns coding-agent instructions into versioned assets with a
registry, execution evidence, security gates, deterministic releases, safe
installation, and a reusable GitHub Action. It is maintenance infrastructure,
not a prompt collection.

Current release: **[v4.0.0](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v4.0.0)**
with 14 active skills, 42 skill traces, and 12 Codex maintenance records.

## 60-Second Review

### Three Commands

```bash
./our-skills quickstart --platform codex --target-root "$PWD/.quickstart-home" --apply
./our-skills doctor
./our-skills demo --check
```

The commands install and replay one skill in an isolated target, diagnose the
repository, and execute the issue-to-review-to-release maintenance flow.
Windows users can run the same commands through `our-skills.cmd`.

### Three Evidence Links

- [42 replayable RigorBench traces](eval-runs/rigorbench-v1.3/traces.json)
- [12 replayable Codex maintainer workflow records](eval-runs/codex-maintenance/README.md)
- [Reusable GitHub Action](action.yml), [external consumer fixture](examples/external-repos/python-library/), and [Issue-to-Release Demo](examples/end-to-end-maintenance/)

Reviewer path: [OSS Reviewer Brief](docs/oss-review.md) |
[Codex for OSS Case Study](docs/codex-for-oss-case-study.md) |
[Maintainer Workflows](docs/maintainer-workflows.md) |
[v4.0.0 Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v4.0.0)

## Five-Minute Quickstart

The first command above previews its writes, installs `code-review-workflow`
into an isolated Codex home, runs strict diagnostics, replays hash-bound
evidence, and writes a machine-readable run record. See the
[Five-Minute Quickstart](docs/quickstart.md) for expected output and cleanup.

## Reusable GitHub Action

Another repository can validate its own `skills.json` and `SKILL.md` files and
produce a deterministic archive, manifest, checksum, and gate report:

```yaml
- uses: 2702207741-dev/agent-skills-pipeline@<FULL_COMMIT_SHA>
  with:
    mode: all
```

Production users should pin a reviewed commit SHA. The
[Action contract](docs/github-action.md) documents inputs and outputs; the
[Python-library fixture](examples/external-repos/python-library/) exercises the
same interface against traversal, tampering, and nondeterministic-build cases.

## Issue-to-Release Demo

The third command in the review path reproduces a reported bug, reviews the
patch and security surface, runs the fixed tests, and verifies the resulting
release gate against a committed JSON oracle. The complete scenario lives in
[`examples/end-to-end-maintenance/`](examples/end-to-end-maintenance/).

## Evidence At A Glance

| Claim | Checked evidence |
|---|---|
| Governed skill surface | `skills.json` owns names, paths, versions, owners, dependencies, and lifecycle state. |
| Behavioral coverage | 42 traces cover success, failure, and boundary behavior for every active skill. |
| Real maintenance work | 12 Git-pinned records cover PR review, issue triage, release, and security audits. |
| Trusted distribution | CI emits checksum, SBOM, SLSA provenance, Sigstore identity bundle, and GitHub attestation. |
| External adoption boundary | A clean consumer repository runs the public Action and deterministic release gate. |
| Recoverable installation | Install and update default to dry-run; applied changes are audited and rollback-tested. |
| Community readiness | MIT, contributing guide, security policy, code of conduct, CLA, templates, CODEOWNERS, and CI are present. |

## Skill System

The detailed registry is [skills.json](skills.json). The 14 active skills are
grouped into three operating surfaces:

| Surface | Skills |
|---|---|
| Build and govern | `skill-authoring-workflow`, `skill-review-workflow`, `skill-pipeline-orchestrator`, `agent-config-reference` |
| Maintainer work | `code-review-workflow`, `systematic-debugging`, `test-design-workflow`, `requirements-clarifier`, `planning-workflow`, `observability-workflow`, `incident-retro-workflow` |
| Trust and operations | `agent-security-guard`, `cross-model-verification`, `git-workflow-for-agents` |

Every registry entry must match its `SKILL.md` frontmatter and retain fixture,
replay, graph, platform, and ownership coverage.

## Safe Installation

```bash
./our-skills list
./our-skills install --platform codex --target-root ~
./our-skills install --platform codex --target-root ~ --apply
./our-skills rollback --platform codex --target-root ~ --skill skill-review-workflow --apply
```

The preview is the default. Writes require explicit `--apply`, updates create a
backup, and every install, update, and rollback writes an audit event.

## Release And Verification

From a fresh clone, the complete release gate is one command:

```bash
./our-skills verify
```

It checks registry and frontmatter sync, fixtures, security policy, supply-chain
configuration, external adoption, RigorBench, the skill graph, generated
reports, release archives, packaging, installation, update, rollback, and
publication readiness.

The retained [v4.0.0 archive](releases/v4.0.0/) contains the zip, manifest,
checksum, SBOM, provenance, integrity signature, marketplace index, quality
dashboard, graph, and model-evaluation sidecars. Tagged GitHub builds add OIDC
Sigstore identity and artifact attestation. See
[SLSA Provenance](docs/slsa-provenance.md) and the
[Threat Model](docs/threat-model.md).

## Documentation

| Need | Start here |
|---|---|
| Understand the project | [Reviewer Brief](docs/oss-review.md) and [Codex for OSS Case Study](docs/codex-for-oss-case-study.md) |
| Install and verify | [Quickstart](docs/quickstart.md) |
| Adopt the Action | [GitHub Action Contract](docs/github-action.md) |
| Operate maintenance flows | [Maintainer Workflows](docs/maintainer-workflows.md) |
| Review security | [Threat Model](docs/threat-model.md) and [Security Checklist](docs/security-review-checklist.md) |
| Contribute a skill | [Contributing](CONTRIBUTING.md) and [Third-Party Skill Spec](docs/third-party-skill-spec.md) |
| Follow the ecosystem direction | [Roadmap to Ecosystem](docs/roadmap-to-ecosystem.md) |

The complete documentation index is in [`docs/`](docs/README.md).

## Scope Boundaries

- Multi-model scoring is deterministic replay, not a claim of live provider API execution.
- The external repository is a verified fixture, not an invented independent adopter.
- The marketplace is local-first; remote registry federation remains roadmap work.
- GitHub-hosted runners, GitHub attestations, and Sigstore are documented trust dependencies.

## License

MIT. See [LICENSE](LICENSE).
