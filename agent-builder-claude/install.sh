#!/bin/bash
# Agent Builder for Claude Code — Installation Script
# Copies agent-builder files into the current project.
# Usage: bash install.sh [target_dir]
#   target_dir: Optional. Defaults to current directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"
FORCE="${2:-}"

confirm_overwrite() {
  local file="$1"
  if [ -f "$file" ] && [ "$FORCE" != "--force" ]; then
    echo "  ⚠️  File đã tồn tại: $file"
    printf "  Ghi đè? (y/N): "
    read -r answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
      echo "  → Bỏ qua: $file"
      return 1
    fi
  fi
  return 0
}

install_commands() {
  mkdir -p "$TARGET_DIR/.claude/commands"
  if confirm_overwrite "$TARGET_DIR/.claude/commands/agent-builder.md"; then
    cp "$SCRIPT_DIR/.claude/commands/agent-builder.md" "$TARGET_DIR/.claude/commands/"
    echo "  ✓ .claude/commands/agent-builder.md"
  fi
}

install_agents() {
  mkdir -p "$TARGET_DIR/.claude/agents"
  if confirm_overwrite "$TARGET_DIR/.claude/agents/builder-engine.md"; then
    cp "$SCRIPT_DIR/.claude/agents/builder-engine.md" "$TARGET_DIR/.claude/agents/"
    echo "  ✓ .claude/agents/builder-engine.md"
  fi
}

install_templates() {
  mkdir -p "$TARGET_DIR/templates" "$TARGET_DIR/validators" "$TARGET_DIR/specs"
  cp "$SCRIPT_DIR/templates/"*.md "$TARGET_DIR/templates/" 2>/dev/null || true
  cp "$SCRIPT_DIR/validators/"*.sh "$TARGET_DIR/validators/" 2>/dev/null || true
  chmod +x "$TARGET_DIR/validators/"*.sh 2>/dev/null || true
  cp "$SCRIPT_DIR/specs/"*.md "$TARGET_DIR/specs/" 2>/dev/null || true
  echo "  ✓ templates/, validators/, specs/"
}

verify_installation() {
  echo ""
  local ok=true
  test -f "$TARGET_DIR/.claude/commands/agent-builder.md" || { echo "  ❌ Thiếu: .claude/commands/agent-builder.md"; ok=false; }
  test -f "$TARGET_DIR/.claude/agents/builder-engine.md" || { echo "  ❌ Thiếu: .claude/agents/builder-engine.md"; ok=false; }
  test -d "$TARGET_DIR/templates" || { echo "  ❌ Thiếu: templates/"; ok=false; }
  test -d "$TARGET_DIR/validators" || { echo "  ❌ Thiếu: validators/"; ok=false; }
  test -d "$TARGET_DIR/specs" || { echo "  ❌ Thiếu: specs/"; ok=false; }

  if $ok; then
    echo "✅ Cài đặt thành công!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 Files đã cài:"
    echo "   .claude/commands/agent-builder.md  ← Slash command (entry point)"
    echo "   .claude/agents/builder-engine.md   ← Subagent (generation engine)"
    echo "   templates/                         ← Format templates"
    echo "   validators/                        ← Validation scripts"
    echo "   specs/                             ← Format specifications"
    echo ""
    echo "🚀 Cách sử dụng:"
    echo "   /agent-builder              ← Bắt đầu tạo command hoặc agent mới"
    echo "   /agent-builder <mô tả>     ← Tạo nhanh với mô tả sẵn"
    echo ""
    echo "💡 Ví dụ:"
    echo "   /agent-builder tạo lệnh deploy lên staging"
    echo "   /agent-builder tạo trợ lý review code Python"
    echo ""
    echo "📖 Agent Builder sẽ hỏi bạn vài câu, tự phát hiện loại"
    echo "   (command hay agent), tạo file, validate, và cài đặt."
    echo "   Mọi thứ tự động — bạn chỉ cần mô tả ý tưởng!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  else
    echo "❌ Cài đặt chưa hoàn tất. Kiểm tra lỗi bên trên."
    exit 1
  fi
}

echo "🚀 Đang cài đặt Agent Builder cho Claude Code..."
echo "   Thư mục: $TARGET_DIR"
echo ""

install_commands
install_agents
install_templates
verify_installation
