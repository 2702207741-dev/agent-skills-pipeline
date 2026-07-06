---
name: platform-adapters
description: 内部参考文档——多平台工具名和路径映射（Hermes Agent / Claude Code / Codex CLI / Cursor）。skill-authoring-workflow 的延伸阅读附件，不单独加载。
---

# Platform Adapters — 多平台工具/路径映射

> 本文档是 `skill-authoring-workflow` 的内部参考。
> SKILL.md 中涉及平台特定命令和路径时，从这里查映射关系。

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

*本文档是 skill-authoring-workflow 的延伸阅读附件，不单独加载。*
