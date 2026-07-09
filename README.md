# AI Agent Skills — 14-Skill Registry

AI agent skill 套件。`skills.json` 是唯一 registry，当前登记 14 个 skill，覆盖 skill 工程自身，也覆盖 code review、debugging、testing、requirements、planning、observability 和 incident retro 等通用 agent 工作流。

## Open Source Upload

This repository is ready to publish as an open-source GitHub project.

- Upload or push the repository root: `C:\Users\86178\Desktop\github\our-skills`.
- Do not upload the parent folder `C:\Users\86178\Desktop\github`; it only contains this repository.
- The project uses the MIT license in `LICENSE`.
- Before publishing, run `python scripts/verify_release.py` from the repository root.
- For a lighter public-upload check, run `python scripts/check_publication_ready.py`.
- If you use GitHub web upload, upload the tracked project files and omit `.git/`, local caches, and temporary build directories.

## Skill 概览

```
                ┌──────────────────────┐
                │  skill-authoring      │
                │  -workflow            │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  skill-review         │
                │  -workflow  ◄──  agent│
                │              +    -security-guard
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  cross-model          │
                │  -verification        │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  skill-pipeline       │
                │  -orchestrator        │
                └──────────┬───────────┘
                           │
                           ▼
            ┌──────────────┴──────────────┐
            │  deploy to cloud / platform │
            └─────────────────────────────┘
```

| # | Skill | Type | 功能 |
|---|-------|------|------|
| 1 | **skill-authoring-workflow** | meta | 从需求到 SKILL.md 的完整创作流程（快速通道+完整 6 阶段） |
| 2 | **skill-review-workflow** | quality | 23 项审查（格式/内容/安全），三段严重级别 |
| 3 | **agent-security-guard** | security | API key 扫描、注入检测、shell 转义铁律 |
| 4 | **cross-model-verification** | testing | 跨模型对抗验证，含外发前敏感信息门禁 |
| 5 | **skill-pipeline-orchestrator** | workflow | 5 阶段管线一键编排（Author → Review+Sec → Verify → Package → Deploy） |
| 6 | **git-workflow-for-agents** | git | 6 步 git 操作流程（含 Expected Output 和失败修复） |
| 7 | **agent-config-reference** | reference | 多平台配置速查 + 排错决策树 |
| 8 | **code-review-workflow** | code-review | 普通代码、diff、PR 的 bug/risk/test-gap 审查 |
| 9 | **systematic-debugging** | debugging | 复现、隔离、修复、验证的系统化调试循环 |
| 10 | **test-design-workflow** | testing | 风险驱动的成功、失败、边界、回归测试设计 |
| 11 | **requirements-clarifier** | requirements | 把模糊需求转成可验收的实现契约 |
| 12 | **planning-workflow** | planning | 多步骤项目、迁移、发布和高风险改动规划 |
| 13 | **observability-workflow** | observability | logs、metrics、traces、alerts、dashboards 设计 |
| 14 | **incident-retro-workflow** | incident-retro | 事件复盘、时间线、根因和行动项闭环 |

## Registry

`skills.json` 是项目的唯一清单。新增、删除、重命名 skill 时，先更新 registry，再同步 README/CHANGELOG 并运行：

```bash
python scripts/check_registry.py
python scripts/validate-skill.py */SKILL.md
python scripts/run_fixture_checks.py
python scripts/security_scan.py
python scripts/run_rigorbench.py
python scripts/check_skill_graph.py
python scripts/generate_platform_reports.py --check
python scripts/generate_example_dataset.py --check
python scripts/run_model_eval.py --check
python scripts/check_ecosystem.py
python scripts/check_release_archive.py
python scripts/check_publication_ready.py
python scripts/review_bot.py --all --check
python scripts/create_release.py --dry-run
python scripts/marketplace.py list
python scripts/marketplace.py doctor --platform codex --target-root ~
python scripts/verify_release.py
```

## 安装

### 自动安装到已检测平台

```bash
# Preview detected platforms and target paths without writing.
bash scripts/install.sh --dry-run

# Write non-interactively; existing targets are backed up first.
bash scripts/install.sh --yes

# Or write with explicit apply mode.
bash scripts/install.sh --apply
```

## 验证

所有 registered skill 应通过 registry、格式、fixture、平台矩阵、安全、打包、release、marketplace 和安装 dry-run 检查。新机器 clone 后优先跑一条命令：

```bash
python scripts/verify_release.py
```

展开后的验证链路：

```bash
python scripts/check_registry.py
python scripts/validate-skill.py */SKILL.md
python scripts/run_fixture_checks.py
python scripts/security_scan.py
python scripts/run_rigorbench.py
python scripts/check_skill_graph.py
python scripts/generate_platform_reports.py --check
python scripts/generate_example_dataset.py --check
python scripts/run_model_eval.py --check
python scripts/check_ecosystem.py
python scripts/check_release_archive.py
python scripts/check_publication_ready.py
python scripts/review_bot.py --all --check
python scripts/package_skill.py --all ./dist
python scripts/create_release.py --output ./dist-release
python scripts/marketplace.py list
python scripts/marketplace.py doctor --platform codex --target-root ~
bash scripts/install.sh --dry-run
```

## RigorBench E2E Harness

v1.3 introduced replayable traces in `eval-runs/rigorbench-v1.3/traces.json`; v1.4 expands that corpus to cover all 14 registered skills instead of scoring only static fixture contracts.

Each registered skill must have at least 3 traces covering `success`, `failure`, and `boundary`. Every trace records:

- input prompt
- triggered skill and trigger evidence
- resources read
- execution steps
- final output decision
- five-point score

`skill_sha256` binds each trace to the current `SKILL.md`; when a skill changes, stale traces fail until the run evidence is refreshed. Pass rates now come from replayed execution results, and `benchmarks/regression-history.json` stores the baseline used to detect degradation.

v1.4 requires each newly promoted general-agent skill to have success, failure, and boundary traces without reducing trigger precision for the original registry.

## Security & Supply Chain

v1.5 hardens distribution evidence and install safety:

- `scripts/create_release.py` now writes `zip`, `manifest`, `.sha256`, `.sbom.json`, `.provenance.json`, and `.sig` sidecars.
- `scripts/verify_release.py` verifies artifact hashes, SBOM contents, provenance subjects, and the canonical provenance signature.
- `scripts/check_release_archive.py` verifies retained release archives against `releases/archive-policy.json`, including historical skill counts and forbidden legacy paths.
- `scripts/marketplace.py` defaults to dry-run; writes require `--apply`, show a file diff first, and append audit events to `.our-skills-audit/events.jsonl`.
- `scripts/install.sh` also defaults to dry-run; `--apply` or `--yes` is required before writing.
- `security/dangerous-command-policy.json` holds allowlist/denylist rules; regression samples explain allowed false positives and block known dangerous misses.
- `security/redaction-regression-cases.json` covers `safe-to-dispatch`, `redacted`, `local-only`, and `abort` external-model dispatch decisions.

## Skill Platform

v2.0 turns the repository into a local platform layer. v3.0 adds ecosystem entry points while keeping public tags and remote release publishing behind an explicit user request.

- `marketplace/index.json` is the local marketplace index with versions, platform paths, dependencies, quality scores, owners, and lifecycle status.
- `scripts/marketplace.py doctor` diagnoses install paths, registry/index sync, dependencies, trigger metadata, and installed skill versions.
- `reports/skill-graph-report.md` and `.json` show the dependency graph, isolated skills, hard cycles, and stage coverage.
- `reports/quality-dashboard.md` and `.json` show pass rates, regressions, owner, last update, lifecycle status, and risk per skill.
- `scripts/create_release.py` now generates marketplace index, quality dashboard, and graph report sidecars with every local release artifact.
- `skills.json` records `owner`, `status`, `deprecated`, `replaced_by`, and `migration_path` for lifecycle and deprecation policy.

## Ecosystem Entry

v3.0 prepares the project for outside contributors and industrial adopters:

- `docs/index.html` is the public documentation site entry.
- `examples/task-library.json` and `examples/replay-dataset.json` expose success, failure, and boundary tasks for every skill.
- `docs/third-party-skill-spec.md` and `schemas/third-party-skill.schema.json` define third-party skill intake.
- `scripts/review_bot.py` runs registry, format, fixture, security, replay, graph, platform report, dataset, model eval, ecosystem, release archive, and publication-ready checks.
- `evals/model_matrix.json` and `reports/model-eval-report.json` cover Codex, Claude, Gemini, and local-model replay evaluation.
- `CONTRIBUTING.md`, `CLA.md`, `SECURITY.md`, PR template, issue templates, CODEOWNERS, and `docs/review-checklist.md` define community contribution gates.

## Release & Marketplace

### Release Policy

当前发布版本由 `skills.json` 的 `version` 和 `release_policy.current_release` 定义。项目使用 semver：

- **Patch**：文档、fixture、测试或兼容性修复，不改变 skill 行为。
- **Minor**：新增 skill、平台支持、installer 能力或验证门禁，向后兼容。
- **Major**：重命名 skill、删除 skill、改变触发语义或破坏 installer/registry 兼容性。

发布冻结必须满足：

1. `skills.json` 与每个 `SKILL.md` frontmatter `version` 完全同步。
2. `python scripts/verify_release.py` 通过。
3. `scripts/create_release.py` 生成 artifact、manifest、`.sha256`、SBOM、provenance 和 signature。
4. `marketplace.py` 能从 release artifact 安装、更新、回滚，并写入可审计日志。
5. 正式 skill 数量仍与 registry 一致，当前为 14 个。

发布资料在 `releases/v3.0.0/`，发布 artifact 由脚本生成：

```bash
python scripts/create_release.py --output ./releases/v3.0.0
```

该命令生成 `our-skills-v3.0.0.zip`、`our-skills-v3.0.0.manifest.json`、`our-skills-v3.0.0.sha256`、`our-skills-v3.0.0.sbom.json`、`our-skills-v3.0.0.provenance.json`、`our-skills-v3.0.0.sig`、`our-skills-v3.0.0.marketplace-index.json`、`our-skills-v3.0.0.quality-dashboard.json`、`our-skills-v3.0.0.skill-graph-report.json` 和 `our-skills-v3.0.0.model-eval-report.json`。

Marketplace 风格安装器支持列出、安装、更新、回滚：

```bash
python scripts/marketplace.py list
python scripts/marketplace.py install --platform codex --target-root ~
python scripts/marketplace.py install --platform codex --target-root ~ --apply
python scripts/marketplace.py update --platform codex --target-root ~ --skill skill-review-workflow --apply
python scripts/marketplace.py rollback --platform codex --target-root ~ --skill skill-review-workflow --apply
python scripts/marketplace.py doctor --platform codex --target-root ~
python scripts/review_bot.py --all --check
python scripts/run_model_eval.py --check
```

## Industrial Roadmap

当前基线是生产级早期。工业级路线按证据链推进：

| Milestone | 目标 | 验收信号 |
|---|---|---|
| v1.2 | 冻结可信发布基线 | tag `v1.1.0`、artifact/checksum、one-command verification |
| v1.3 | 真实 E2E Harness | 每个 skill 至少 3 条真实 agent 运行轨迹 |
| v1.4 | 补齐通用 agent 空白域 | code-review/debugging/testing/requirements/planning/observability/incident-retro 变正式 skill |
| v1.5 | 安全与供应链硬化 | 签名 artifact、SBOM、策略化安全扫描、dry-run 安装与可审计 rollback |
| v2.0 | Skill Platform | marketplace index、doctor、质量 dashboard、graph report、弃用策略 |
| v3.0 | Ecosystem Entry | docs site、third-party spec、review bot、multi-model eval、community gates |

## 目录结构

```
our-skills/
├── skills.json                                # 唯一 skill registry
├── benchmarks/                                # RigorBench replay config 与回归记录
├── eval-runs/rigorbench-v1.3/traces.json      # v1.3/v1.4 每个 skill 的真实执行轨迹
├── fixtures/skill_e2e_cases.json              # 每个 skill 的静态端到端任务合约
├── graphs/skill_graph.json                    # skill 硬依赖/软协作图谱
├── marketplace/manifest.json                  # marketplace/installer 元数据
├── platforms/platform_test_matrix.json        # Hermes/Claude/Codex/Cursor 测试矩阵
├── reports/                                   # quality dashboard and skill graph report
├── docs/                                      # public docs site and third-party spec
├── examples/                                  # task library and replay dataset
├── evals/                                     # multi-model evaluation matrix
├── releases/v3.0.0/                           # artifact、manifest、SBOM、provenance、signature、ecosystem reports
├── security/                                  # allowlist/denylist 和 redaction 回归样本
├── roadmap/agent_skill_domains.json           # 通用 agent skill domain 状态路线图
├── agent-security-guard/SKILL.md              # Discipline-enforcing
├── cross-model-verification/SKILL.md          # Technique (Addyosmani)
├── skill-pipeline-orchestrator/SKILL.md       # Technique
├── skill-authoring-workflow/
│   ├── SKILL.md                               # meta-skill
│   └── references/
│       ├── full-workflow.md                   # 完整 6 阶段流程
│       ├── body-templates.md                  # 4 类型模板
│       ├── addyosmani-minimalist-style.md     # 极简风格指南
│       └── platform-adapters.md              # 多平台映射
├── skill-review-workflow/SKILL.md             # Discipline-enforcing
├── git-workflow-for-agents/SKILL.md           # Technique
├── agent-config-reference/SKILL.md            # Reference
├── code-review-workflow/SKILL.md              # General agent workflow
├── systematic-debugging/SKILL.md              # General agent workflow
├── test-design-workflow/SKILL.md              # General agent workflow
├── requirements-clarifier/SKILL.md            # General agent workflow
├── planning-workflow/SKILL.md                 # General agent workflow
├── observability-workflow/SKILL.md            # General agent workflow
├── incident-retro-workflow/SKILL.md           # General agent workflow
└── scripts/
    ├── check_registry.py                      # registry 与目录一致性检查
    ├── check_skill_graph.py                   # 死链/孤岛/硬循环/阶段覆盖检查
    ├── create_release.py                      # 版本化 release artifact + SBOM/provenance/signature
    ├── marketplace.py                         # dry-run/apply/install/update/rollback/doctor 审计安装器
    ├── generate_platform_reports.py           # marketplace index、quality dashboard、graph report
    ├── platform_reports.py                    # shared platform report builder
    ├── generate_example_dataset.py            # public task library and replay dataset
    ├── run_model_eval.py                      # Codex/Claude/Gemini/local replay evaluation
    ├── review_bot.py                          # automatic contribution review gate
    ├── check_ecosystem.py                     # docs/spec/examples/eval/community asset check
    ├── run_rigorbench.py                      # 可重放 E2E RigorBench 与回归检查
    ├── run_fixture_checks.py                  # fixture/矩阵/空白域检查
    ├── security_scan.py                       # secret/shell/redaction 策略化扫描
    ├── verify_release.py                      # 一条命令发布验证入口
    ├── validate-skill.py                      # 8 项格式验证
    ├── package_skill.py                       # 打包工具
    └── install.sh                             # 安装脚本
```

## 设计原则

- **description 铁律** — 只写触发条件，不写流程，防止 agent 跳过正文
- **Expected Output** — 每步必检，agent 有明确的"做对了"信号
- **Bad/Good 对照** — 反例+正例，不给 agent 猜的空间
- **Iron Law** — 条件→结果，无条件阻断（Discipline-enforcing 类型）
- **ASCII 决策树** — 分支可视化，路径清晰
