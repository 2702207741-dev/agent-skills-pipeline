#!/usr/bin/env bash
# Install registered skills into detected agent platforms.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="$ROOT_DIR/skills.json"

DRY_RUN=1
YES=0
SKIP_EXISTING=0

usage() {
    cat <<'EOF'
Usage: scripts/install.sh [--dry-run] [--apply] [--yes] [--skip-existing]

Options:
  --dry-run        Show planned installs without writing anything. This is the default.
  --apply          Write changes after showing the diff preview.
  --yes            Non-interactive apply mode; existing targets are backed up first.
  --skip-existing  Leave existing skill directories untouched.
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --apply) DRY_RUN=0 ;;
        --yes) YES=1; DRY_RUN=0 ;;
        --skip-existing) SKIP_EXISTING=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
    shift
done

if [ ! -f "$REGISTRY" ]; then
    echo "Missing registry: $REGISTRY"
    exit 1
fi

read_registry() {
    python - "$REGISTRY" <<'PY'
import json
import sys
from pathlib import Path

registry = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for skill in registry["skills"]:
    print(f"{skill['name']}\t{skill['path']}\t{skill.get('category', 'meta')}")
PY
}

platform_targets() {
    if [ -d "$HOME/.hermes/skills" ]; then
        printf "hermes\t%s\n" "$HOME/.hermes/skills"
    fi
    if command -v claude >/dev/null 2>&1 || [ -d "$HOME/.claude" ]; then
        printf "claude\t%s\n" "$HOME/.claude/skills"
    fi
    if command -v codex >/dev/null 2>&1 || [ -d "$HOME/.codex" ]; then
        printf "codex\t%s\n" "$HOME/.codex/skills"
    fi
    if [ -d "$HOME/.cursor" ]; then
        printf "cursor\t%s\n" "$HOME/.cursor/skills"
    fi
}

preview_diff() {
    source_dir="$1"
    dest="$2"
    echo "[DIFF] $source_dir -> $dest"
    if [ -d "$dest" ]; then
        diff -ru --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' "$dest" "$source_dir" || true
    else
        find "$source_dir" -type f ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' | sort | while read -r file; do
            rel="${file#$source_dir/}"
            echo "  + $rel"
        done
    fi
}

write_audit() {
    action="$1"
    platform="$2"
    skill_name="$3"
    source_dir="$4"
    dest="$5"
    backup="$6"
    rollback_mode="$7"

    audit_dir="$HOME/.our-skills-audit"
    mkdir -p "$audit_dir"
    python - "$audit_dir/events.jsonl" "$action" "$platform" "$skill_name" "$source_dir" "$dest" "$backup" "$rollback_mode" <<'PY'
import json
import sys
from datetime import datetime
from pathlib import Path

path, action, platform, skill, source, dest, backup, rollback = sys.argv[1:]
event = {
    "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    "installer": "scripts/install.sh",
    "action": action,
    "platform": platform,
    "skill": skill,
    "source": source,
    "destination": dest,
    "backup": backup or None,
    "rollback_mode": rollback,
}
with Path(path).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n")
PY
}

install_one() {
    platform="$1"
    base_target="$2"
    skill_name="$3"
    skill_rel_path="$4"
    category="$5"

    source_dir="$ROOT_DIR/$skill_rel_path"
    if [ ! -f "$source_dir/SKILL.md" ]; then
        echo "Missing SKILL.md for registered skill: $skill_name ($skill_rel_path)"
        return 1
    fi

    if [ "$platform" = "hermes" ]; then
        dest="$base_target/$category/$skill_name"
    else
        dest="$base_target/$skill_name"
    fi

    preview_diff "$source_dir" "$dest"

    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[DRY-RUN] $skill_name -> $dest"
        return 0
    fi

    mkdir -p "$(dirname "$dest")"

    if [ -e "$dest" ]; then
        if [ "$SKIP_EXISTING" -eq 1 ]; then
            echo "[SKIP] $dest already exists"
            return 0
        fi

        choice="backup"
        if [ "$YES" -eq 0 ]; then
            printf "%s exists. Choose [b]ackup, [s]kip: " "$dest"
            read -r choice
            case "$choice" in
                b|B|backup|"") choice="backup" ;;
                s|S|skip) echo "[SKIP] $dest"; return 0 ;;
                *) echo "Unknown choice: $choice"; return 1 ;;
            esac
        fi

        if [ "$choice" = "backup" ]; then
            backup="${dest}.backup.$(date +%Y%m%d%H%M%S)"
            mv "$dest" "$backup"
            echo "[BACKUP] $dest -> $backup"
            rollback_mode="restore_backup"
        fi
    else
        backup=""
        rollback_mode="remove_created_dest"
    fi

    cp -R "$source_dir" "$dest"
    find "$dest" -name '__pycache__' -type d -prune -exec rm -rf {} +
    find "$dest" \( -name '*.pyc' -o -name '*.pyo' \) -type f -delete
    echo "[OK] $skill_name -> $dest"
    write_audit "install" "$platform" "$skill_name" "$source_dir" "$dest" "$backup" "$rollback_mode"
}

main() {
    platforms="$(platform_targets)"
    if [ -z "$platforms" ]; then
        echo "No supported agent platform directories found."
        echo "Manual targets: ~/.hermes/skills, ~/.claude/skills, ~/.codex/skills, ~/.cursor/skills"
        [ "$DRY_RUN" -eq 1 ] && exit 0
        exit 1
    fi

    echo "Agent Skill Platform installer"
    [ "$DRY_RUN" -eq 1 ] && echo "Mode: dry-run (default)"
    [ "$DRY_RUN" -eq 0 ] && echo "Mode: apply"

    while IFS=$'\t' read -r platform target; do
        [ -z "$platform" ] && continue
        echo ""
        echo "Platform: $platform ($target)"
        while IFS=$'\t' read -r skill_name skill_rel_path category; do
            install_one "$platform" "$target" "$skill_name" "$skill_rel_path" "$category"
        done < <(read_registry)
    done <<< "$platforms"
}

main
