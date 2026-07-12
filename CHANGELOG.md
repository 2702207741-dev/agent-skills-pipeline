# Changelog

## Unreleased

### Added

- Root composite GitHub Action for repository-independent skill quality and
  deterministic release verification, with pinned dependencies and documented
  inputs/outputs.
- Cross-platform `our-skills` CLI with doctor, verify, marketplace, replay,
  quickstart, and maintenance-demo commands.
- Five-minute isolated quickstart, verified external Python repository fixture,
  and a complete issue-to-PR-review-to-release-gate executable scenario.
- External-adoption regression gate covering deterministic builds, Action
  outputs, path traversal, tampered metadata, installation, replay, and demo.
- Ecosystem roadmap for repository conformance, signed registry federation,
  transactional marketplace behavior, evidence exchange, and governance.

- GitHub OIDC supply-chain workflow with Cosign keyless blob signing, immediate
  identity verification, GitHub artifact attestation, and release-only upload
  authority.
- SLSA provenance v1 generator and a CI gate that validates artifact digest,
  source commit, workflow, builder, invocation, and byproducts.
- CodeQL, OpenSSF Scorecard, Dependabot, and narrow GitHub secret-scanning
  configuration with all executable Actions pinned to full commit SHAs.
- Threat model, supply-chain verification guide, and security review checklist
  covering outbound data, dangerous commands, install writes, rollback, and
  supply-chain poisoning.

### Changed

- Labeled the historical `.sig` sidecar as local integrity evidence and reserved
  `.sigstore.json` plus GitHub attestation for identity-backed assurance.
- Added supply-chain assurance to CI, one-command release verification, review
  bot, ecosystem, publication, and full regression gates.
- Added external adoption to CI, review bot, one-command verification,
  publication checks, and the public documentation entry point.

- Reworked the public README into an English, reviewer-oriented project entry
  point with CI badge, release status, one-command verification, evidence map,
  skill registry, install safety, release policy, and Codex for OSS fit.
- Clarified v3.0.0 publishing metadata so the retained release can be promoted
  from a local artifact baseline to a public GitHub tag and release.

### Fixed

- Removed mojibake from the public changelog and README so the repository renders
  cleanly on GitHub.

## 3.0.0 - 2026-07-08

### Added

- `docs/index.html`: public documentation entry for marketplace, doctor,
  quality, replay, and contribution workflows.
- `examples/task-library.json` and `examples/replay-dataset.json`: generated
  public examples from saved agent traces.
- `docs/third-party-skill-spec.md` and
  `schemas/third-party-skill.schema.json`: third-party skill intake and
  compatibility specification.
- `templates/third-party-skill/`: starter skill template and intake metadata for
  outside contributors.
- `scripts/review_bot.py` and `.github/workflows/skill-review-bot.yml`:
  automatic review gates for registry, format, fixtures, security, replay,
  graph, platform reports, datasets, model evaluation, and ecosystem checks.
- `evals/model_matrix.json`, `scripts/run_model_eval.py`, and
  `reports/model-eval-report.json`: deterministic multi-model replay evaluation
  for Codex, Claude, Gemini, and a local model row.
- Community files: `CONTRIBUTING.md`, `CLA.md`, `SECURITY.md`,
  pull-request template, issue templates, CODEOWNERS, and
  `docs/review-checklist.md`.

### Changed

- `scripts/create_release.py` now emits a model-evaluation sidecar in addition
  to the v2 platform sidecars.
- `scripts/verify_release.py`, CI, and `scripts/test_all.sh` now verify
  ecosystem assets, example datasets, model evaluation, and review-bot gates.
- `skills.json` records v3 ecosystem policy and release metadata.

## 2.0.0 - 2026-07-08

### Added

- `marketplace/index.json`: local marketplace index with skill versions,
  platform paths, dependencies, quality scores, owners, and lifecycle status.
- `scripts/marketplace.py doctor`: diagnostics for registry/index sync, source
  metadata, dependency coverage, platform paths, trigger metadata, and installed
  versions.
- `reports/quality-dashboard.json` and `.md`: per-skill pass rates,
  regressions, owners, last updates, lifecycle status, and risk levels.
- `reports/skill-graph-report.json` and `.md`: Mermaid dependency graph plus
  isolated-skill, hard-cycle, and stage-coverage checks.
- `scripts/platform_reports.py` and `scripts/generate_platform_reports.py`:
  shared generation and freshness checks for platform reports.
- `skills.json` deprecation policy with owner, status, deprecated,
  replaced-by, and migration-path metadata.

### Changed

- `scripts/create_release.py` now generates marketplace index, quality
  dashboard, and graph report sidecars for every release artifact.
- `scripts/verify_release.py`, CI, and `scripts/test_all.sh` now verify platform
  reports and strict marketplace doctor checks.

## 1.5.0 - 2026-07-08

### Added

- `skills.json`: single source of truth for the expanded 14-skill registry.
- General-agent workflow skills: `code-review-workflow`,
  `systematic-debugging`, `test-design-workflow`, `requirements-clarifier`,
  `planning-workflow`, `observability-workflow`, and
  `incident-retro-workflow`.
- `scripts/check_registry.py`: verifies registry entries, directories,
  frontmatter names, and semver metadata.
- `fixtures/skill_e2e_cases.json`: end-to-end task contracts for every
  registered skill.
- `roadmap/agent_skill_domains.json`: general-agent domain roadmap.
- `platforms/platform_test_matrix.json`: install and trigger verification
  matrix for Hermes, Claude Code, Codex, and Cursor.
- `scripts/run_fixture_checks.py`: fixture, blank-domain, and platform-matrix
  checks.
- `scripts/security_scan.py`: secret scanning, policy-backed dangerous command
  scanning, external-model redaction drift, and security regression cases.
- `security/dangerous-command-policy.json`,
  `security/dangerous-command-regression-cases.json`, and
  `security/redaction-regression-cases.json`.
- `releases/v1.5.0/`: release manifest, migration guide, compatibility table,
  artifact, checksum, SBOM, provenance, and signature.
- `scripts/create_release.py`: release artifact generator.
- `scripts/verify_release.py`: one-command release verification.
- `eval-runs/rigorbench-v1.3/traces.json`: replayable E2E traces with
  success, failure, and boundary coverage.
- `benchmarks/rigorbench.json` and `benchmarks/regression-history.json`:
  replay baseline and regression history.
- `scripts/run_rigorbench.py`: replay and stale-trace checks.
- `marketplace/manifest.json` and `scripts/marketplace.py`: dry-run-default
  list/install/update/rollback marketplace installer with diff preview and
  audit log.
- `graphs/skill_graph.json` and `scripts/check_skill_graph.py`: dependency graph
  and graph-health checks.
- CI workflow for registry validation, skill validation, whitespace, package
  smoke test, release smoke test, marketplace smoke test, and installer dry-run.

### Changed

- README, release metadata, compatibility docs, CI, packaging, and release
  verification now derive expected skill counts from `skills.json`.
- README documents release policy and the industrial roadmap.
- `scripts/install.sh` reads `skills.json`, defaults to dry-run, requires
  `--apply` or `--yes` before writing, previews diffs, writes audit events, and
  backs up existing targets.
- `scripts/marketplace.py` defaults to dry-run, requires `--apply` before
  writing, previews diffs, filters bytecode caches, and supports auditable
  rollback.
- `scripts/package_skill.py` can package every registered skill with `--all`.
- Release verification derives artifact names from `skills.json`.
- Removed the legacy unofficial eighth-skill benchmark reference.

## 1.1.0 - 2026-07-07

### Added

- Retained 7-skill production baseline with release archive, manifest, checksum,
  SBOM, provenance, and signature sidecars.
- Archive policy checks to make sure historical release artifacts do not drift
  to newer registry contents.

## 1.0.0 - 2026-07-06

### Added

- Initial 7-skill pipeline for AI agent workflows:
  `agent-security-guard`, `cross-model-verification`,
  `skill-pipeline-orchestrator`, `skill-authoring-workflow`,
  `skill-review-workflow`, `git-workflow-for-agents`, and
  `agent-config-reference`.
- `scripts/validate-skill.py`, `scripts/package_skill.py`, and
  `scripts/install.sh`.
- Initial README and skill authoring references.

### Quality

- 7/7 registered skills passed the format validator.
- Full five-stage pipeline smoke test passed.
- Cross-model verification found and helped fix real skill-quality issues before
  the first baseline.
