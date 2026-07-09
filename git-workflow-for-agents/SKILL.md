---
name: git-workflow-for-agents
description: Use when the user says 提交代码, 创建PR, 分支管理, 推到远程, commit, pull request, or any full-cycle git operation. Use when an agent has completed a feature and needs to commit, branch, and submit a PR following project conventions.
version: 1.0.0
---

# Git Workflow for AI Agents

## Overview

git 历史是项目唯一的可追溯线索——半年后查 bug 时，能否快速定位"哪个 PR 引入的"、"为什么这样改"完全取决于 commit 粒度和 message 质量。`git add .` 一行混入不相关文件、`update` 这种无信息 message，会让追溯失效。这套工作流把 git 操作强制成"小步、精确、可解释"。

AI agent 使用 git 的标准化工作流。从 `git status` 到 merged PR 的完整链路——状态检查、分支管理、精确提交、PR 前自检、冲突处理。核心原则：小步提交、精确 add、描述性 message、PR 前自检后提交。

## When to Use

| Use When | Don't Use When |
|----------|----------------|
| 用户说"提交代码""commit""推到远程""push" | 只是 `git status` 或 `git log` 查看（不需要这个 skill） |
| 用户说"创建 PR""提 pull request" | 解决 merge conflict（作为单独的冲突处理/调试任务，不走完整提交流程） |
| 用户说"切分支""新建分支做这个功能" | 用户说"先别提交""不要 commit" |
| Agent 完成功能实现需要走提交流程 | 只是 `git clone` 下载代码 |
| 需要 rebase 或处理分支历史 | 修改 `.gitignore`（单文件操作，不需要完整工作流） |

## Step 1: 确认当前状态

**Expected Output:** `git status 输出 → 工作区干净 / 有 N 个未暂存修改 / 有 N 个未跟踪文件`

```
git status → 输出什么？
  │
  ├── nothing to commit, working tree clean
  │     └── → 继续 Step 2
  │
  ├── 有未暂存的修改（modified: ...）
  │     │
  │     ├── 属于当前任务 → git add <files>（精确添加）
  │     │
  │     └── 不属于当前任务
  │           ├── git stash push -m "WIP: <描述>"
  │           └── 或告知用户："发现非本任务的修改: <文件列表>，要 stash 还是忽略？"
  │
  └── 有未跟踪文件（Untracked files: ...）
        │
        ├── 需要提交 → git add <file>
        │
        └── 不需要 → 确认 .gitignore 已覆盖，或告知用户
```

**命令：**
```bash
git status                    # 查看状态
git stash push -m "WIP: ..."  # 暂存非当前任务的修改
git stash list                # 查看暂存列表
```

## Step 2: 分支管理

**Expected Output:** `当前在 <branch> / 已切换到 <new-branch> / 分支不存在需要创建`

```
需要新建分支？
  │
  ├── 是 → 从哪个基准创建？
  │         │
  │         ├── 从 main/master → git checkout -b <type>/<desc>
  │         └── 从其他分支 → git checkout -b <type>/<desc> origin/<base>
  │
  └── 否 → git checkout <existing-branch>
```

**分支命名规则：** `<type>/<short-description>`，全小写+连字符，≤ 50 chars。

| type | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/gallery-unlock` |
| `fix/` | Bug 修复 | `fix/backup-path-null` |
| `docs/` | 文档 | `docs/install-guide` |
| `chore/` | 杂项（工具、配置） | `chore/add-validate-script` |
| `refactor/` | 重构（不改功能） | `refactor/extract-validator` |

```bash
git checkout -b feat/gallery-unlock    # 新建功能分支
git branch -a                          # 查看所有分支
git branch -d feat/old-feature         # 删除已合并的本地分支
```

## Step 3: 精确提交

**Expected Output:** `commit hash + status 提示`

```
提交粒度：一个逻辑变更 = 一个 commit。
永远不用 git add . ——它会把所有改动混在一起。

git add <specific-files>
  │
  ├── 只加与当前变更直接相关的文件
  ├── 如果有多个逻辑变更 → 拆成多个 commit
  │
  ▼
git commit -m "<type>: <简短摘要>

<详细说明（可选）>"
```

**Commit message 格式（强制）：**

```
<type>: <简短摘要（≤72 chars，中文或英文）>

- 变更点 1
- 变更点 2
- 为什么这样改（如有非显而易见的决策）
```

**正确示例：**
```bash
git add skills/skill-review-workflow/SKILL.md skills/INDEX.md
git commit -m "feat: add skill-review-workflow with 23-item checklist

- 5 Rules with Bad/Good 对照
- Rationalization Table 封堵 5 种常见借口
- related_skills 引用 skill-authoring-workflow"
```

**错误示例（禁止）：**
```bash
git add .                          # ← 禁止！会混入不相关文件
git commit -m "update"             # ← 禁止！无意义的 message
git commit -m "fix stuff"          # ← 禁止！不描述修了什么
```

## Step 4: 保持同步

**Expected Output:** `Already up to date.` 或 `Successfully rebased` 或 `CONFLICT → 进入冲突处理流程`

```
提交完成 → 推之前先同步远程:
  │
  ├── git fetch origin
  │
  ├── 远程有新 commit？
  │     │
  │     ├── 是 → git pull --rebase origin main
  │     │         │
  │     │         ├── rebase 成功 → 继续
  │     │         │
  │     │         └── CONFLICT → 进入冲突处理
  │     │               │
  │     │               ├── git status 查看冲突文件
  │     │               ├── 手动解决冲突（编辑文件，删除 <<< === >>> 标记）
  │     │               ├── git add <resolved-files>
  │     │               ├── git rebase --continue
  │     │               └── 或放弃: git rebase --abort（回到 rebase 前状态）
  │     │
  │     └── 否 → 继续 Step 5
```

```bash
git fetch origin                              # 拉取远程更新
git pull --rebase origin main                 # rebase 到最新 main
git rebase --continue                         # 解决冲突后继续
git rebase --abort                            # 放弃本次 rebase
```

## Step 5: PR 前自检

**Expected Output:** `自检清单全部 ✓ → 进入 Step 6` 或 `发现 N 项需修复`

推送前必须逐项确认：

```
git diff origin/main...HEAD → 只改了该改的文件？
  │
  ├── 有多余文件？→ git reset HEAD <file> 撤销暂存
  │
  ├── 运行项目测试 → 全部通过？
  │     ├── 通过 → ✓
  │     └── 失败 → 修复，追加 commit，重新自检
  │
  ├── validate-skill.py 通过？（如适用）
  │
  ├── CHANGELOG 或文档需要更新？
  │     ├── 是 → 追加 commit
  │     └── 否 → ✓
  │
  └── Commit message 符合格式？
        ├── 是 → ✓
        └── 否 → git commit --amend 修改
```

```bash
git diff origin/main...HEAD --stat         # 查看改了哪些文件
git diff origin/main...HEAD                # 查看具体改动
git commit --amend -m "<new message>"       # 修改最后一次 commit message
```

## Step 6: 推送 + 创建 PR

**Expected Output:** `PR 创建链接 → https://github.com/.../pull/new/<branch>`

```bash
git push origin <branch-name>
# GitHub 会输出 PR 创建链接：https://github.com/.../pull/new/<branch>
```

**PR 描述模板（强制）：**

```markdown
## 做了什么

<一句话描述>

## 变更文件

- `path/to/file1` — <改动说明>
- `path/to/file2` — <改动说明>

## 验证

- [ ] 测试通过：`<test command>`
- [ ] validate-skill.py 通过（如适用）
- [ ] 手动验证：<截图/日志/步骤>

## 关联 Issue

Closes #<issue-number>（如有）
```

## Common Pitfalls

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| PR 包含不相关文件 | `git add .` | `git add <specific-files>` |
| Push 被拒（non-fast-forward） | 远程有新 commit，本地落后 | `git pull --rebase origin main` |
| Merge commit 满天飞 | 没用 rebase 用 merge | 默认用 `git pull --rebase` |
| Commit 在错误分支上 | 忘记切分支就开始改 | `git stash` → `git checkout -b <new>` → `git stash pop` |
| PR 被拒因 commit message 不清晰 | "fix"/"update"/"stuff" | `<type>: <summary>` 格式 |
| 误提交 API key/密码 | 没检查 `git diff` 内容 | `git diff --cached | grep -i "sk-\|AKIA\|xox\|password\|secret"` 扫描，发现匹配则拒绝提交 |
| `git add .` 混入敏感文件 | 未过滤 .env、*.key、*.pem | commit 前加载 agent-security-guard 做 API key 扫描，检测通过才提交 |
| Force push 丢掉别人的 commit | `git push --force` 覆盖远程 | 用 `git push --force-with-lease`（检查远程是否有新 commit） |
| Rebase 后分支历史混乱 | rebase 过程中操作错误 | `git rebase --abort` 回到 rebase 前 |

## Rationalization Table

| 借口 | 为什么不成立 |
|------|-------------|
| "就改了一个文件，不用 git add <file> 直接用 git add . 更快" | 以后你会习惯 git add . — 迟早混入不相关文件。习惯从第一天养成 |
| "commit message 随便写，PR 描述写清楚就行" | PR 被合并后，git log 只显示 commit message。6 个月后没人去看 PR 描述 |
| "不用 pull --rebase，merge 也没关系" | Merge commit 污染 git log，10 个 feature 分支 = 10 个无意义的 merge commit |
| "测试等下跑，先 push 再说" | CI 挂了你的 PR 一样过不了。本地跑测试比等 CI 快 10 倍 |
| "force push 没事，就我一个人在这个分支" | 你不知道别人有没有基于你的分支工作。`--force-with-lease` 永远比 `--force` 安全 |

## Red Flags

- 准备执行 `git add .` → 停下，精确 add
- 准备写 commit message "update" → 停下，用 `<type>: <summary>` 格式
- 准备 `git push --force` → 停下，换成 `--force-with-lease`
- PR 描述只有一句话没有验证步骤 → 补全模板
- 跳过 PR 前自检直接 push → 你的 commit 质量没保障

## Verification Checklist

提交前逐项确认：

- [ ] `git status` 干净或确认未提交文件都属于当前任务
- [ ] 在正确分支上（新功能 = feature 分支，格式 `<type>/<desc>`）
- [ ] 每个 commit 用 `git add <specific-files>` 精确添加
- [ ] Commit message 遵循 `<type>: <summary>` 格式（≤72 chars 摘要）
- [ ] `git diff origin/main...HEAD --stat` 确认只改了该改的文件
- [ ] 项目测试全部通过
- [ ] `validate-skill.py` 通过（如适用）
- [ ] PR 描述完整（做了什么 + 变更文件 + 验证步骤）
- [ ] 未使用 `git push --force`（如有必要则用 `--force-with-lease`）

## Interaction with Other Skills

本 skill 是其他 skill 的**基础设施层**——写 skill、审 skill、改代码都离不开 git 流程。

| 相关 Skill | 配合方式 |
|------------|---------|
| **skill-authoring-workflow** | SKILL.md 写完后，用 git-workflow 走提交 → PR 流程；新 skill 的分支命名用 `<type>/<skill-name>` 格式 |
| **skill-review-workflow** | skill-review 发现的问题修完后，用 git-workflow 提交修复；review 要求的更改拆成独立 commit |
| **项目自带审查流程** | PR 前按项目约定完成代码审查或质量检查，然后走本 skill 的 PR 前自检；review 意见按 commit 拆分 |
| **agent-security-guard** | commit 前加载 agent-security-guard 做 API key 扫描；`git add .` 前先扫描防止混入敏感文件 |
| **agent-config-reference** | skill 安装到多平台后，用 git-workflow 提交跨平台配置变更 |

**联合使用流程：**
```
写 skill → skill-authoring-workflow 走完 6 阶段
         → git-workflow 切分支、commit（commit 前 agent-security-guard 扫描）
         → skill-review-workflow 审查（23 项 + 安全扫描）
         → 修复问题，git-workflow 追加 commit
         → skill-pipeline-orchestrator Stage 4-5（package + deploy）
         → git-workflow 推送 + 创建 PR
```
