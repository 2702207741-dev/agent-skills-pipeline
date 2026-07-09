---
name: full-workflow
description: 内部参考文档——完整 6 阶段 skill 创作流程（Phase 0-5）+ Iterative Refinement + 8 反模式 + Quality Scorecard。skill-authoring-workflow 的延伸阅读附件，不单独加载。
---

# Full Workflow — Skill 创作完整 6 阶段

> 本文档是 `skill-authoring-workflow` 的内部参考，涵盖完整 6 阶段的每一步细节。
> 简单 skill 走快速通道（分类 → 草稿 → 验证），复杂 skill 走本文件。

---

## Phase 0: 分类与决策

### 目标

通过两个问题决定：①skill 类型是什么？②走快速通道还是完整流程？

### 类型决策树

```
用户的 skill 是用来______？
  │
  ├─ 强制执行规则/纪律 → Discipline-enforcing
  │     │
  │     ├── 特征词：必须、禁止、不能、不X就不Y
  │     ├── 正面例子：agent-security-guard
  │     │   "危险操作前没通过安全扫描 → 不执行"
  │     ├── 正面例子：skill-review-workflow
  │     │   "不通过全部 23 项检查 → 不批准交付"
  │     └── 反面例子：错误归为 Technique
  │         "介绍一下安全的写法"→ 没有铁律和强制执行机制，不应是 Discipline
  │
  ├─ 教怎么做一件事 → Technique
  │     │
  │     ├── 特征词：怎么做、步骤、流程、命令
  │     ├── 正面例子：git-workflow-for-agents
  │     │   6 步流程（确认状态 → 分支管理 → 精确提交 → 保持同步 → PR 自检 → 推送）
  │     ├── 正面例子：cross-model-verification
  │     │   5 步流程（Collect → Prompt → Dispatch → Diff → Report）
  │     └── 反面例子：错误归为 Reference
  │         "这是一套 git 操作流程"→ 有具体步骤和 Expected Output，不是单纯参考
  │
  ├─ 提供思维框架 → Pattern
  │     │
  │     ├── 特征词：思路、框架、模型、判断
  │     ├── 正面例子：（待实际实现后补充）
  │     └── 反面例子：错误归为 Reference
  │         "这是一个四象限分析框架"→ 有判断逻辑和边界条件，不是单纯查阅
  │
  └─ 查阅信息/规范 → Reference
        │
        ├── 特征词：参考、速查、字段、参数
        ├── 正面例子：agent-config-reference
        │   速查表在前，详细说明在后，排错在最后
        ├── 反面例子：错误归为 Technique
            "查各平台的 skill 目录"→ 没有步骤流程，不是 Technique
```

### 快速通道 vs 完整流程判断标准

```
判断当前 skill 是简单还是复杂？
  │
  ├── 简单 skill（满足 ≥3 项）
  │     ├── 单引擎/单领域
  │     ├── 边界清晰（≤5 步或≤5 条规则）
  │     ├── 无多分支决策树
  │     └── 无多平台差异
  │     └── → 快速通道：分类 → 草稿 → 一键验证（~500 token）
  │
  └── 复杂 skill（满足 ≥2 项）
        ├── 多引擎/跨领域
        ├── 含铁律/禁入条件
        ├── 步骤 > 5 或规则 > 5 条
        ├── 需查重（担心与现有 skill 重复）
        └── 涉及多平台差异
        └── → 完整流程（6 阶段，~3k token）
```

---

## Phase 1: 研究与对标

### 目标

避免闭门造车。用 GitHub 上已验证的高质量 skill 作为结构参照。

### 步骤

```bash
# 1. 选 1-2 个标杆仓库
git clone --depth 1 https://github.com/addyosmani/agent-skills.git   ~/temp/agent-skills
git clone --depth 1 https://github.com/ComposioHQ/awesome-claude-skills.git ~/temp/awesome-claude

# 2. 在标杆仓库里找同类型 skill（按你 Phase 0 判定的类型）
#    Discipline-enforcing  → 找 review / validation / security 相关的
#    Technique            → 找 workflow / pipeline / process 相关的
#    Pattern              → 找 thinking / framework / strategy 相关的
#    Reference            → 找 config / reference / cheat-sheet 相关的

# 3. 读 2-3 个 SKILL.md，分析以下维度
#    ③ description 写法（触发词 vs 流程词）
#    ③ 章节顺序（ Overview / When to Use / 正文 / Checklist 的顺序）
#    ③ 代码块风格（Bad/Good 对照、ASCII 决策树、表格）
#    ③ 验证方式（Expected Output、Verification Checklist）
```

### 对标分析表

| 维度 | 标杆做法 | 我们的选择 |
|------|---------|-----------|
| description | addyosmani 通常用 "Use when X" 开头 | 我们也用 "Use when" 开头 |
| 章节顺序 | Hermes 类型：When to Use → Core Workflow → Common Pitfalls → Verification Checklist | 同上 |
| 代码块风格 | Addyosmani 极简：ASCII 决策树，无 Bad/Good | Hermes 风格：Bad/Good 对照 |
| 验证方式 | 各 skill 自设 Verification Checklist | 统一格式：分维度分场景的 Checklist |

---

## Phase 2: 结构与命名

### 命名规则

```
格式: <动词-名词> 或 <名词-名词>
例子: git-workflow-for-agents / agent-security-guard / skill-authoring-workflow
```

**为什么禁止这些词：**

| 禁止词 | 原因 |
|--------|------|
| `how-to-` | 多余前缀，skill 名本身已表意 |
| `skill-` | "这是 skill 怎么用 xxx skill" → 冗余 |
| `-helper` / `-tool` | 暗示工具函数而非知识传递，混淆类型定位 |

**反例表：**

| 错误名称 | 问题 | 正确替代 |
|---------|------|---------|
| `how-to-deploy` | 有 how-to- | `deploy-workflow` |
| `skill-review` | 有 skill- | `review-workflow` |
| `config-helper` | 有 -helper | `config-reference` |
| `git-tool` | 有 -tool | `git-workflow` |

### Category 16 个枚举值

（Hermes Agent 专用，Claude / Codex / Cursor 无需 category）

| Category | 适用 skill 类型 |
|----------|---------------|
| `workflow` | 流程类（git-workflow、deploy-workflow） |
| `quality` | 质量类（code-review、tdd-workflow） |
| `security` | 安全类（agent-security-guard） |
| `testing` | 测试类（testing-anti-patterns） |
| `debugging` | 调试类（systematic-debugging） |
| `planning` | 规划类（autoplan-pipeline） |
| `brainstorming` | 头脑风暴类（brainstorm-and-plan） |
| `context` | 上下文管理类（context-management） |
| `subagent` | Sub-agent 管理类 |
| `documentation` | 文档类 |
| `deployment` | 部署类 |
| `git` | Git 操作类 |
| `meta` | 元 skill（skill-authoring-workflow、writing-skills） |
| `review` | 审查类（skill-review-workflow） |
| `reference` | 参考类（agent-config-reference） |
| `tools` | 工具集成类 |

### 模板选择逻辑

```
你的 skill 类型是？
  │
  ├── Discipline-enforcing → references/body-templates.md § Discipline
  │
  ├── Technique            → references/body-templates.md § Technique
  │         └── 如果 > 8k chars 或有分支决策树
  │               → references/addyosmani-minimalist-style.md
  │
  ├── Pattern              → references/body-templates.md § Pattern
  │
  └── Reference            → references/body-templates.md § Reference
```

### 分支决策：拆分子 skill 还是合在一个文件？

≥3 条互斥分支，每条正文 >500 字 → 考虑拆分子 skill，而不是全塞一个文件。

```
你的 skill 有 ≥3 条互斥分支，每条 >500 字？
  │
  ├── 是 → 拆分子 skill
  │        ├── 主 skill: 路由逻辑（决策树 + 跳转指令，~500 字）
  │        ├── 子 skill A: 分支 A 的详细操作
  │        ├── 子 skill B: 分支 B 的详细操作
  │        └── 子 skill C: 分支 C 的详细操作
  │
  │        Agent 读主 skill 决策树，只加载被路由到的子 skill。
  │        不走的分支不占 token。浪费从 ~60% 降到 0%。
  │
  └── 否 → 合在一个文件（≤3 分支，或每条 ≤500 字）
```

注意：子 skill 的 `description` 要能被主 skill 的跳转指令触发。主 skill 描述中不要"锁死"子 skill 名称——用事件场景而非 skill 名做跳转条件。

---

## Phase 3: 内容写作

### 3.1 Discipline-enforcing

Discipline-enforcing 有两种已验证的子模式：

| 子模式 | 核心逻辑 | Iron Law 句式 | 典型示例 |
|--------|---------|---------------|---------|
| **操作阻断型** | 在执行危险操作前拦截 | `"操作前没通过X → 不执行Y"` | agent-security-guard |
| **检测阻断型** | 检测到 X 条件出现就阻断 Y 流程 | `"X 出现在暂存区 → 阻断 commit"` | env-file-security, context-read-first |

两种子模式都使用 Iron Law 的"条件 → 结果"句式，只是条件的来源不同（"即将做某事" vs "检测到某状态"）。

**Iron Law 写法（必须用 "不X就不Y" 句式）：**

```
❌ BAD: "安全扫描很重要，建议每次 commit 前都执行"
   → 建议语气，不具强制力

❌ BAD: ".env 文件不应该被提交到 git"
   → 陈述事实，不是阻断规则

✅ GOOD: "commit 前没通过安全扫描 → 不执行"
   → 操作阻断型：不X就不Y 句式，无条件阻断

✅ GOOD: ".env 文件在 git diff 中 → 阻断 commit"
   → 检测阻断型：X 条件出现 → 阻断 Y 操作
```

**Iron Law 结构：**

```
## The Iron Law

条件A → 结果A
条件B → 结果B
（每行一个条件-结果对）
```

**Rules 必须含 Bad/Good 对照：**

```
### Rule N: 规则名称

**What:** 一句话说明规则适用场景。

**Bad:**
```
反模式示例（直接展示错误行为）
→ 展示错误的后果
```

**Good:**
```
正确做法
→ 展示正确执行的结果
```
```

**Rationalization Table 至少 4 条：**

| 借口 | 为什么不成立 |
|------|-------------|
| "这个 key 是测试环境的，没关系" | 测试 key 可能和生产共用基础设施 |
| "我检查过了，没问题" | 人眼容易遗漏正则匹配的内容 |
| ...（至少 4 条） | ... |

### 3.2 Technique

**Expected Output 格式：**

```
**Expected Output:** `<具体输出>`
```

- 不是 "应该成功" 或 "显示正确"
- 是 `"Build ID: abc123"` 或 `3 files added, 1 deleted`
- 每步都必须有（不允许跳过）

**If fails 分支（至少 2 条）：**

```
执行命令
  │
  ├── 成功 → 继续下一步
  │
  ├── 失败 A → <根因> → <修复命令>
  │
  └── 失败 B → <根因> → <修复命令>
```

**命令必须完整路径：**

```bash
# ❌ BAD
./deploy.sh

# ✅ GOOD
./scripts/deploy.sh --check --env staging
```

### 3.3 Pattern

**Recognition Guide（何时用此模式）：**

```
什么情况应该用这个模式？
  │
  ├── 条件 1（具体场景描述）
  ├── 条件 2
  └── 什么情况不应该用
```

**至少 2 个 Worked Example：**

每个 Example 包含：
- 场景描述（输入）
- 应用步骤
- 最终结果（输出）

**边界条件表：**

| 边界条件 | 此模式是否适用 | 说明 |
|---------|-------------|------|
| 超大规模 | ✅/❌ | 为什么 |
| 强依赖外部服务 | ✅/❌ | 为什么 |
| 实时性要求高 | ✅/❌ | 为什么 |

### 3.4 Reference

**Quick Reference 表格必须放最前面：**

```markdown
### 路径速查 / 字段兼容 / 配置表

| 维度 A | 维度 B | ... |
|--------|--------|-----|
| ...     | ...     | ... |
```

**Constraints & Limits 表：**

```markdown
| 限制项 | 值 | 超出后果 |
|--------|-----|---------|
| 名称最大长度 | 64 chars | 截断后不匹配 |
| ... | ... | ... |
```

**Troubleshooting 决策树：**

```
问题类型？
  │
  ├── 类型 A → 诊断路径 1
  │
  ├── 类型 B → 诊断路径 2
  │
  └── 类型 C → 诊断路径 3
```

每步含 Expected Output，不允许只有 "应该正常"。

---

## Phase 4: 验证

### validate-skill.py 8 项检查说明

| # | 检查项 | 检查什么 | 失败时修复命令 |
|---|--------|---------|---------------|
| 1 | 文件以 `---` 开头 | 确认无 BOM、无乱码 | 用 UTF-8 保存 |
| 2 | Frontmatter 闭合 | `---` 配对 + 后跟空行 | 补空行或补闭合 `---` |
| 3 | `name` 格式 | ≤64 chars, a-z0-9- | 修改 name 字段 |
| 4 | `description` 格式 | ≤1024 chars, 以 "Use when" 开头 | 重写 description |
| 5 | description 无流程泄露 | "—" 后无操作动词 | 删掉破折号后的步骤描述 |
| 6 | When to Use 节 | `| Use When \| Don't Use When \|` 表格存在 | 添加表格 |
| 7 | Verification Checklist 节 | "Verification Checklist" 文字存在 | 添加 Checklist 节 |
| 8 | 文件长度 | ≤15000 chars | 精简正文，大段参考移入 `references/` |

### 人工自检清单

#### Trigger（触发）
- [ ] 5 个该触发场景全部覆盖
- [ ] 3 个不该触发场景全部拦截（Don't Use When ≥3 条）
- [ ] description 含用户实际会说的关键词
- [ ] Don't Use When 中的关键词与 Use When 互斥

#### Content（内容）
- [ ] Overview ≤ 3 句
- [ ] 所有命令精确可执行（含完整路径）
- [ ] 关键步骤有 Expected Output
- [ ] 无模糊词：应该、可能、通常、一般、大概
- [ ] Common Pitfalls ≥ 3 条，每条含事件→原因→修复
- [ ] Red Flags 对应每个自我欺骗借口

#### Format（格式）
- [ ] 文件以 `---` 开头（无 BOM）
- [ ] Frontmatter 闭合，YAML 有效
- [ ] `name` ≤ 64 chars，全小写+连字符
- [ ] `description` ≤ 1024 chars，"Use when" 开头
- [ ] 文件长度在类型上限以内

---

## Phase 5: 交付

### 4 平台写入路径

| 平台 | 路径 | 要求 |
|------|------|------|
| Hermes Agent | `~/.hermes/skills/<category>/<name>/SKILL.md` | 需要 category，目录名 = name |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | 无需 category |
| Codex CLI | `~/.codex/skills/<name>/SKILL.md` | 无需 category |
| Cursor | `~/.cursor/skills/<name>/SKILL.md` 或 `~/.cursor/rules/<name>.md` | >5k chars → Skills；<3k chars → Rules |

### 覆盖确认流程

```bash
# 1. 检查目标已存在？
ls ~/.hermes/skills/<category>/<name>/SKILL.md 2>/dev/null && echo "EXISTS" || echo "NEW"

# EXISTS → 先问用户：覆盖 / 备份 / 跳过
# NEW → 直接写入

# 2. 写入后验证
python3 scripts/validate-skill.py <path>  # 必须 8/8

# 3. 报告 Quality Scorecard
```

### Quality Scorecard 打分细则

| 维度 | 1 分 | 2 分 | 3 分 | 4 分 | 5 分 |
|------|------|------|------|------|------|
| **Trigger Precision** (×2) | 触发词缺失或错误 | 只覆盖 2-3 个场景 | 覆盖主要场景但有遗漏 | 覆盖所有预期场景 | 覆盖所有预期 + 反场景全覆盖 |
| **Actionability** (×3) | 步骤模糊，无法执行 | 部分命令可执行 | 大部分命令可执行 | 所有命令可执行，缺 Expected | 所有命令精确 + 每步有 Expected |
| **Completeness** (×2) | 缺核心章节 | 缺 1-2 个关键 section | 结构完整但内容有缺 | 内容完整，少量细项缺 | 内容完整，无遗漏 |
| **Conciseness** (×1) | 类型相关：超过上限且冗余严重 | 超过上限+多处重复 | 类型相关：超过目标但在上限内 | 类型相关：在目标范围内 | 类型相关：接近下限且无冗余 |
| **Verifiability** (×2) | 无验证方式 | 只有模糊的"应该" | 有 Checklist 但缺 Expected | Checklist 完整，Expected 清晰 | 每步 Expected 精确 + Checklist 可操作 |

**总分 = (Trigger ×2) + (Actionability ×3) + (Completeness ×2) + (Conciseness ×1) + (Verifiability ×2)**

| 总分 | 结论 |
|------|------|
| < 20 | ❌ 拒绝交付 |
| 20-39 | ⚠️ 有条件通过，需修复 |
| 40-49 | ✅ 通过，优秀 |
| 50 | 🌟 满分 |

---

## 8 个反模式

| # | 反模式名称 | 为什么危险 | 如何避免 | 对应 Red Flag |
|---|-----------|-----------|---------|---------------|
| 1 | 跳过分类直接写 | 类型决定结构，写错结构后全盘推倒 | 先走 Phase 0 类型决策树 | #2 |
| 2 | 先写后分类 | 先盖房再画图 | Phase 0 在动笔前完成 | #2 |
| 3 | 跳过验证 | Skill 的 bug 是静默的错误指导 | 必跑 `validate-skill.py` | #3 |
| 4 | description 含流程 | Agent 用 description 信息执行，跳过正文 | Description 铁律自查 | #4 |
| 5 | 写多了再删 | 第 3 个 example 边际价值趋近零 | 写前设定内容上限 | #5 |
| 6 | 不写边界条件 | Agent 会遇异常——你得替它想 | 每个步骤都写 If fails 分支 | #6 |
| 7 | 引用不存在的 skill | Agent 尝试加载时困惑或报错 | Phase 2 验证所有 related_skills | #7 |
| 8 | 追求优雅而非正确 | 优雅 = 模糊。正确性 > 优雅性 | 宁可啰嗦也要精确 | #8 |

---

## Iterative Refinement

### 迭代触发条件

| 触发信号 | 含义 | 行动 |
|---------|------|------|
| 同一问题被问 3 次以上 | description 漏了触发词 | 补触发词，更新 description |
| 用户说"这不是我想要的" | Overview 或 When to Use 不准确 | 重写相关章节 |
| `validate-skill.py` 发现新失败项 | 格式要求更新 | 修复格式 + 更新验证清单 |
| 用户明确说"帮我把这个 skill 改一下" | 大改 | 走 skill-authoring-workflow 全流程 |

### 迭代原则

- 小改（补触发词、修 Typo）→ 直接编辑，不用走完整 6 阶段
- 大改（新增章节、改类型、加 Iron Law）→ 走完整流程
- 每次迭代后重新跑 `validate-skill.py`

---

*本文档是 skill-authoring-workflow 的延伸阅读附件，不单独加载。*
