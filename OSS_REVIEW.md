# OSS Reviewer Notes

This repository is an agent skill infrastructure project for Codex-style coding agents.

## v3.1 Fast Path

In under a minute, a reviewer can establish the project scope and verify its
maintenance posture:

1. Read the [Codex for OSS Case Study](docs/codex-for-oss-case-study.md) for
   the problem, evidence, and honest scope boundary.
2. Inspect [AGENTS.md](AGENTS.md) and the
   [Maintainer Workflows](docs/maintainer-workflows.md) for explicit Codex
   review, release, and security behavior.
3. Run `python scripts/verify_release.py`, then inspect the
   [v3.0.0 GitHub Release](https://github.com/2702207741-dev/agent-skills-pipeline/releases/tag/v3.0.0).

## Project in One Sentence

`our-skills` makes agent workflows reviewable and repeatable by combining a skill registry, replayable execution traces, security gates, release evidence, marketplace-style installation, and contributor review automation.

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
| One-command validation | `python scripts/verify_release.py` runs the full verification gate. |
| Security posture | `scripts/security_scan.py`, `security/dangerous-command-policy.json`, and redaction regression cases are included. |
| Trusted distribution | `releases/v3.0.0/` includes manifest, checksum, SBOM, provenance, signature, marketplace index, dashboard, graph, and model-eval sidecars. |
| Install safety | `scripts/marketplace.py` and `scripts/install.sh` default to dry-run and support auditable rollback. |
| Community readiness | MIT license, contributing guide, security policy, code of conduct, CLA, CI, review bot, issue templates, PR template, and CODEOWNERS are present. |

## Recommended First Commands

```bash
python scripts/check_publication_ready.py
python scripts/verify_release.py
python scripts/review_bot.py --all --check
```

## Fast Review Path

1. Start with `README.md` for the project shape and the 14-skill registry.
2. Open `releases/v3.0.0/RELEASE_NOTES.md` for the public release summary.
3. Inspect `eval-runs/rigorbench-v1.3/traces.json` to confirm every skill has
   success, failure, and boundary execution evidence.
4. Run `python scripts/verify_release.py` to reproduce the complete gate.
5. Check the GitHub Actions `CI / validate` workflow on `main`.

## Scope Boundaries

- The deterministic model evaluation in `reports/model-eval-report.md` uses replay adapters, not live model API calls.
- Public release publishing is intentionally explicit and now recorded for v3.0.0.
- The marketplace installer writes only after explicit `--apply` or `--yes`.
