# Changelog

## Unreleased

### Fixed

- Restored the retained `v1.1.0` release archive to the original 7-skill production baseline and regenerated matching SBOM, provenance, and signature sidecars.
- Added `releases/archive-policy.json` and `scripts/check_release_archive.py` so historical release artifacts cannot silently drift to newer registry contents.

### Added

- Added MIT licensing, a code of conduct, `.gitattributes`, and GitHub upload guidance for public open-source release readiness.
- Added `scripts/check_publication_ready.py` and wired it into CI, `verify_release.py`, `test_all.sh`, and the review bot.

## 3.0.0 (2026-07-08)

### Added

- **docs/index.html** - public documentation site for marketplace, doctor, quality, replay, and contribution entry points.
- **examples/task-library.json** and **examples/replay-dataset.json** - public task library and replay dataset generated from saved agent traces.
- **docs/third-party-skill-spec.md** and **schemas/third-party-skill.schema.json** - third-party skill intake and compatibility specification.
- **templates/third-party-skill/** - starter `SKILL.md` and intake metadata for outside contributors.
- **scripts/review_bot.py** and **.github/workflows/skill-review-bot.yml** - automatic review gate for registry, format, fixtures, security, replay, graph, platform, dataset, model eval, and ecosystem checks.
- **evals/model_matrix.json**, **scripts/run_model_eval.py**, and **reports/model-eval-report.json/md** - deterministic multi-model replay evaluation for Codex, Claude, Gemini, and a local model row.
- **CONTRIBUTING.md**, **CLA.md**, **SECURITY.md**, PR template, issue templates, CODEOWNERS, and **docs/review-checklist.md** - community contribution process, CLA, review checklist, and security gates.

### Changed

- `scripts/create_release.py` now emits a model evaluation sidecar in addition to v2 platform sidecars.
- `scripts/verify_release.py`, CI, and `scripts/test_all.sh` now verify ecosystem assets, example datasets, model evaluation, and review bot gates.
- `skills.json` now records v3 ecosystem policy while keeping public publishing behind an explicit user request.

## 2.0.0 (2026-07-08)

### Added

- **marketplace/index.json** - local marketplace index with skill versions, compatible platform paths, dependencies, quality scores, owners, and lifecycle status.
- **scripts/marketplace.py doctor** - diagnoses registry/index sync, source metadata, dependency coverage, platform install paths, trigger metadata, and installed skill versions.
- **reports/quality-dashboard.json** and **reports/quality-dashboard.md** - per-skill pass rates, regressions, owner, last update, lifecycle status, and risk level.
- **reports/skill-graph-report.json** and **reports/skill-graph-report.md** - visual Mermaid dependency graph plus isolated skill, hard cycle, and stage coverage summaries.
- **scripts/platform_reports.py** and **scripts/generate_platform_reports.py** - shared generation and freshness checks for platform reports.
- **skills.json deprecation policy** - `owner`, `status`, `deprecated`, `replaced_by`, and `migration_path` metadata for every registered skill.

### Changed

- `scripts/create_release.py` now generates marketplace index, quality dashboard, and graph report sidecars for every release artifact.
- `scripts/verify_release.py`, CI, and `scripts/test_all.sh` now verify platform reports and strict marketplace doctor checks.
- Public publishing remains deferred until v3.0; v2.0 is a committed local platform milestone.

## 1.5.0 (2026-07-08)

### Added

- **skills.json** — single source of truth for the 14 registered skills, including the v1.4 general-agent workflow expansion.
- **code-review-workflow**, **systematic-debugging**, **test-design-workflow**, **requirements-clarifier**, **planning-workflow**, **observability-workflow**, and **incident-retro-workflow** — promoted roadmap domains to formal skills.
- **scripts/check_registry.py** — verifies registry entries match skill directories and frontmatter names.
- **fixtures/skill_e2e_cases.json** — end-to-end task contracts for every registered skill, including 14 new v1.4 cases for the seven promoted domains.
- **roadmap/agent_skill_domains.json** — general-agent domain roadmap with v1.4 domains marked as registered.
- **platforms/platform_test_matrix.json** — install and trigger verification matrix for Hermes, Claude Code, Codex, and Cursor.
- **scripts/run_fixture_checks.py** — validates fixture coverage, blank-domain coverage, and platform matrix completeness.
- **scripts/security_scan.py** — scans for likely secrets, policy-backed dangerous shell patterns, external-model redaction drift, and security regression samples.
- **security/dangerous-command-policy.json** — allowlist/denylist policy for explainable dangerous-command scanning.
- **security/dangerous-command-regression-cases.json** and **security/redaction-regression-cases.json** — regression samples for false-positive rationale, missed dangerous commands, and external-model redaction decisions.
- **releases/v1.5.0/** — versioned release manifest, migration guide, compatibility table, artifact, checksum, SBOM, provenance, and signature.
- **scripts/create_release.py** — generates `our-skills-v<version>.zip`, checksum manifest, SBOM, provenance, and signature sidecars from semver registry metadata.
- **scripts/verify_release.py** — one-command release verification for fresh clones, signed artifact sidecars, and audited install/update/rollback checks.
- **eval-runs/rigorbench-v1.3/traces.json** — replayable E2E agent execution traces with success/failure/boundary coverage for every registered skill.
- **benchmarks/rigorbench.json** and **benchmarks/regression-history.json** — replayable RigorBench baseline with per-skill pass rates and regression records.
- **scripts/run_rigorbench.py** — replays saved execution traces, checks stale SKILL.md hashes, and fails on pass-rate regressions.
- **marketplace/manifest.json** and **scripts/marketplace.py** — dry-run-default list/install/update/rollback marketplace installer with diff preview and audit log.
- **graphs/skill_graph.json** and **scripts/check_skill_graph.py** — dependency graph with dead-link, island, hard-cycle, and stage-coverage checks for the expanded 14-skill registry.
- CI workflow for registry validation, `validate-skill.py`, `git diff --check`, package smoke test, and installer dry-run.

### Changed

- README now reflects the 14-skill registry and the v1.4 general-agent workflow coverage.
- Release metadata, compatibility docs, CI, packaging, and release verification now derive expected skill counts from `skills.json` instead of assuming 7 skills.
- README now documents release policy and the industrial-grade roadmap.
- `scripts/check_registry.py` now validates project and skill semver metadata.
- `scripts/install.sh` now reads `skills.json`, defaults to `--dry-run`, requires `--apply`/`--yes` before writing, previews diffs, writes audit events, and backs up existing targets instead of silently deleting them.
- `scripts/marketplace.py` now defaults to dry-run, requires `--apply` before writing, previews diffs, filters bytecode caches, and makes fresh install rollback auditable.
- `scripts/package_skill.py` now matches the current `validate_skill()` return shape and can package every registered skill with `--all`.
- Release verification now derives artifact names from `skills.json` instead of hardcoding `v1.1.0`.
- Removed the old non-official eighth-skill benchmark reference from authoring case studies.

## 1.0.0 (2026-07-06)

Initial release — 7-skill pipeline for AI agent workflows.

### Added

#### 新 Skill（3 个）
- **agent-security-guard** — 安全门禁（API key 扫描、注入检测、shell 转义）
- **cross-model-verification** — 跨模型对抗验证 + Adversarial Prompt 模板
- **skill-pipeline-orchestrator** — 5 阶段管线编排（Author → Review+Sec → Verify → Package → Deploy）

#### 升级 Skill（4 个）
- **skill-authoring-workflow** v1.5.0 — 新增快速通道、Iterative Refinement、Interaction 联动、4 个 reference 文件
- **skill-review-workflow** v1.1.0 — 新增 Security 严重级别、Expected Output 补全、Interaction 联动
- **git-workflow-for-agents** — 6 步全部补全 Expected Output，新增 API key 误提交检测
- **agent-config-reference** — Troubleshooting 重构为类型 A/B/C 决策树，新增 Security Configuration

#### 工具
- **scripts/validate-skill.py** — 8 项格式一键验证
- **scripts/package_skill.py** — 打包脚本
- **scripts/install.sh** — 多平台安装脚本

#### 文档
- README.md — 项目概览 + 安装指南
- skill-authoring-workflow/references/ 下 4 个参考文档

### Quality

- 7/7 registered skills 全部通过 validate-skill.py 8 项检查
- 5 阶段管线全流程测试通过
- 跨模型验证（Claude + GLM）发现并修复 5 个真实问题
- 双平台部署认证（Hermes Agent + Claude Code）
