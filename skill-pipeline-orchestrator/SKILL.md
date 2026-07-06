---
name: skill-pipeline-orchestrator
description: Orchestrate a skill through the full lifecycle — author, review, cross-check, package, deploy — in one flow. Use when the user says "一键发布 skill", "走完整 pipeline", "发布这个 skill", or "skill 上线". Use when a new skill has been reviewed and is ready to package and deploy.
---

# Skill Pipeline Orchestrator

## Overview

One skill, five stages, zero manual handoffs. Author writes → Review checks → Cross-check verifies → Package bundles → Deploy installs. Each stage has a go/no-go gate. Failure at any stage loops back to fix before proceeding.

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户说"一键发布 skill""走完整 pipeline""skill 上线" | skill 还在草稿阶段（先走 skill-authoring-workflow） |
| 新 skill 审查通过后，需要打包和部署 | 只是修改已有 skill 的小问题（直接编辑，不需要走 pipeline） |
| 需要跨平台同时部署（Hermes+Claude+Codex+Cursor） | 用户说"先看看"，还没决定要上线 |
| 用户说"发布这个 skill"，已完成 skill-review | 审查未通过（先修完再发布） |

## The Pipeline

```
用户触发"一键发布"
       │
       ▼
  ┌─────────────┐
  │ Stage 1:    │
  │ Author      │── fail ──→ 回到 skill-authoring-workflow 修复
  └──────┬──────┘
         │ pass
         ▼
  ┌─────────────┐
  │ Stage 2:    │
  │ Review +    │── fail ──→ 回到 Stage 1 重写
  │ Security    │
  └──────┬──────┘
         │ pass
         ▼
  ┌─────────────┐
  │ Stage 3:    │
  │ Cross-Check │── fail ──→ 回到 Stage 2 重审
  └──────┬──────┘
         │ pass
         ▼
  ┌─────────────┐
  │ Stage 4:    │
  │ Package     │── fail ──→ 回到 Stage 2 修复格式
  └──────┬──────┘
         │ pass
         ▼
  ┌─────────────┐
  │ Stage 5:    │
  │ Deploy      │── fail ──→ 检查平台路径，重试
  └──────┬──────┘
         │ pass
         ▼
      上线完成
```

## Stage 1: Author

**Loads:** `skill-authoring-workflow`

```
skill-authoring-workflow 创作完成？
  │
  ├── 是 → validate-skill.py 8/8 通过？
  │     ├── 是 → Stage 1 pass → Stage 2
  │     └── 否 → 修复格式 → 重跑 validate-skill.py
  │
  └── 否 → 加载 skill-authoring-workflow → 走完整 6 阶段
```

**Expected Output:** SKILL.md 草稿 + validate-skill.py 8/8 通过

## Stage 2: Review + Security

**Loads:** `skill-review-workflow` + `agent-security-guard`

```
加载 skill-review-workflow 做 23 项审查
  │
  ├── 总分 ≥ 40？
  │     ├── 是 → 加载 agent-security-guard 做安全扫描
  │     │     ├── 无安全问题 → Stage 2 pass → Stage 3
  │     │     └── 发现安全问题 → 修复 → 重新 Stage 2
  │     │
  │     └── 否 → 修复审查发现的问题 → 重新 Stage 2
  │
  └── 发现 Critical 级别问题 → 强制修复，不允许跳过
```

**Expected Output:** skill-review 评分卡 + agent-security-guard 安全扫描报告

## Stage 3: Cross-Check

**Loads:** `cross-model-verification`

```
用户确认要交叉验证？
  │
  ├── 是 → 加载 cross-model-verification
  │     ├── 生成对抗性提示词
  │     ├── 发送第二模型
  │     ├── Diff 结果
  │     └── 无 Critical 发现 → Stage 3 pass → Stage 4
  │     └── 有发现 → 回到 Stage 2 修复
  │
  └── 否（用户跳过）→ Stage 3 pass → Stage 4（跳过验证）
```

**Expected Output:** 第二模型审查报告 + 分类后的发现清单

## Stage 4: Package

**Loads:** `../../scripts/package_skill.py`

```
运行 package_skill.py
  │
  ├── 验证通过 → 生成 .zip 包
  │     └── Stage 4 pass → Stage 5
  │
  └── 验证失败 → 列出错误项
        └── 回到 Stage 2 修复，重新 package
```

```bash
../../scripts/package_skill.py <skill-path>
# Expected: <skill-name>.zip 生成成功
```

**Expected Output:** `<skill-name>.zip` 文件

## Stage 5: Deploy

**Loads:** `agent-config-reference`（查平台路径） + `../../scripts/install.sh`

```
安装到各平台
  │
  ├── Hermes → cp -r <skill> ~/.hermes/skills/<category>/
  │     └── validate-skill.py 通过 → ✓
  │
  ├── Claude Code → cp -r <skill> ~/.claude/skills/
  │     └── validate-skill.py 通过 → ✓
  │
  ├── Codex CLI → cp -r <skill> ~/.codex/skills/
  │     └── validate-skill.py 通过 → ✓
  │
  └── Cursor → cp -r <skill> ~/.cursor/skills/
        └── validate-skill.py 通过 → ✓
```

全部通过 → **上线完成**

**Expected Output:** 4 个平台路径确认 + 各平台 validate-skill.py 通过

## Failure Recovery

| 失败阶段 | 失败原因 | 恢复动作 |
|---------|---------|---------|
| Stage 1 | 格式验证失败 | 修复 frontmatter / description / 结构 |
| Stage 1 | 内容不符合类型 | 重新走 skill-authoring-workflow 分类 |
| Stage 2 | 审查分数 < 40 | 按评分卡修复项逐项修改 |
| Stage 2 | 安全扫描发现问题 | 按 agent-security-guard 报告修复 |
| Stage 3 | 第二模型发现 Critical | 回到 Stage 2 修复后重审 |
| Stage 3 | 第二模型不可用 | 降级为自审，标记 degraded，继续 |
| Stage 4 | package_skill.py 失败 | 检查文件完整性，补全 resources |
| Stage 5 | 某平台安装失败 | 检查路径和权限，手动安装 |

## Interaction with Other Skills

- **skill-authoring-workflow** → Stage 1：创作阶段加载，走 6 阶段流程
- **skill-review-workflow** → Stage 2：23 项质量审查
- **agent-security-guard** → Stage 2：安全专项扫描（与 review 并行）
- **cross-model-verification** → Stage 3：第二模型交叉验证
- **agent-config-reference** → Stage 5：查各平台安装路径
- **git-workflow-for-agents** → Stage 5：部署后走 git 提交流程

## Verification Checklist

完成前逐项确认：

- [ ] Stage 1: SKILL.md 存在 + validate-skill.py 8/8 通过
- [ ] Stage 2: skill-review 评分 ≥ 40 + agent-security-guard 扫描通过
- [ ] Stage 3: cross-model 完成（或用户确认跳过）+ 结果分类
- [ ] Stage 4: package_skill.py 成功生成 .zip
- [ ] Stage 5: 4 个平台全部安装成功
- [ ] 任意阶段失败 → 已记录失败原因 → 已执行恢复动作
