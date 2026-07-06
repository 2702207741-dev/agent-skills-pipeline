---
name: agent-security-guard
description: Use when about to execute risky operations that could cause irreversible damage, data loss, or security incidents. Use before rm, git push --force, database migrations, or production deploys. Use when reviewing code that touches API keys, credentials, or secrets. Use when the agent detects a pattern that could trigger a safety incident.
version: 1.0.0
metadata:
  tags: [security, safety-guard, discipline-enforcing, risk-mitigation]
  related_skills: [skill-review-workflow]
---

# Agent Security Guard

## Overview

AI agent 执行的危险操作比人类更容易造成全局性破坏——一行 `rm -rf`、一次 `git push --force`、或一个含 API key 的 commit，几秒钟内就能造成不可逆损失。本 skill 在危险操作前强制执行安全扫描，在代码审查中检测安全模式。不遵守就停，不讨论，不绕过。

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 执行前含 `rm`、`rmdir`、`trash`、`drop` 的文件操作 | 普通的文件读写（读取、新建文件） |
| 执行 `git push --force`、`git push -f` | `git push`（非 force） |
| 数据库迁移、schema 变更、数据删除操作 | 只读数据库查询 |
| 生产环境部署、配置变更、权限修改 | 本地开发环境操作 |
| 代码审查时发现 API key、secret、password 模式 | 硬编码的公共配置（如 `BASE_URL`） |
| agent 怀疑输出可能含敏感信息 | 输出已经是公开信息 |

## The Iron Law

```
危险操作前没通过安全扫描 → 不执行。
API key 出现在 commit / log / 输出中 → 零容忍，立即停止并修复。
```

## The Rules

### Rule 1: 危险命令执行前必须扫描

**What:** 在以下命令执行前，必须通过对应检查项：

| 命令类型 | 触发检查 | 检查项 |
|---------|---------|--------|
| `rm` / `rmdir` / `trash` | 删除扫描 | 是否只删目标文件 / 是否进了回收站 / 是否确认 |
| `git push --force` | Force push 检查 | 远程有新 commit 吗 / 用 `--force-with-lease` 替代 |
| 数据库 DROP / DELETE | 数据删除检查 | 有 WHERE 子句吗 / 有确认步骤吗 |
| 生产部署 | 部署检查 | 有回滚方案吗 / 有 staging 验证吗 |

**Bad:**
```
agent: rm -rf build/
→ 直接执行，没检查 build/ 里有没有 .env 或 node_modules
```

**Good:**
```
agent: rm -rf build/
→ 先 ls build/ 确认内容
→ 如果含 .env → "检测到 .env，跳过；如果需要清空，手动确认"
→ 确认后再执行
```

### Rule 2: API Key 泄露零容忍

**What:** 在任何输出、commit、log 中发现以下模式，立即停止并修复：

```
检测正则（覆盖主流格式）：
├── sk-...                    ← OpenAI / Stripe / Anthropic key prefix
├── AKIA...                   ← AWS Access Key ID
├── AIza...                   ← Google API Key
├── xox[baprs]-...            ← Slack Token
├── Bearer <token>            ← Generic Bearer auth header
├── api_key=<SECRET_39f2250e>       ← URL-encoded key
├── password=<SECRET_39f2250e>      ← Inline password
├── --password <SECRET_6c08a52f>        ← CLI flag password
├── x-api-key: <SECRET_39f2250e>       ← Header key
└── "private_key" / "secret_key" / "api_secret"  ← Common field names
```

**扫描场景：**
1. **Commit 前** — 扫描 `git diff --cached` 和 `git diff`
2. **输出前** — 扫描 agent 即将发送的文本内容
3. **Log 输出** — 扫描任何写到 log 文件的请求/响应体

**Bad:**
```bash
git add .
git commit -m "add config"
→ .env 里的 OPENAI_API_KEY 被一起提交
```

**Good:**
```bash
git diff --cached | grep -i "sk-\|AKIA\|xox[baprs]-"
→ 如果匹配 → "检测到疑似 API key，已取消提交"
→ 检查 .gitignore 是否覆盖 .env
→ 再次 diff 确认干净后再提交
```

### Rule 3: Shell 注入防护

**What:** 执行 shell 命令时，识别以下危险模式并拒绝：

| 模式 | 风险 | 拒绝理由 |
|------|------|---------|
| `rm -rf /` 或 `rm -rf ~` | 递归删除根目录或 home | 极可能为拼写错误或注入 |
| `$(...)` 或 `` `...` `` 在不受信任输入上下文中 | 命令注入 | 外部输入可能含恶意 shell 代码 |
| `curl <url> \| bash` | 下载执行远程脚本 | 远程脚本不可信 |
| `chmod 777` | 全局可写 | 过度授权，最小权限原则 |
| `eval()` 或 `exec()` 处理不受信任字符串 | 代码注入 | 同命令注入 |

**Bad:**
```bash
curl https://example.com/setup.sh | bash
→ 远程脚本可能含恶意代码，直接执行
```

**Good:**
```bash
curl https://example.com/setup.sh -o /tmp/setup.sh
→ 先下载，审查内容，确认后再 bash /tmp/setup.sh
```

### Rule 4: 文件操作前确认意图

**What:** 以下文件操作必须显式确认，不能静默执行：

```
删除操作：
├── 删除单个文件 → 确认文件名
├── 删除目录 → 先 ls 确认内容
├── 递归删除（rm -rf）→ 列出将删除的文件列表
└── 清空回收站 → 双确认

覆盖操作：
├── 覆盖已有文件 → "文件 <path> 已存在，确认覆盖？"
└── 批量覆盖 → 列出所有将被覆盖的文件

格式转换 / 批量处理：
├── 10 个以上文件 → 先列出文件清单
└── 修改 config / .env → 显示 diff 确认
```

### Rule 5: Git 推送前检查

**What:** 每次 `git push` 前必须完成以下检查：

```
推送前：
├── git diff origin/main...HEAD → 确认只有该改的文件
├── git diff --cached | grep -i "sk-\|AKIA\|xox\|password\|secret" → 无匹配
├── git status → 没有 .env、*.key、*.pem 等敏感文件
└── commit message → 不含内部域名、IP、密钥
```

**Push --force 额外要求：**
- 改用 `git push --force-with-lease`
- 确认"远程有新 commit"（不是覆盖别人的工作）

## Rationalization Table

| 借口 | 为什么不成立 |
|------|-------------|
| "这只是本地操作，不会出问题" | 本地操作同样会删文件、提交 key。rm -rf 不区分本地和远程 |
| "这个 key 是测试环境的，没关系" | 测试 key 可能和生产共用基础设施，泄露仍然有效 |
| "我检查过了，没问题" | 人眼容易遗漏正则匹配的内容。扫描是机械的、可重复的 |
| "只有这一个 key，不会有人发现" | 泄露检测是概率性的，一次命中就出事故 |
| "这只是个示例，用户不会用真的 key" | 示例被复制到生产环境时 key 就进去了 |
| "先跑测试，安全扫描可以跳过" | 测试环境和生产环境的 key 可能不同，先扫再跑 |
| "安全扫描太慢，耽误事" | 安全事件造成的损失远超过几秒扫描时间 |

## Red Flags

- 准备执行 `rm -rf` 前没先 `ls` 确认目标内容
- `git push --force` 直接执行，没用 `--force-with-lease`
- `git diff --cached` 里有 `sk-`、`AKIA`、`xox` 等前缀仍要继续 commit
- agent 输出中含有 `password=`、`secret=`、`private_key` 字段值
- `curl ... | bash` 直接执行远程脚本
- `chmod 777` 出现在任何建议或命令中
- 发现安全问题但判断"这个应该没问题"然后绕过
- 批量操作（>10 文件）没列出清单

## Detection Patterns

### API Key Patterns

```regex
# OpenAI / Anthropic / Stripe
sk-[A-Za-z0-9]{20,}

# AWS Access Key
AKIA[0-9A-Z]{16}

# Google API Key
AIza[0-9A-Za-z_-]{35}

# Slack Token
xox[baprs]-[0-9a-zA-Z-]{10,}

# Generic patterns
(password|secret|api_key|private_key|token)\s*[:=]\s*["']?[A-Za-z0-9_\-]{8,}["']?
```

### Shell Injection Patterns

```bash
# Unsafe remote execution
curl <url> | bash
wget -qO- <url> | sh

# Command substitution from untrusted input
eval $user_input
`echo $untrusted | base64 -d | bash`

# Dangerous flags
rm -rf /   # root deletion
rm -rf ~   # home deletion
chmod 777  # world writable
```

### Git Danger Patterns

```bash
git push --force          # ← 必须改用 --force-with-lease
git push -f               # ← 同上
git add .                 # ← 可能混入敏感文件
git commit -m "update"    # ← 无意义 message 难以追溯
```

## Verification Checklist

执行前逐项确认：

### 删除操作
- [ ] 已列出将被删除的文件列表
- [ ] 已确认目标不含敏感文件（.env、*.key、*.pem）
- [ ] 已确认路径无拼写错误

### 推送操作
- [ ] `git diff --cached` 扫描无 API key 匹配
- [ ] `git status` 无敏感文件
- [ ] 如用 `--force` → 已改用 `--force-with-lease` 并说明原因

### 代码输出
- [ ] 输出不含 API key、password、secret 明文
- [ ] 示例代码中的 key 已用占位符替代
- [ ] 日志配置不会记录请求体中的 token

### 命令执行
- [ ] 无 `curl | bash` 模式
- [ ] 无 `rm -rf /` 或 `rm -rf ~`
- [ ] 无 `chmod 777`
- [ ] 外部输入未直接传入 `eval` / `exec`

## Interaction with Other Skills

本 skill 是所有危险操作的**前置门禁**——其他 skill 在执行可能造成不可逆损失的操作前应加载本 skill。

| 关联 Skill | 触发时机 | 联动方式 |
|------------|---------|---------|
| **git-workflow-for-agents** | commit / push 前 | `git add` 前扫描待暂存文件、`git push` 前扫描 diff、`--force` 时强制改 `--force-with-lease` |
| **skill-review-workflow** | 审查发现 Security 级别问题 | skill-review 自动加载本 skill 做深度扫描，Security 发现优先于其他 finding |
| **skill-pipeline-orchestrator** | Stage 2 审查阶段 | 与 skill-review-workflow 并行执行，安全扫描通过才能进入 Stage 3 |
| **cross-model-verification** | 第二模型发现安全相关 finding | 优先用本 skill 专项检测，cross-model 负责一般性逻辑审查 |
| **agent-config-reference** | 跨平台迁移 skill 时 | 迁移前加载本 skill 检查 config.yaml 中的 API key 隔离 |

**Pipeline 位置：**
```
任意 skill 执行危险操作前
         │
         ▼
agent-security-guard（本 skill）── 扫描通过
         │
         ▼
   继续执行操作

agent-security-guard ── 扫描失败 → 阻断操作，强制修复
```
