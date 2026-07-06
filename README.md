# AI Agent Skills — 7-Skill Pipeline

超越 Addyosmani 的生产级 AI agent skill 套件。7 个 skill 覆盖从创建、审查、安全、验证、编排到部署的完整生命周期。

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
| 4 | **cross-model-verification** | testing | 跨模型对抗验证，Adversarial Prompt 模板 |
| 5 | **skill-pipeline-orchestrator** | workflow | 5 阶段管线一键编排（Author → Review+Sec → Verify → Package → Deploy） |
| 6 | **git-workflow-for-agents** | git | 6 步 git 操作流程（含 Expected Output 和失败修复） |
| 7 | **agent-config-reference** | reference | 多平台配置速查 + 排错决策树 |

## 安装

### Hermes Agent

```bash
for skill in agent-security-guard cross-model-verification skill-pipeline-orchestrator \
             skill-authoring-workflow skill-review-workflow git-workflow-for-agents \
             agent-config-reference; do
  mkdir -p ~/.hermes/skills/meta/$skill
  cp our-skills/$skill/SKILL.md ~/.hermes/skills/meta/$skill/
done
```

### Claude Code

```bash
for skill in agent-security-guard cross-model-verification skill-pipeline-orchestrator \
             skill-authoring-workflow skill-review-workflow git-workflow-for-agents \
             agent-config-reference; do
  mkdir -p ~/.claude/skills/$skill
  cp our-skills/$skill/SKILL.md ~/.claude/skills/$skill/
done
```

### Codex CLI

```bash
for skill in agent-security-guard cross-model-verification skill-pipeline-orchestrator \
             skill-authoring-workflow skill-review-workflow git-workflow-for-agents \
             agent-config-reference; do
  mkdir -p ~/.codex/skills/$skill
  cp our-skills/$skill/SKILL.md ~/.codex/skills/$skill/
done
```

### Cursor

Skills（>5k chars 用 Skills，<3k chars 用 Rules）：

```bash
for skill in agent-security-guard cross-model-verification skill-pipeline-orchestrator \
             skill-authoring-workflow skill-review-workflow git-workflow-for-agents \
             agent-config-reference; do
  mkdir -p ~/.cursor/skills/$skill
  cp our-skills/$skill/SKILL.md ~/.cursor/skills/$skill/
done
```

## 验证

所有 skill 已通过 `validate-skill.py` 8 项检查：

```bash
cd our-skills && python3 scripts/validate-skill.py */SKILL.md
```

## 目录结构

```
our-skills/
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
└── scripts/
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
