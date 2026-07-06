---
name: skill-authoring-workflow
description: Use when the user says "写个 skill""创建 SKILL.md""这个流程变成 skill" or any new skill creation request. Use when the user provides a design document and asks to implement it as a skill. Do NOT use for small edits to existing skills or questions about skill format — answer those directly.
version: 1.5.0
metadata:
  tags: [skill-authoring, meta-skill, workflow, quality]
  related_skills: []
---

# Skill Authoring Workflow

## Overview

不规范的 skill 是静默的错误指导——agent 加载后可能漏步骤、用错工具、或跳过关键校验。这套工作流确保每个 SKILL.md 的触发条件精确、步骤可执行、检查项可验证，避免"写完但不知道怎么用"的烂尾。

两套流程写 skill。简单 skill（单领域、≤5 步、边界清晰）走快速通道（3 步，~500 token 流程开销）。复杂 skill（多分支、含铁律、跨领域）走完整 6 阶段（见 `references/full-workflow.md`）。

> **⚠️ ~500 token 指流程开销，不含正文写作。**
> 正文按下方 Token Budget 表算——Reference 最少 2K、Technique 最少 5K。
> 快速通道省的是完整 6 阶段的 3K+ token 决策流程，不是正文内容。

本 skill 支持多平台（Hermes Agent / Claude Code / Codex CLI / Cursor）。工具名和路径因平台而异——详见 `references/platform-adapters.md`。

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户说"写个 skill""帮我创建 SKILL.md""把这个流程写成 skill" | 只是修改现有 skill 的一小段（直接编辑即可） |
| 用户说"这个工作流应该变成 skill""帮我封装成 skill" | 用户只是问"skill 格式是什么""description 怎么写"（直接回答，不需要走流程） |
| 用户给了一份设计文档，要求实现为 skill | 写 skill 之外的代码（如实现功能本身） |
| 新 skill 写完准备交付，需要验证质量 | 用户说"随便写写，不用规范"（质量要求由用户取消） |
| 需要把 skill 从 Hermes 迁移到 Claude Code / Cursor | 只是查询已有的 skill 怎么用（加载解释即可） |

## 快速通道 vs 完整流程（先看这里）

```
你的 skill 特征是？
  │
  ├── 简单 skill（满足 ≥3 项）
  │     ├── 单引擎/单领域、边界清晰、步骤 ≤ 5、无多分支
  │     └── → 快速通道：分类 → 草稿 → 一键验证（~500 token 流程开销，正文另算）
  │
  └── 复杂 skill（满足 ≥2 项）
        ├── 多引擎/跨领域、含铁律、步骤 > 5、需查重
        └── → 完整流程（6 阶段，~3k token）
              详见 references/full-workflow.md
```

## 快速通道

### 快1：分类

用下方 Phase 0 类型决策树判定类型，输出 1 行结论。

```
用户的 skill 是用来______？
  ├─ 强制执行规则/纪律 → Discipline-enforcing（特征词：必须、禁止、不能）
  ├─ 教怎么做一件事 → Technique（特征词：怎么做、步骤、流程、命令）
  ├─ 提供思维框架 → Pattern（特征词：思路、框架、模型、判断）
  └─ 查阅信息/规范 → Reference（特征词：参考、速查、字段、参数）
```

**Expected Output:** `类型: <Discipline/Technique/Pattern/Reference> + 一句话理由`

### 快2：草稿

从 `references/body-templates.md` 选对应模板，直接填。保留 section：Overview / When to Use / Core Workflow / Common Pitfalls / Verification Checklist。跳过的 section：Rationalization Table / No Exceptions / 5×5 Trigger 矩阵。

命名规则（硬性）：`<动词>-<名词>` 或 `<名词>-<名词>`，全小写+连字符，≤ 64 字符。禁止 `how-to-`、`skill-`、`-helper`、`-tool` 前缀/后缀。Category 从 16 个枚举值选（见 `references/full-workflow.md` §Phase 2.3）。

**Expected Output:** `SKILL.md 草稿文件（含 frontmatter + 5 个必选 section）`

### 快3：一键验证

```bash
# 所有平台通用：终端中运行
python3 scripts/validate-skill.py <path/to/SKILL.md>
```

8 项全过 → 跳到「交付」。有失败 → 修复后重跑。

**Expected Output:** `validate-skill.py 8/8 通过，或具体失败项清单`

---

## 核心规则（快速通道和完整流程都要遵守）

### Frontmatter

```yaml
---
name: <动词-名词>                    # ≤ 64 chars, 全小写+连字符
description: Use when <触发条件>.     # ≤ 1024 chars, 只写 WHEN，不写 WHAT
version: 1.0.0
metadata:
  tags: [3-5个名词标签]
  related_skills: [真实存在的 skill 名]
---
```

### Description 铁律

**只写触发条件，不写流程。** Agent 扫描 skill 时，如果 description 已经写了怎么做（如 `"Use when X — step1: check config, step2: build"`），agent 用 description 信息执行，不再读正文——所有精心内容白费。

```
❌ BAD: "Use when debugging Python — use pdb, check logs, isolate the bug, fix it"
   → agent 看到 pdb/check/isolate/fix，以为全懂了，跳过正文

✅ GOOD: "Use when a Python process crashes with an unclear traceback or hangs indefinitely"
   → agent 只知道什么时候触发，必须读正文
```

自查：description 出现破折号+操作动词（runs/checks/builds/creates）、逗号分隔步骤、工具名（pdb/kubectl）、流程术语（pipeline/workflow）→ 重写。

### When to Use 格式

```
| Use When | Don't Use When |
|----------|----------------|
| 场景（含触发关键词） | 反场景（含排除关键词） |
```

每条 Use When 含 ≥1 个可匹配关键词。Don't Use When 列 ≥ 3 条。

### 风格选择

```
你的 skill 是什么类型？
  │
  ├── Reference / Pattern / Discipline-enforcing → Hermes 原生
  │     （5 字段 frontmatter，Markdown 表格，Bad/Good 对照）
  │
  └── Technique / 混合型，> 8k chars，有分支决策
        │
        └── → Addyosmani 极简（见 references/addyosmani-minimalist-style.md）
              （2 字段 frontmatter，ASCII 决策树，验证信号对照表）
```

**先对标再下笔。** 去 GitHub 找 1-2 个同领域爆火 skill（addyosmani/agent-skills、ComposioHQ/awesome-claude-skills），`git clone --depth 1` 拉下来读 2-3 个 SKILL.md。风格差距大 → 调整模板选择，别等写完再推倒。

### Token Budget

| 类型 | 目标 | 上限 |
|------|------|------|
| Discipline | 3-6k | 8k |
| Technique | 5-12k | 15k |
| Pattern | 3-8k | 10k |
| Reference | 2-10k | 12k |

缩短口诀：砍 Expected 输出 → 首句传核心 → 补或删无修复的 Pitfall → 合并重复信息。

---

## 参考模型速查

写新 skill 时，找 1-2 个已完成的高质量 skill 做结构参照。优先选同类型的——Technique 参照 Technique，Discipline-enforcing 参照 Discipline-enforcing。

**推荐外部参考（GitHub）：**
- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — 30+ 生产级 skill，Addyosmani 极简风格发源地
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) — 精选 skill 索引

**用你项目里已有的高质量 skill：** 用 `skill_view(name)` 加载 1-2 个同类型的查看结构，分析它们的 description 写法、章节顺序、代码块风格、验证方式，然后对标。

---

## Common Pitfalls

| # | 错误 | 修复 |
|---|------|------|
| 1 | When to Use 太泛 | 具体化：`"Use when about to run kubectl apply against production"` |
| 2 | 命令缺完整路径 | 写完整：`./scripts/deploy.sh --check` |
| 3 | Expected 模糊："应该显示成功" | 给样例：`"Build ID: abc123"` |
| 4 | 步骤间没依赖说明 | 每步加 Why（1 句） |
| 5 | Pitfall 只有"可能出错"，没收尾 | 三段式：错误现象 → 原因 → 修复命令 |
| 6 | 跳过分类直接写 | 强制先走类型决策树 |
| 7 | 只有正面指导，没 Red Flags | 针对每种自我欺骗加一条 Red Flag |
| 8 | description 抄了另一个 skill 句式 | 为每个 skill 从头设计触发条件 |
| 9 | related_skills 编造不存在的 skill 名 | Phase 2 查重时验证 |
| 10 | 交付前没跑验证，凭感觉说"没问题" | 跑 `scripts/validate-skill.py` |
| 11 | 闭门造车，不知道外面流行什么风格 | 先对标外部标杆再下笔 |
| 12 | 简单 skill 走了完整 6 阶段 | 先判断复杂度，选快速通道 |
| 13 | 以为快速通道能省正文 token | 流程开销 ≠ 正文开销。正文按类型 budget 算，不因快速通道变少 |

---

## Red Flags

脑子里出现以下想法——停下来：

| # | Red Flag | 为什么危险 |
|---|---------|-----------|
| 1 | "太简单了，不需要走完整流程" | 简单 skill 结构更需要精确 |
| 2 | "我先写了再说，写完再分类" | 先写后分类 = 先盖房再画图 |
| 3 | "验证可以跳过，反正看起来是对的" | Skill 的 bug 是静默的错误指导 |
| 4 | "description 写了流程但 agent 也会读正文的" | Agent 不会。desc 有流程 = 正文白写 |
| 5 | "再加一个 Worked Example" | 第 3 个 example 边际价值趋近零 |
| 6 | "用户没提边界条件，我就不写了" | Agent 会遇异常——你得替它想 |
| 7 | "和已有 X 有点像但我懒得引用" | Agent 不知道该用哪个，可能选错 |
| 8 | "写得优雅一点而不是那么啰嗦" | 优雅 = 模糊。正确性 > 优雅性 |
| 9 | "这步简单，不需要 Expected 输出" | 没有 Expected = agent 不知道做对了没 |

---

## Verification Checklist

交付前逐项确认：

### 格式
- [ ] 文件以 `---` 开头（无 BOM）
- [ ] Frontmatter 闭合，YAML 有效
- [ ] `name` ≤ 64 chars，全小写+连字符
- [ ] `description` ≤ 1024 chars，"Use when" 开头，无流程摘要
- [ ] 文件长度在类型上限以内

### Trigger
- [ ] 5 该触发场景全部匹配
- [ ] 5 不该触发场景全部拦截
- [ ] Don't Use When ≥ 3 条

### Content
- [ ] Overview ≤ 3 句
- [ ] 所有命令精确可执行
- [ ] 关键步骤有 Expected 输出
- [ ] 无模糊词：应该、可能、通常、一般、大概
- [ ] Common Pitfalls ≥ 3 条，每条有完整事件→原因→修复链路
- [ ] related_skills 引用真实存在
- [ ] 没落入 8 个反模式（见 `references/full-workflow.md`）

---

## Interaction with Other Skills

本 skill 是 pipeline 的起点——写完后自动进入审查和部署流程。

| 下游 Skill | 触发时机 | 加载方式 |
|------------|---------|---------|
| **skill-review-workflow** | SKILL.md 草稿完成、validate-skill.py 通过后 | 自动进入 Stage 2 |
| **agent-security-guard** | skill-review 发现安全相关问题时 | skill-review 自动触发 |
| **skill-pipeline-orchestrator** | 审查通过后，用户说"一键发布" | 用户主动触发 Stage 1-5 |

**Pipeline 入口：**
```
写 skill → skill-authoring-workflow（本 skill）
         → validate-skill.py 通过
         → skill-review-workflow（23 项审查）
         → skill-pipeline-orchestrator（一键发布）
```

---

## 交付

将 SKILL.md 写入对应平台的 skills 目录：

| 平台 | 路径 |
|------|------|
| Hermes Agent | `~/.hermes/skills/<category>/<name>/SKILL.md` |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` |
| Codex CLI | `~/.codex/skills/<name>/SKILL.md` |
| Cursor | `~/.cursor/skills/<name>/SKILL.md` |

目标已存在 → 先问用户。保存后输出 Quality Scorecard：

```
Trigger Precision:  _/5 ×2 = __
Actionability:     _/5 ×3 = __
Completeness:      _/5 ×2 = __
Conciseness:       _/5 ×1 = __
Verifiability:     _/5 ×2 = __
总分: __/50（≥20 可交付，≥40 优秀）
```

---

## Step 6: 迭代（Iterative Refinement）

Skill 交付后不是终点——实际使用中会发现遗漏和偏差。

```
交付完成 → 实际使用 → 发现问题
                          │
                          ├── 触发词漏了 → 更新 description
                          ├── 步骤有歧义 → 加 Expected Output 或示例
                          ├── 平台工具错 → 检查 references/platform-adapters.md
                          ├── 新增场景 → 补 When to Use 和 Common Pitfalls
                          └── 用户反馈"不对" → 回溯步骤，改正文或 Iron Law
```

**迭代触发条件：**
- 同一问题被问 3 次以上 → description 漏了触发词
- 用户说"这不是我想要的"→ Overview 或 When to Use 不准确
- `validate-skill.py` 发现新失败项 → 更新验证清单
- 用户明确说"帮我把这个 skill 改一下"→ 走 skill-authoring-workflow 全流程

**迭代原则：**
- 小改直接编辑，不用走完整 6 阶段
- 大改（新增章节、改类型、加 Iron Law）走完整流程
- 每次迭代后重新跑 `validate-skill.py`

---

## 延伸阅读

- `references/full-workflow.md` — 完整 6 阶段流程（Phase 0-5、Iterative Refinement、8 反模式、Quality Scorecard）
- `references/body-templates.md` — 4 种类型的写作模板
- `references/addyosmani-minimalist-style.md` — Addyosmani 极简风格指南
- `references/platform-adapters.md` — 多平台工具/路径映射（Claude Code / Codex / Cursor）
- `scripts/validate-skill.py` — 8 项格式一键检查
