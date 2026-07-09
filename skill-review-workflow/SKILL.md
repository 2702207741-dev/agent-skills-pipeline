---
name: skill-review-workflow
description: Use when the user says "审查这个skill""review skill""检查skill质量""这个skill写得怎么样". Use when a new SKILL.md is ready for pre-commit quality validation. Use when the user wants an objective quality score for an existing skill. Do NOT use during drafting stage, for reviewing non-SKILL.md code, or when the user asks how to use a skill (load and explain directly).
version: 1.1.0
metadata:
  tags: [skill-review, quality-gate, discipline-enforcing, meta-skill]
  related_skills: [skill-authoring-workflow]
---

# Skill Review Workflow

## Overview

Skill 的 bug 是静默的——format 看着对，触发条件也对，但某条检查项漏了，agent 按错误指导执行。审查者的工作是确保交付前的 SKILL.md 是可用的。

审核 SKILL.md 的质量——对标 skill-authoring-workflow 的 23 项验证标准 + 5 维度评分卡。每个 skill 交付前必须通过此审查，总分 ≥ 40 才批准。不通过不批准，缺一项报告一项。

本 skill 审查 skill-authoring-workflow 方法论产出的 skill，也审查任何其他 SKILL.md。

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户说"审查这个 skill""review skill""检查 skill 质量""这个 skill 写得怎么样" | 用户只是问"这个 skill 怎么用"（只需加载解释，不需审查） |
| 新 skill 写完准备交付，用户说"帮我看看能不能过" | skill 还在草稿阶段（用户说"还在写"→等写完再审查） |
| 用户想了解某个 skill 的客观评分和问题清单 | 用户让你改 skill 的内容（审查只报告，不改代码——Rule 5） |
| 多个 skill 需要批量审查 | 审查的是 .py/.js/.ts 代码而非 SKILL.md（按普通代码审查处理） |
| 从 GitHub 拉下来的 skill 想评估能不能用 | 只是格式转换（如 .txt 转 .md）——不是审查 |

## The Iron Law

```
不通过全部 23 项检查 → 不批准交付。
逐项打勾，不过就是不过。只说"整体不错"不算审查。
```

## The Rules

### Rule 1: 先跑自动化，再人工审

**Expected Output:** `validate-skill.py 8/8 全过 → 进入人工审` 或 `N 项失败 → 先修格式再重跑`

**What:** 审查第一条命令永远是 `validate-skill.py`。8 项全过才能进入人工审查。格式问题不值得人工看。

**Bad:**
```
"我大致看了下格式应该没问题，直接看内容吧"
→ 可能漏掉 frontmatter 不闭合、description 超长等低级错误
```

**Good:**
```bash
python3 scripts/validate-skill.py skills/<skill-name>/SKILL.md
# 输出：
#   [✓] 以 --- 开头
#   [✓] Frontmatter 闭合+空行
#   ...全部通过 ✓
#   → 继续人工审查
```

### Rule 2: 逐项对照 23 项清单，生成评分卡

**Expected Output:** `完整评分卡（含 ✓/✗、Quality Scorecard、结论、修复项）`

**What:** 逐一检查 Verification Checklist 的格式(8项)+触发(5项)+内容(10项)。每项给 ✓ 或 ✗，✗ 项附具体说明。不能概括。

**23 项清单（审查时逐项复制到报告，不从其他文件重建）：**

| # | 类别 | 检查项 |
|---|------|--------|
| 1 | Format | 文件以 `---` 开头且无 BOM |
| 2 | Format | Frontmatter 闭合，且闭合后有空行 |
| 3 | Format | `name` ≤ 64 chars，全小写、数字、连字符 |
| 4 | Format | `description` ≤ 1024 chars，且以触发条件为主 |
| 5 | Format | `description` 无流程泄露（无步骤、命令清单、执行摘要） |
| 6 | Format | `When to Use` 表格存在，列名为 `Use When` / `Don't Use When` |
| 7 | Format | `Verification Checklist` 存在 |
| 8 | Format | 文件长度 ≤ 15000 chars |
| 9 | Trigger | 至少 5 个该触发场景可由 description 或 Use When 覆盖 |
| 10 | Trigger | 至少 3 个不该触发场景被 Don't Use When 拦截 |
| 11 | Trigger | Don't Use When ≥ 3 条 |
| 12 | Trigger | 常见误触发场景已覆盖，且与 Use When 互斥 |
| 13 | Trigger | description 含用户实际会说的关键词 |
| 14 | Content | Overview ≤ 3 句，说明用途、风险或价值 |
| 15 | Content | 所有命令精确可执行，含必要路径、参数或平台条件 |
| 16 | Content | 关键步骤有具体 Expected Output |
| 17 | Content | Technique 类型有成功/失败分支或 Failure Recovery |
| 18 | Content | Discipline 类型有 Iron Law、Rules(Bad/Good)、Rationalization Table |
| 19 | Content | Reference 类型有 Quick Reference 和 Constraints & Limits |
| 20 | Content | Pattern 类型有 Recognition Guide 和 ≥2 Worked Examples |
| 21 | Content | Common Pitfalls ≥ 3 条，且包含现象→原因→修复 |
| 22 | Content | related_skills 和正文提到的可加载 skill 均真实存在 |
| 23 | Content | 没有安全风险：密钥泄露、shell 注入、静默覆盖、危险权限建议 |

**输出格式（强制）：**

```
═══ Skill Review: <skill-name> ═══
  路径: <path>
  长度: <N> chars | 类型: <type> | 风格: <style>

  【格式检查 — validate-skill.py 已跑】:
  [✓] 8/8 全部通过

  【触发检查】(5 项):
  [✓] 9.  5 该触发场景全部匹配
  [✗] 10. 第 3 个不该触发场景漏拦截
           → "问存档位置在哪" 未被 Don't Use When 覆盖
  [✓] 11. Don't Use When ≥ 3 条
  [✓] 12. 常见误触发场景已覆盖
  [✓] 13. 用户常见表达方式已覆盖

  【内容检查】(10 项):
  [✓] 14. Overview 2 句，简洁
  [✗] 15. Step 3 "检查配置文件" → 无具体命令。改为 "cat config.yaml | grep model"
  [✓] 16. 每步有 Expected 输出
  ...

  Quality Scorecard:
    Trigger Precision:  4/5 ×2 =  8  ← 第3个反触发场景漏了
    Actionability:      4/5 ×3 = 12  ← Step 3 命令模糊
    Completeness:       5/5 ×2 = 10
    Conciseness:        5/5 ×1 =  5
    Verifiability:      5/5 ×2 = 10
    总分: 45/50

  结论: ⚠️ 有条件通过（总分 ≥ 40，但 2 项需修复后重新审查）
  修复项:
    #10 — 补充反触发："仅查看存档位置"→ Don't Use When
    #15 — Step 3 "检查配置文件" → "cat ~/.hermes/config.yaml | grep model"
```

### Finding Severity — 分级标准

审查发现的每个问题打上 severity，让作者知道优先级：

| Prefix | 含义 | 作者行动 |
|--------|------|---------|
| `Security:` | 最高优先级 | API key 泄露、shell 注入风险 → 加载 agent-security-guard 深度扫描 |
| `Critical:` | 阻断合并 | 格式错误（frontmatter 不闭合、name 超 64 char、description 含流程词）、触发条件完全失效 |
| `[ ]`（无前缀） | 必须修复 | 缺失 When to Use / Verification Checklist / Iron Law（Discipline 类型） |
| **Nit:** | 可选优化 | 措辞打磨、格式风格统一 |
| **Optional:** / **Consider:** | 建议项 | 可改进但不影响使用 |
| **FYI** | 仅知悉 | 供未来迭代参考，不需要本次修复 |

**优先级排序：** Security > Critical > 无前缀 > Nit > Optional > FYI

### Rule 3: 类型判定一致性

**What:** 检查 skill 的实际结构是否与声称的类型一致。

| 声称类型 | 必须有 | 缺少则扣分 |
|---------|--------|-----------|
| Discipline-enforcing | Iron Law + Rules(Bad/Good) + Rationalization Table | 缺 Rationalization → Completeness -1 |
| Technique | 精确命令 + Expected 输出 + If fails 分支 | 缺 Expected → Actionability -1 |
| Pattern | Recognition Guide + ≥2 Worked Examples | 缺第二个 Example → Completeness -1 |
| Reference | Quick Reference 表格 + Constraints | 缺 Constraints → Completeness -1 |

### Rule 4: 引用完整性

**Expected Output:** `相关 skill 引用全部经验证存在（附 find 命令输出）` 或 `N 个 skill 不存在 → 列出缺失项`

**What:** 引用不存在的 skill 会导致 agent 尝试加载时困惑。验证每个 `related_skills` 条目是否在已安装 skill 目录中真实存在。

**Bad:**
```
related_skills: [skill-that-doesnt-exist-yet]
→ agent 尝试加载时报错或困惑
```

**Good:**
```bash
for skill in skill-authoring-workflow agent-security-guard; do
  find ~/.hermes/skills/ ~/.claude/skills/ -name "$skill" -type d 2>/dev/null | head -1 \
    || echo "✗ $skill 不存在 — 检查引用或安装 skill"
done
# Expected: 所有 skill 找到，或缺失项已明确列出
```

### Rule 5: 审查不修改

**What:** 审查输出的是**问题清单**，不是修改后的代码。审查者只找问题+打分。作者自己修。

**Expected Output:** 问题清单（含 ✓/✗、具体位置、修复建议），无修改后的代码。

**Bad:**
```
"description 太长了，我帮你删掉了后面两句 →"
→ 越界。审查者改代码，作者失去修改主动权
```

**Good:**
```
"description 356 chars。建议缩到 150 以内，
 当前后半段 'Covers three engine paths...' 可删除"
→ 指出问题位置和原因，不改动原文
```

## Rationalization Table

| 借口 | 为什么不成立 |
|------|-------------|
| "格式检查脚本跑了，8/8 全过，剩下的我肉眼扫一下就行" | validate-skill.py 只检查格式。触发设计、命令精确度、类型一致性——脚本看不到，必须人工逐项 |
| "这个 skill 很简单，不需要 23 项" | 简单 skill 更易有隐藏问题——步骤少意味着每步承载更多责任，一步错全盘错 |
| "总分 42，≥40 已经通过了，别纠结了" | 通过了 ≠ 满分。找到的问题就该报告，修不修是作者的事，报不报是你的责任 |
| "related_skills 引用的 skill 以后可能会加" | 引用不存在 = agent 运行时困惑。引用只写已存在的，未来的用 TODO 注释 |
| "我没找到问题，但感觉哪里不对" | "感觉"不是审查结论。追到具体位置——是哪一步缺 Expected？哪个触发场景没覆盖？ |

## Red Flags

- 跳过 `validate-skill.py` 直接人工看 → 你在偷懒
- 只说"整体不错"没有逐项打勾 → 不是审查，是敷衍
- 发现问题后自己去改 → 越界。审查者不改代码
- 引用不验证就写 ✓ → 虚假通过
- 类型判定明显错误但不报告（Technique 没有 Expected 你说"还行"） → 失职
- 分数低于 20 但不拒绝 → 底线失守

## Verification Checklist

审查者自身审查——每个审查完成后逐项确认：

- [ ] `validate-skill.py` 8/8 全过（附输出）
- [ ] 23 项清单逐项打勾，✗ 项附具体说明
- [ ] 类型判定与 skill 实际结构一致
- [ ] `related_skills` 所有引用经验证存在
- [ ] Quality Scorecard 5 维度打分完成
- [ ] 总分 ≥ 20（<20 → 明确拒绝）
- [ ] 每个 ✗ 项给出了具体位置和原因（不是"有问题"而是"Step 3 L45 '检查配置'→缺具体命令"）
- [ ] 没有替作者修改任何内容

## Interaction with Other Skills

本 skill 是 pipeline 的质量门禁——审查通过才能进入下一阶段。

| 关联 Skill | 触发时机 | 联动方式 |
|------------|---------|---------|
| **skill-authoring-workflow** | SKILL.md 创作完成 | 审查 skill-authoring-workflow 产出的 SKILL.md |
| **agent-security-guard** | 审查发现 Security 级别问题 | 自动加载 agent-security-guard 做深度安全扫描 |
| **cross-model-verification** | 用户要求或审查发现复杂问题 | 送审查结果做第二模型交叉验证 |
| **skill-pipeline-orchestrator** | 审查通过（总分 ≥ 40） | 进入 Stage 2，串联后续打包部署流程 |

**Pipeline 位置：**
```
skill-authoring-workflow（创作）
         │
         ▼
skill-review-workflow（本 skill）←── agent-security-guard（安全扫描）
         │
         ├── 通过 → skill-pipeline-orchestrator Stage 3（交叉验证）
         │
         └── 不通过 → 回到 skill-authoring-workflow 修复
```
