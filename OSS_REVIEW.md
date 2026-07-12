# OSS Reviewer Notes

This repository is an agent skill infrastructure project for Codex-style coding agents.

## v4.0 Release Fast Path

In under a minute, a reviewer can establish the project scope and verify its
maintenance posture:

1. Read the [Codex for OSS Case Study](docs/codex-for-oss-case-study.md) for
   the problem, evidence, and honest scope boundary.
2. Inspect [AGENTS.md](AGENTS.md) and the
   [Maintainer Workflows](docs/maintainer-workflows.md) for explicit Codex
   review, release, and security behavior.
3. Run the [Five-Minute Quickstart](docs/quickstart.md) with
   `./our-skills quickstart --target-root "$PWD/.quickstart-home" --apply`.
4. Run `./our-skills demo --check` and inspect the
   [verified external consumer](examples/external-repos/python-library/).
5. Run `./our-skills verify`, then inspect the [Supply Chain workflow](.github/workflows/supply-chain.yml)
   and [v4.0.0 GitHub Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v4.0.0).

## Project in One Sentence

`our-skills` is an adoptable maintenance layer that combines repository-owned
skill registries, replayable execution, security and release evidence, safe
installation, and a reusable gate for other OSS projects.

## Why It Fits Codex for Open Source

The project targets maintainer work that coding agents are already asked to help with:

- reviewing code, diffs, and PRs for bugs and missing tests;
- debugging failures through reproduce, isolate, fix, and verify loops;
- designing success, failure, boundary, and regression tests;
- clarifying ambiguous requirements into acceptance criteria;
- planning migrations, releases, and risky multi-step changes;
- designing observability around failure modes;
- creating incident retros with root causes and verified action items;
- packaging, installing, updating, rolling back, and auditing agent skills.

## Evidence at a Glance

| Claim | Evidence |
|---|---|
| Active skill system | `skills.json` lists 14 active skills. |
| Real execution coverage | `eval-runs/rigorbench-v1.3/traces.json` has 42 traces: success, failure, and boundary for every skill. |
| Replayable scoring | `scripts/run_rigorbench.py` checks trace evidence and regression history. |
| Real Codex maintenance | `eval-runs/codex-maintenance/traces.json` has 12 Git-pinned review, triage, release, and security records with replayed commands. |
| One-command validation | `python scripts/verify_release.py` runs the full verification gate. |
| Security posture | CodeQL, OpenSSF Scorecard, GitHub secret scanning, Dependabot, custom policy gates, and a threat model are checked together. |
| Trusted distribution | Every accepted `main` build emits SLSA provenance, a GitHub OIDC Cosign bundle, and a GitHub artifact attestation; release upload authority is isolated. |
| Install safety | `scripts/marketplace.py` and `scripts/install.sh` default to dry-run and support auditable rollback. |
| External adoption | `action.yml` runs against a clean consumer fixture, emits deterministic release evidence, exposes checked outputs, and rejects tampering and traversal. |
| Complete workflow | `./our-skills demo --check` reproduces an issue, reviews the fix, runs tests, and reaches a verified release gate. |
| Community readiness | MIT license, contributing guide, security policy, code of conduct, CLA, CI, review bot, issue templates, PR template, and CODEOWNERS are present. |

## Recommended First Commands

```bash
./our-skills quickstart --target-root "$PWD/.quickstart-home" --apply
./our-skills doctor
./our-skills demo --check
```

## Fast Review Path

1. Start with `README.md` for the project shape and the 14-skill registry.
2. Open `releases/v4.0.0/RELEASE_NOTES.md` for the public release summary.
3. Inspect `eval-runs/rigorbench-v1.3/traces.json` to confirm every skill has
   success, failure, and boundary execution evidence.
4. Inspect `eval-runs/codex-maintenance/traces.json` to confirm the four
   maintainer workflows each have three replayable records.
5. Run `./our-skills verify` to reproduce the complete gate.
6. Check `External Action Self-Test`, `CI`, `Supply Chain`, `CodeQL`, and
   `OpenSSF Scorecard` on `main`.

## Scope Boundaries

- The deterministic model evaluation in `reports/model-eval-report.md` uses replay adapters, not live model API calls.
- Public release publishing is intentionally explicit and recorded for v4.0.0.
- The marketplace installer writes only after explicit `--apply` or `--yes`.
- The v3.0.0 `.sig` is legacy local-integrity evidence; identity-backed signing
  begins with v3.3 workflow artifacts and does not rewrite the old release.
- The external repository is a verified fixture, not a fabricated independent
  adopter. The next social proof is a consented public third-party workflow.
