---
name: platform-adapters
description: 内部参考文档——多平台工具名和路径映射（Hermes Agent / Claude Code / Codex CLI / Cursor）+ OS 差异速查（Linux / macOS / Windows）。skill-authoring-workflow 的延伸阅读附件，不单独加载。
---

# Platform Adapters — 多平台工具/路径映射 + OS 差异速查

> 本文档是 `skill-authoring-workflow` 的内部参考。
> SKILL.md 中涉及平台特定命令和路径时，从这里查映射关系。
> 第一部分：Agent 平台差异。第二部分：操作系统差异。

---

## 工具名映射

### 文件操作

| 操作 | Hermes Agent | Claude Code | Codex CLI | Cursor |
|------|-------------|-------------|-----------|--------|
| 读文件 | `read_file(path)` | `Read` 工具 | `file_read` | Cmd+V |
| 写文件 | `write_file(path, content)` | `Write` 工具 | `file_write` | Cmd+S |
| 编辑文件 | `edit_file(path, old, new)` | `Edit` 工具 | `file_edit` | 手动编辑 |
| 批量替换 | `replace_text(glob, old, new)` | `Edit`(replace_all) | `file_replace` | Cmd+Shift+H |
| 创建目录 | `mkdir(path)` | `Bash: mkdir -p` | `bash` | 终端 |
| 列出目录 | `list(path)` | `ls`(Bash) | Glob | 侧边栏 |

### 代码执行

| 操作 | Hermes Agent | Claude Code | Codex CLI | Cursor |
|------|-------------|-------------|-----------|--------|
| 运行代码 | `run(python path)` | `Bash: python path` | `bash` | 终端 |
| 运行测试 | `run("pytest path")` | `Bash: pytest` | `bash` | 终端 |
| 安装依赖 | `run("pip install ...")` | `Bash: pip install` | `bash` | 终端 |
| 搜索代码 | `search(pattern, path)` | `Grep` 工具 | `grep` | Cmd+Shift+F |

### Git 操作

| 操作 | Hermes Agent | Claude Code | Codex CLI | Cursor |
|------|-------------|-------------|-----------|--------|
| 状态检查 | `run("git status")` | `Bash: git status` | `bash` | 终端 |
| 提交 | `run("git commit -m ...")` | `Bash: git commit` | `bash` | 终端 |
| 推送 | `run("git push")` | `Bash: git push` | `bash` | 终端 |
| 分支管理 | `run("git branch ...")` | `Bash: git branch` | `bash` | 终端 |
| Diff 查看 | `run("git diff ...")` | `Bash: git diff` | `bash` | 终端 |

### 项目操作

| 操作 | Hermes Agent | Claude Code | Codex CLI | Cursor |
|------|-------------|-------------|-----------|--------|
| 搜索文件 | `search_files(pattern)` | `Glob` 工具 | `glob` | Cmd+P |
| 查找内容 | `grep(pattern, path)` | `Grep` 工具 | `grep` | Cmd+Shift+F |
| Web 搜索 | `web_search(query)` | `WebSearch` 工具 | `web` | Chat |
| 网络请求 | `web_fetch(url)` | `WebFetch` 工具 | `curl` | 扩展 |

---

## 路径映射

### Config 文件路径

| 平台 | 主配置文件 | 环境变量 |
|------|-----------|---------|
| Hermes Agent | `~/.hermes/config.yaml` | `HERMES_CONFIG` |
| Claude Code | `~/.claude/settings.json` / `CLAUDE.md` | `CLAUDE_CONFIG` |
| Codex CLI | `~/.codex/config.yaml` | `CODEX_CONFIG` |
| Cursor | `.cursorrules`（项目根目录） | `CURSOR_RULES` |

### Skill 安装路径

| 平台 | Skill 目录 | 规则目录 |
|------|-----------|---------|
| Hermes Agent | `~/.hermes/skills/<category>/<name>/` | —（无独立规则目录） |
| Claude Code | `~/.claude/skills/<name>/` | —（skills 即规则） |
| Codex CLI | `~/.codex/skills/<name>/` | —（skills 即规则） |
| Cursor | `~/.cursor/skills/<name>/` | `~/.cursor/rules/<name>.md` |

### Python 脚本路径

| 脚本 | 标准路径 |
|------|---------|
| validate-skill.py | `scripts/validate-skill.py`（项目根相对路径） |
| package_skill.py | `scripts/package_skill.py` |
| init_skill.py | `scripts/init_skill.py` |
| install.sh | `scripts/install.sh` |

---

## 平台间迁移注意事项

### Hermes → Claude/Codex/Cursor

1. **保留** `name` 和 `description` 字段
2. `version` / `metadata` 字段可保留（其他平台忽略，无害）
3. 不需要 category 参数
4. 检查命令是否用了 Hermes 专有函数（`write_file()`、`run()`）
5. 如果用了，替换为 Claude / Codex 对应工具

### Claude/Codex → Hermes

1. 添加 `version: 1.0.0` + `metadata:` 块
2. 确认 `description` 以 "Use when" 开头（Hermes 强制）
3. 添加 category 参数
4. 检查路径 `~/.claude/skills/<name>/` → `~/.hermes/skills/<category>/<name>/`
5. 将 Tools（Read / Write / Edit 等）转换为 Hermes 函数名

---

## 平台特定行为

### Hermes Agent

- Skill 需要手动 `skill_view(name)` 加载，或通过 cron 自动
- Frontmatter 必须有 5 字段（含 category）
- Category 从 16 个枚举值选择

### Claude Code

- Skill 自动扫描 `~/.claude/skills/`
- 2 字段 frontmatter 足够
- 触发通过 description 匹配
- 不需要手动注册

### Codex CLI

- 与 Claude Code 高度兼容
- 同样自动扫描
- 使用 `codex exec --sandbox read-only` 运行沙箱命令

### Cursor

- Skills：按需触发加载，适合 >5k chars 的 skill
- Rules：始终加载，适合 <3k chars 的规则
- Rules 文件在 `~/.cursor/rules/<name>.md`，格式与 SKILL.md 相同

---

## OS 差异速查

写跨平台 skill 时，以下维度不需要每个 skill 重新发明。从这里查标准做法。

| 操作 | Linux | macOS | Windows (PowerShell) | Windows (CMD) |
|------|-------|-------|---------------------|---------------|
| **续行符** | `\` | `\` | `` ` `` | `^` |
| **包管理器** | `apt` / `yum` | `brew` | `winget` / `choco` | `winget` / `choco` |
| **进程信息** | `/proc/$PID/status` + `ps -T -p $PID` | `ps -M $PID` | `Get-Process -Id $PID` | `tasklist /FI "PID eq $PID"` |
| **系统调用追踪** | `strace -p $PID` | `dtruss -p $PID`（需 SIP 关闭） | —（无内置等价物） | —（无内置等价物） |
| **Python 调试 (native)** | `gdb -p $PID` + `python3-dbg` | `lldb -p $PID` + `py-bt` | —（py-spy 不支持 Windows） | —（用 `faulthandler` 替代） |
| **Python 采样 profiler** | `py-spy` | `py-spy` | —（不支持） | —（不支持） |
| **路径分隔符** | `/` | `/` | `\` 或 `/` | `\` |
| **临时目录** | `/tmp` | `/tmp` | `$env:TEMP` | `%TEMP%` |
| **查看环境变量** | `env \| grep VAR` | `env \| grep VAR` | `Get-ChildItem Env:VAR` | `echo %VAR%` |
| **递归删除目录** | `rm -rf path` | `rm -rf path` | `Remove-Item -Recurse -Force path` | `rmdir /s /q path` |
| **文件权限** | `chmod +x file` | `chmod +x file` | —（NTFS ACL，不需要 chmod） | —（NTFS ACL，不需要 chmod） |

### OS 检测

```bash
# 在所有平台通用
uname -s
# Expected:
#   Linux   → 走 Linux 列
#   Darwin  → 走 macOS 列
#   MINGW* / MSYS* → 走 Windows 列（Git Bash / WSL 环境）
#   CYGWIN* → 走 Windows 列（Cygwin 环境）
```

### Fallback 策略

写跨平台 skill 时，每个 OS 特定操作必须有 fallback：

```
首选命令 → 可用？
  │
  ├── 是 → 执行
  │
  └── 否 → 检查 OS？
        ├── macOS 无 /proc → 用 ps -M 替代
        ├── Windows 无 strace → 告知用户 Windows 不支持系统调用追踪
        └── Windows 无 py-spy → 告知用户用 faulthandler 替代方案
```

不要在 skill 正文里硬编码 OS 判断逻辑——引用本文档的 §OS 差异速查即可。

---

*本文档是 skill-authoring-workflow 的延伸阅读附件，不单独加载。*
