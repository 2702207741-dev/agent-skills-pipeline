---
name: body-templates
description: 内部参考文档——4 种 skill 类型（Discipline-enforcing / Technique / Pattern / Reference）的写作模板。skill-authoring-workflow 的延伸阅读附件，不单独加载。
---

# Body Templates — 4 种类型写作模板

> 本文档提供 4 种 skill 类型的完整结构模板。复制对应模板，填入具体内容即可。
> 类型判定见 `full-workflow.md` § Phase 0。

---

## 模板 1: Discipline-enforcing（纪律执行型）

### 适用场景

强制执行规则、纪律、安全要求。特征词：必须、禁止、不能、不X就不Y。

### 结构模板

```markdown
---
name: <动词-名词>
description: Use when <触发条件>. Use when <第二触发条件>. Use when <第三触发条件>.
version: 1.0.0
metadata:
  tags: [tag1, tag2, tag3]
  related_skills: [skill-a, skill-b]
---

# <Skill 标题>

## Overview

<2-3 句说明这个 skill 强制执行什么规则、为什么重要、不遵守会怎样。>

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| <场景 1，含触发关键词> | <反场景 1> |
| <场景 2，含触发关键词> | <反场景 2> |
| <场景 3，含触发关键词> | <反场景 3> |
| | <反场景 4> |

## The Iron Law

```
<条件 A> → <结果 A>
<条件 B> → <结果 B>
```

## The Rules

### Rule 1: <规则名称>

**What:** <一句话说明规则适用场景。>

| 维度 | 检查项 |
|------|--------|
| <维度 1> | <具体检查内容> |
| <维度 2> | <具体检查内容> |

**Bad:**
```
<反模式示例>
→ <错误后果>
```

**Good:**
```
<正确做法>
→ <正确执行结果>
```

### Rule 2: <规则名称>
...（重复上述结构）

## Rationalization Table

| 借口 | 为什么不成立 |
|------|-------------|
| "<借口 1>" | <反驳理由> |
| "<借口 2>" | <反驳理由> |
| "<借口 3>" | <反驳理由> |
| "<借口 4>" | <反驳理由> |

## Red Flags

- <Red Flag 1>
- <Red Flag 2>
- <Red Flag 3>
- <Red Flag 4>

## Detection Patterns（可选，用于安全类）

```regex
<检测正则 1>
<检测正则 2>
```

## Verification Checklist

### <场景 1>
- [ ] <检查项 1>
- [ ] <检查项 2>
- [ ] <检查项 3>

### <场景 2>
- [ ] <检查项 1>
- [ ] <检查项 2>

## Interaction with Other Skills

本 skill 是<前置门禁/质量门禁/...>——<说明上下游关系>。

| 关联 Skill | 触发时机 | 联动方式 |
|------------|---------|---------|
| **<skill-a>** | <触发时机> | <联动方式> |
| **<skill-b>** | <触发时机> | <联动方式> |
```

### 写作要点

| 章节 | 必须有 | 常见错误 |
|------|--------|---------|
| Iron Law | "不X就不Y" 句式，无条件阻断 | 用"建议"、"应该"等弱语气 |
| Rules | 每条都有 Bad/Good 对照 | 只有正面指导，无反例 |
| Rationalization Table | ≥4 条借口反驳 | 只列 1-2 条，封堵不充分 |
| Red Flags | 对应每个自我欺骗借口 | 模糊不清，无具体场景 |
| Verification Checklist | 分场景，每场景独立子清单 | 所有检查项混在一起 |

### 例子参考

- `agent-security-guard/SKILL.md` — 安全规则强制执行
- `skill-review-workflow/SKILL.md` — 审查质量门禁

---

## 模板 2: Technique（技术流程型）

### 适用场景

教怎么做一件事，含具体步骤、命令、Expected Output。特征词：怎么做、步骤、流程、命令。

### 结构模板

```markdown
---
name: <动词-名词>
description: Use when <触发条件>.
version: 1.0.0
metadata:
  tags: [tag1, tag2, tag3]
  related_skills: []
---

# <Skill 标题>

## Overview

<2-3 句说明这个 skill 解决什么问题、核心流程是什么。>

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| <场景 1，含触发关键词> | <反场景 1> |
| <场景 2> | <反场景 2> |
| <场景 3> | <反场景 3> |

## The Process

```
<流程概览图，5-7 个箭头连接的关键步骤>
   │
   ▼
   ...
```

### Step 1: <步骤名称>

**Expected Output:** `<具体输出格式>`

```
<决策树或步骤详图>
  │
  ├── 分支 A → <行动>
  │
  └── 分支 B → <行动>
```

**命令：**
```bash
<具体命令 1>
<具体命令 2>
```

**If fails:**
- 失败现象 A → <根因> → <修复命令>
- 失败现象 B → <根因> → <修复命令>

### Step 2: <步骤名称>
...（重复上述结构）

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| <错误现象 1> | <根因 1> | <修复 1> |
| <错误现象 2> | <根因 2> | <修复 2> |
| <错误现象 3> | <根因 3> | <修复 3> |
| <错误现象 4> | <根因 4> | <修复 4> |

## Rationalization Table（可选）

| 借口 | 为什么不成立 |
|------|-------------|
| "<借口 1>" | <反驳理由> |
| "<借口 2>" | <反驳理由> |

## Red Flags

- 准备 <动作 1> → 停下，<正确做法>
- 准备 <动作 2> → 停下，<正确做法>

## Verification Checklist

- [ ] Step 1: <检查项>
- [ ] Step 2: <检查项>
- [ ] ...

## Interaction with Other Skills

<说明上下游关系和触发时机。>
```

### 写作要点

| 章节 | 必须有 | 常见错误 |
|------|--------|---------|
| Step | 每步都有 Expected Output | 只写"应该成功"等模糊词 |
| 命令 | 完整路径，可执行 | 用 `./deploy.sh` 等相对路径 |
| If fails | 至少 2 个失败分支 | 只写成功路径，无错误处理 |
| Common Pitfalls | 三段式（现象→原因→修复） | 只有现象，无根因和修复 |
| Red Flags | 对应具体的"准备做 X"动作 | 抽象的"不要粗心" |

### 例子参考

- `git-workflow-for-agents/SKILL.md` — Git 操作完整流程
- `cross-model-verification/SKILL.md` — 跨模型验证流程

---

## 模板 3: Pattern（思维模式型）

### 适用场景

提供思维框架、判断逻辑、决策模型。特征词：思路、框架、模型、判断。

### 结构模板

```markdown
---
name: <名词-名词>
description: Use when <触发条件>.
version: 1.0.0
metadata:
  tags: [tag1, tag2, tag3]
  related_skills: []
---

# <Skill 标题>

## Overview

<2-3 句说明这个 skill 提供什么思维框架、何时用、为什么有效。>

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| <场景 1> | <反场景 1> |
| <场景 2> | <反场景 2> |
| <场景 3> | <反场景 3> |

## The Framework

### Recognition Guide（何时用此模式）

```
什么情况应该用这个模式？
  │
  ├── 条件 1：具体场景描述
  │     └── 为什么适用
  │
  ├── 条件 2：具体场景描述
  │     └── 为什么适用
  │
  └── 什么情况不应该用
        └── 为什么不适用
```

### 核心要素

```
<框架的核心步骤/要素/判断点>

  要素 A
    │
    ▼
  要素 B
    │
    ▼
  要素 C
```

| 要素 | 含义 | 关键问题 |
|------|------|---------|
| <要素 A> | <说明> | <要问自己的问题> |
| <要素 B> | <说明> | <要问自己的问题> |
| <要素 C> | <说明> | <要问自己的问题> |

## Worked Examples

### Example 1: <场景标题>

**场景：**
<具体场景描述>

**应用步骤：**
1. <步骤 1>
2. <步骤 2>
3. <步骤 3>

**最终结果：**
<输出或决策>

### Example 2: <场景标题>
...（同上结构，至少 2 个例子）

## Boundary Conditions

| 边界条件 | 此模式是否适用 | 说明 |
|---------|-------------|------|
| <条件 1> | ✅/❌ | <为什么> |
| <条件 2> | ✅/❌ | <为什么> |
| <条件 3> | ✅/❌ | <为什么> |
| <条件 4> | ✅/❌ | <为什么> |

## Common Pitfalls

| # | 错误 | 修复 |
|---|------|------|
| 1 | <错误 1> | <修复 1> |
| 2 | <错误 2> | <修复 2> |
| 3 | <错误 3> | <修复 3> |

## Verification Checklist

- [ ] <检查项 1>
- [ ] <检查项 2>
- [ ] <检查项 3>

## Interaction with Other Skills

<说明上下游关系。>
```

### 写作要点

| 章节 | 必须有 | 常见错误 |
|------|--------|---------|
| Recognition Guide | "什么情况应该/不应该用"分明 | 只写正面，无反场景 |
| Worked Examples | ≥2 个完整例子（场景+步骤+结果） | 只有 1 个例子或缺少结果 |
| Boundary Conditions | 边界条件表，标 ✅/❌ | 不写边界，看似万能 |
| 核心要素 | 表格化呈现，含关键问题 | 文字描述，难以对照 |

---

## 模板 4: Reference（参考查阅型）

### 适用场景

查阅信息、规范、配置。特征词：参考、速查、字段、参数。

### 结构模板

```markdown
---
name: <名词-名词>
description: Use when <触发条件>.
version: 1.0.0
metadata:
  tags: [reference, tag2, tag3]
  related_skills: []
---

# <Skill 标题>

## Overview

<2-3 句说明这个 skill 提供什么信息的速查、为什么需要、覆盖哪些维度。>

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| <场景 1> | <反场景 1> |
| <场景 2> | <反场景 2> |
| <场景 3> | <反场景 3> |

## Quick Reference

### <类别 1>速查

| 维度 A | 维度 B | 维度 C | 错误配置后果 |
|--------|--------|--------|-------------|
| <值 1> | <值 2> | <值 3> | <错误后果> |
| ...    | ...    | ...    | ...         |

### <类别 2>速查
...（按需添加多个速查表）

## Detailed Reference

### <条目 1>

**配置语法：**
```yaml
<配置示例>
```

**关键约束：**
- <约束 1>
- <约束 2>
- <约束 3>

### <条目 2>
...（每个条目独立小节）

## Constraints & Limits

| 限制项 | 值 | 超出后果 |
|--------|-----|---------|
| <限制 1> | <值 1> | <后果> |
| <限制 2> | <值 2> | <后果> |
| <限制 3> | <值 3> | <后果> |

## Troubleshooting

### 类型 A：<问题分类>

**Expected Output:** <4 步后期望的结果>

```
1. <检查步骤 1>
   ├── Expected: <结果 A> → 进入 2
   └── Expected: <结果 B> → <修复>

2. <检查步骤 2>
   ├── Expected: <结果 A> → 进入 3
   └── Expected: <结果 B> → <修复>

3. <检查步骤 3>
   └── Expected: <最终结果>

4. <最终步骤>
   └── Expected: <问题已解决>
```

**Common mistakes（同类型）：**
- <错误 1> → <原因> → <修复>
- <错误 2> → <原因> → <修复>

### 类型 B：<问题分类>
...（每个问题类型独立小节）

## Common Mistakes

| 错误 | 为什么错 | 正确做法 |
|------|---------|---------|
| <错误 1> | <原因 1> | <做法 1> |
| <错误 2> | <原因 2> | <做法 2> |
| <错误 3> | <原因 3> | <做法 3> |

## Verification Checklist

- [ ] <检查项 1>
- [ ] <检查项 2>
- [ ] <检查项 3>

## Interaction with Other Skills

<说明上下游关系。>
```

### 写作要点

| 章节 | 必须有 | 常见错误 |
|------|--------|---------|
| Quick Reference | 速查表放最前面 | 详细说明在前，速查在后 |
| Constraints & Limits | 限制值 + 超出后果 | 只写限制不写后果 |
| Troubleshooting | 4 步诊断路径 + 每步 Expected | 只有"应该正常"等模糊词 |
| Common Mistakes | 错误/原因/正确做法三栏 | 缺正确做法列 |

### 例子参考

- `agent-config-reference/SKILL.md` — 多平台配置速查+排错

---

## 模板选择决策

```
你 Phase 0 判定的类型是？
  │
  ├── Discipline-enforcing → 模板 1
  ├── Technique            → 模板 2
  │         └── 如果 > 8k chars 或有分支决策树
  │               → 配合 addyosmani-minimalist-style.md 使用
  ├── Pattern              → 模板 3
  └── Reference            → 模板 4
```

---

## 写作顺序建议

1. **先填 frontmatter** — `name` 和 `description` 决定后续所有内容
2. **再填 When to Use** — 触发场景定下来，正文才不会跑偏
3. **写 Overview** — 2-3 句浓缩全 skill 的核心
4. **写正文核心章节** — Rules / Steps / Framework / Quick Reference
5. **写 Common Pitfalls** — 把每步可能出错的地方列出来
6. **写 Verification Checklist** — 总结所有检查项
7. **写 Interaction** — 上下游关系，最后写

反对顺序：先写 Overview → 再定 name → 最后写 When to Use。这样会导致 name 和 description 频繁返工。

---

*本文档是 skill-authoring-workflow 的延伸阅读附件，不单独加载。*
