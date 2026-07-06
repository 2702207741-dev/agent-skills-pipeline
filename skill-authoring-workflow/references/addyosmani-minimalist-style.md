---
name: addyosani-minimalist-style
description: 内部参考文档——Addyosmani 极简 SKILL.md 风格指南，适用于 Technique 类型 >8k chars 或含多分支决策树的 skill。skill-authoring-workflow 的延伸阅读附件，不单独加载。
---

# Addyosmani 极简风格指南

> 本文档是 `skill-authoring-workflow` 的内部参考。
> 适用条件：Technique 类型 +（>8k chars 或 含多分支决策树）。
> 不适用：Discipline-enforcing / Pattern / Reference 类型走 Hermes 原生 5 字段风格。

## 何时选 Addyosmani

```
你的 skill 特征是？
  │
  ├── Hermes 原生风格（5 字段 frontmatter，Markdown 表格，Bad/Good 对照）
  │     ├── Reference / Pattern / Discipline-enforcing
  │     └── Technique < 8k chars，无多分支
  │
  └── Addyosmani 极简风格
        ├── Technique > 8k chars
        └── 含多分支决策树
```

## 核心区别

| 维度 | Hermes 原生 | Addyosmani 极简 |
|------|-------------|----------------|
| Frontmatter | 5 字段（name+desc+version+tags+related） | 2 字段（name+desc） |
| 章节 | When to Use / Core Workflow / Common Pitfalls / Verification Checklist | 同上，但无 Rationalization Table / Iron Law |
| 代码块 | Bad/Good 对照 | ASCII 决策树 |
| 验证 | Expected Output + Verification Checklist | 验证信号对照表 + Exit codes |
| 示例 | 反例+正例 | Worked Examples |
| 适读性 | 表格化，清晰但略啰嗦 | 极简，信息密度高 |

## Frontmatter 格式

```yaml
---
name: <动词-名词>
description: Use when <触发条件>. Use when <第二触发条件>.
---
```

**绝对不要添加** `version` / `metadata.tags` / `metadata.related_skills` 等字段。
Addyosmani 平台扫描器不识别这些字段，添加无用且占 token。

**注意：** 迁移到 Hermes 时需要补全 5 字段。保留旧字段对 Hermes 无害。

## 章节组织

```
## When to Use
│
├── Overview（2 句，极简）
│
├── The Process / Pipeline / Core Workflow
│     ├── ASCII 流程图（必选）
│     └── 逐步骤（每步 ≤ 3 个子节）
│           ├── Expected Output（必选）
│           ├── 决策树（必选）
│           └── 命令（可选）
│
├── 验证信号对照表
│     ├── 信号 | 含义 | 行动
│
├── Common Pitfalls
│
├── Verification Checklist
│
└── Interaction with Other Skills
```

## ASCII 决策树规范

### 分支符号

```
├── 是 → <分支名称>    ← 条件成立
├── 否 → <分支名称>    ← 条件不成立
│
└── 分支名
      │
      ├── 子分支 A
      │
      └── 子分支 B
```

### Expected Output 格式

```
**Expected Output:** `<具体输出>`
```

- 禁止模糊词
- 必须可搜索

### 验证信号对照表

| 信号 | 含义 | 行动 |
|------|------|------|
| `Build ID: abc123` | 构建成功 | 继续部署 |
| `Error: port 3000 in use` | 端口被占用 | `kill $(lsof -t -i:3000)` |
| `All tests passed` | 测试通过 | 进入 PR 前自检 |

---

## 具体写法对照

### Overview

| | Hermes 原生 | Addyosmani 极简 |
|--|-------------|----------------|
| 长度 | 3-5 句 | 2 句 |
| 内容 | "背景 + 问题 + 解决方案 + 前提条件" | "问题 → 核心方法链" |
| 例子 | "git 历史是项目唯一的可追溯线索...这套工作流把 git 操作强制成..." | "One skill, five stages, zero manual handoffs." |

### When to Use

两种风格相同格式：

```
| Use When | Don't Use When |
|----------|----------------|
```

Addyosmani 保持用词统一，不用问句做标题，表格列数固定 2-4 列。

### 步骤正文

**Hermes 原生：**
```
## Step 1: 确认当前状态

**Expected Output:** `xxx`

git status → 输出什么？
  │
  ├── nothing to commit → 继续
  │
  └── 有未暂存修改
        │
        ├── git add <files>
        │
        └── git stash

**命令：**
git status
```

**Addyosmani 极简（去掉"命令"小节，决策树即为命令）：**
```
## Step 1: 确认当前状态

**Expected Output:** `xxx`

git status → 输出什么？
  │
  ├── nothing to commit → 继续 Step 2
  │
  └── 有未暂存修改
        │
        ├── git add <files>
        │
        └── git stash push -m "WIP: ..."
```

### Common Pitfalls

两种风格都用表格。Addyosmani 表格列数更少（3 列 vs 4 列）：

```
| Symptom | Root cause | Fix |
```

Bad/Good 对照在 Addyosmani 中保留但极简化——不用两个代码块，用 1 行注释：

```
curl https://setup.sh | bash   # ← 危险！先审查再执行
```

---

## 迁移指南

### Addyosmani → Hermes

从 Addyosmani 风格迁移到 Hermes 时，需要补：

```diff
+ version: 1.0.0
+ metadata:
+   tags: [tag1, tag2]
+   related_skills: [skill-a, skill-b]
```

正文部分：
- 如果需要 Bad/Good 对照 → 从决策树中提取反例，写成独立 Bad 代码块
- 如果需要 Iron Law → 从约束条件中提炼
- 不需要删任何内容，Hermes 兼容 Addyosmani 格式

### Hermes → Addyosmani

```diff
- version: 1.0.0
- metadata:
-   tags: [...]
-   related_skills: [...]
+ （删除这些字段）
```

正文部分：
- Bad/Good 对照 → 合并为决策树
- Iron Law → 在步骤中提到约束即可
- 缩短概览到 2 句

---

*本文档是 skill-authoring-workflow 的延伸阅读附件，不单独加载。*
