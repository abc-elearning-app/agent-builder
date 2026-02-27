#!/bin/bash
# Agent Builder for Claude Code — Installation Script
# Copies agent-builder files into the current project.
# Usage: bash install.sh [target_dir]
#   target_dir: Optional. Defaults to current directory.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"

install_commands() {
  mkdir -p "$TARGET_DIR/.claude/commands"
  cp "$SCRIPT_DIR/.claude/commands/agent-builder.md" "$TARGET_DIR/.claude/commands/"
}

install_agents() {
  mkdir -p "$TARGET_DIR/.claude/agents"
  cp "$SCRIPT_DIR/.claude/agents/builder-engine.md" "$TARGET_DIR/.claude/agents/"
}

install_templates() {
  mkdir -p "$TARGET_DIR/templates" "$TARGET_DIR/validators" "$TARGET_DIR/specs"
  cp "$SCRIPT_DIR/templates/"*.md "$TARGET_DIR/templates/" 2>/dev/null || true
  cp "$SCRIPT_DIR/validators/"*.sh "$TARGET_DIR/validators/" 2>/dev/null || true
  chmod +x "$TARGET_DIR/validators/"*.sh 2>/dev/null || true
  cp "$SCRIPT_DIR/specs/"*.md "$TARGET_DIR/specs/" 2>/dev/null || true
}

verify_installation() {
  local ok=true
  test -f "$TARGET_DIR/.claude/commands/agent-builder.md" || { echo "  ❌ Missing: .claude/commands/agent-builder.md"; ok=false; }
  test -f "$TARGET_DIR/.claude/agents/builder-engine.md" || { echo "  ❌ Missing: .claude/agents/builder-engine.md"; ok=false; }
  test -d "$TARGET_DIR/templates" || { echo "  ❌ Missing: templates/"; ok=false; }
  test -d "$TARGET_DIR/validators" || { echo "  ❌ Missing: validators/"; ok=false; }
  test -d "$TARGET_DIR/specs" || { echo "  ❌ Missing: specs/"; ok=false; }

  if $ok; then
    echo "✅ Installation complete!"
    echo ""
    echo "Usage:"
    echo "  Run /agent-builder in Claude Code to create a new command or agent."
    echo "  Run /agent-builder <description> to skip the first question."
  else
    echo "❌ Installation incomplete. Check errors above."
    exit 1
  fi
}

echo "🚀 Installing Agent Builder for Claude Code..."
echo "   Target: $TARGET_DIR"
echo ""

install_commands
install_agents
install_templates
verify_installation
