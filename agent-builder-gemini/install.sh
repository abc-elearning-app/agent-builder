#!/bin/bash
# Agent Builder for Gemini CLI — Installation Script
# Copies agent-builder files into the current project.
# Usage: bash install.sh [target_dir] [--force]
#   target_dir: Optional. Defaults to current directory.
#   --force:    Skip overwrite confirmation.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="${1:-.}"
FORCE=""

# Parse flags
for arg in "$@"; do
  case "$arg" in
    --force) FORCE="--force" ;;
  esac
done

# Remove --force from TARGET_DIR if it was passed as first arg
if [ "$TARGET_DIR" = "--force" ]; then
  TARGET_DIR="."
fi

confirm_overwrite() {
  local file="$1"
  if [ -f "$file" ] && [ "$FORCE" != "--force" ]; then
    echo "  ⚠️  File already exists: $file"
    printf "  Overwrite? (y/N): "
    read -r answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
      echo "  → Skipped: $file"
      return 1
    fi
  fi
  return 0
}

install_commands() {
  mkdir -p "$TARGET_DIR/.gemini/commands"
  if confirm_overwrite "$TARGET_DIR/.gemini/commands/agent-builder.toml"; then
    cp "$SCRIPT_DIR/.gemini/commands/agent-builder.toml" "$TARGET_DIR/.gemini/commands/"
    echo "  ✓ .gemini/commands/agent-builder.toml"
  fi
}

install_agents() {
  mkdir -p "$TARGET_DIR/.gemini/agents"
  if confirm_overwrite "$TARGET_DIR/.gemini/agents/builder-engine.md"; then
    cp "$SCRIPT_DIR/.gemini/agents/builder-engine.md" "$TARGET_DIR/.gemini/agents/"
    echo "  ✓ .gemini/agents/builder-engine.md"
  fi
}

install_support() {
  mkdir -p "$TARGET_DIR/templates" "$TARGET_DIR/validators" "$TARGET_DIR/specs"

  # Templates
  cp "$SCRIPT_DIR/templates/"* "$TARGET_DIR/templates/" 2>/dev/null || true
  echo "  ✓ templates/"

  # Validators
  cp "$SCRIPT_DIR/validators/"*.sh "$TARGET_DIR/validators/" 2>/dev/null || true
  chmod +x "$TARGET_DIR/validators/"*.sh 2>/dev/null || true
  echo "  ✓ validators/"

  # Specs
  cp "$SCRIPT_DIR/specs/"*.md "$TARGET_DIR/specs/" 2>/dev/null || true
  echo "  ✓ specs/"
}

verify_installation() {
  echo ""
  local ok=true
  test -f "$TARGET_DIR/.gemini/commands/agent-builder.toml" || { echo "  ❌ Missing: .gemini/commands/agent-builder.toml"; ok=false; }
  test -f "$TARGET_DIR/.gemini/agents/builder-engine.md" || { echo "  ❌ Missing: .gemini/agents/builder-engine.md"; ok=false; }
  test -d "$TARGET_DIR/templates" || { echo "  ❌ Missing: templates/"; ok=false; }
  test -d "$TARGET_DIR/validators" || { echo "  ❌ Missing: validators/"; ok=false; }
  test -d "$TARGET_DIR/specs" || { echo "  ❌ Missing: specs/"; ok=false; }

  if $ok; then
    echo "✅ Installation successful!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📍 Files installed:"
    echo "   .gemini/commands/agent-builder.toml  ← Custom command (entry point)"
    echo "   .gemini/agents/builder-engine.md     ← Subagent (generation engine)"
    echo "   templates/                           ← Format templates"
    echo "   validators/                          ← Validation scripts"
    echo "   specs/                               ← Format specifications"
    echo ""
    echo "🚀 Usage:"
    echo "   /agent-builder              ← Start creating a new command or agent"
    echo ""
    echo "💡 Examples:"
    echo "   /agent-builder"
    echo "   Then describe: 'tạo lệnh deploy lên staging'"
    echo "   Or: 'tạo trợ lý review code Python'"
    echo ""
    echo "📖 Agent Builder will ask you a few questions in Vietnamese,"
    echo "   auto-detect the type (command or agent), generate the file,"
    echo "   validate it, and install it. Fully automated!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  else
    echo "❌ Installation incomplete. Check errors above."
    exit 1
  fi
}

echo "🚀 Installing Agent Builder for Gemini CLI..."
echo "   Target: $TARGET_DIR"
echo ""

install_commands
install_agents
install_support
verify_installation
