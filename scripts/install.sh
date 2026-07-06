#!/usr/bin/env bash
# Agent Skill Platform — 一键安装脚本
# 自动检测 AI Agent 平台并安装所有 skill + 工具链

set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
PLATFORMS_FOUND=()

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}═══ Agent Skill Platform 安装器 ═══${NC}"
echo ""

# ─── 检测已安装的平台 ───

if [ -d "$HOME/.hermes/skills" ]; then
    PLATFORMS_FOUND+=("hermes")
    echo -e "  ${GREEN}✓${NC} Hermes Agent"
fi

if command -v claude &>/dev/null || [ -d "$HOME/.claude" ]; then
    PLATFORMS_FOUND+=("claude")
    echo -e "  ${GREEN}✓${NC} Claude Code"
fi

if command -v codex &>/dev/null || [ -d "$HOME/.codex" ]; then
    PLATFORMS_FOUND+=("codex")
    echo -e "  ${GREEN}✓${NC} Codex CLI"
fi

if [ -d "$HOME/.cursor" ]; then
    PLATFORMS_FOUND+=("cursor")
    echo -e "  ${GREEN}✓${NC} Cursor"
fi

if [ ${#PLATFORMS_FOUND[@]} -eq 0 ]; then
    echo -e "  ${YELLOW}未检测到已知 AI Agent 平台${NC}"
    echo "  手动安装路径参考:"
    echo "    Hermes Agent:  ~/.hermes/skills/"
    echo "    Claude Code:   ~/.claude/skills/"
    echo "    Codex CLI:     ~/.codex/skills/"
    echo "    Cursor:        ~/.cursor/skills/"
    exit 0
fi

# ─── 安装到每个检测到的平台 ───

for platform in "${PLATFORMS_FOUND[@]}"; do
    case $platform in
        hermes) TARGET="$HOME/.hermes/skills" ;;
        claude) TARGET="$HOME/.claude/skills" ;;
        codex)  TARGET="$HOME/.codex/skills" ;;
        cursor) TARGET="$HOME/.cursor/skills" ;;
    esac

    echo ""
    echo -e "${BLUE}── 安装到 ${platform} ──${NC}"
    mkdir -p "$TARGET"

    # 安装所有 skill（skills/ 目录下的每个子目录）
    for skill_path in "$SKILL_DIR/skills/"*/; do
        skill_name=$(basename "$skill_path")
        # 跳过 INDEX.md
        [ "$skill_name" = "INDEX.md" ] && continue

        dest="$TARGET/$skill_name"
        if [ -d "$dest" ]; then
            rm -rf "$dest"
        fi
        cp -r "$skill_path" "$dest"
        echo -e "  ${GREEN}✓${NC} $skill_name"
    done
done

# ─── 验证 ───

echo ""
echo -e "${BLUE}── 验证安装 ──${NC}"

INSTALLED=0
for platform in "${PLATFORMS_FOUND[@]}"; do
    case $platform in
        hermes) TARGET="$HOME/.hermes/skills" ;;
        claude) TARGET="$HOME/.claude/skills" ;;
        codex)  TARGET="$HOME/.codex/skills" ;;
        cursor) TARGET="$HOME/.cursor/skills" ;;
    esac

    count=$(find "$TARGET" -name "SKILL.md" -maxdepth 3 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✓${NC} $platform — $count 个 skill 已安装"
    INSTALLED=$((INSTALLED + count))
done

echo ""
echo -e "${GREEN}═══ 安装完成 ═══${NC}"
echo ""
echo "  平台: ${PLATFORMS_FOUND[*]}"
echo "  共安装: $INSTALLED 个 skill"
echo "  工具链: scripts/init_skill.py | validate-skill.py | package_skill.py"
echo ""
echo "  使用: 对你的 Agent 说 '写个 skill' 或 '创建一个 skill'"
echo ""
