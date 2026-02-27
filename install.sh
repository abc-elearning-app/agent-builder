#!/bin/bash
# Agent Builder — Install Script
# Copy agent-build workflow vào project hiện tại

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_FILE="$SCRIPT_DIR/agent-build.md"
TOML_FILE="$SCRIPT_DIR/.gemini/commands/agent-build.toml"

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ agent-build.md not found at $SCRIPT_DIR"
    echo "   Make sure you're running this script from the agent-builder directory."
    exit 1
fi

# ── Claude Code (.claude/commands/) ──────────────────────────────────────────
mkdir -p ".claude/commands"
cp "$WORKFLOW_FILE" ".claude/commands/agent-build.md"
echo "✅ Claude Code: .claude/commands/agent-build.md"

# ── Gemini CLI (.gemini/commands/) ───────────────────────────────────────────
mkdir -p ".gemini/commands"
if [ -f "$TOML_FILE" ]; then
    cp "$TOML_FILE" ".gemini/commands/agent-build.toml"
    echo "✅ Gemini CLI:  .gemini/commands/agent-build.toml"
else
    # Generate TOML on the fly if source doesn't exist
    cat > ".gemini/commands/agent-build.toml" <<'EOF'
description = "Auto-generate an AI agent from a natural language description, run it immediately, and refine through a feedback loop"

prompt = """
@{agent-build.md}

---

User description: {{args}}
"""
EOF
    echo "✅ Gemini CLI:  .gemini/commands/agent-build.toml (generated)"
fi

# ── Antigravity / generic (.agent/workflows/) ─────────────────────────────────
mkdir -p ".agent/workflows"
cp "$WORKFLOW_FILE" ".agent/workflows/agent-build.md"
echo "✅ Antigravity:  .agent/workflows/agent-build.md"

# ── Copy examples if they exist ───────────────────────────────────────────────
if [ -d "$SCRIPT_DIR/examples" ]; then
    AGENT_DIR="./agents"
    if [ -d ".claude/agents" ]; then
        AGENT_DIR=".claude/agents"
    elif [ -d ".agent/agents" ]; then
        AGENT_DIR=".agent/agents"
    fi

    echo ""
    read -p "📂 Copy example agents to $AGENT_DIR? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$AGENT_DIR"
        cp "$SCRIPT_DIR/examples/"*.md "$AGENT_DIR/" 2>/dev/null || true
        EXAMPLES_COPIED=$(ls "$SCRIPT_DIR/examples/"*.md 2>/dev/null | wc -l | tr -d ' ')
        echo "   ✅ Copied $EXAMPLES_COPIED example agents to $AGENT_DIR/"
    fi
fi

echo ""
echo "✅ Agent Builder installed for all supported IDEs!"
echo ""
echo "📖 Usage:"
echo "   Claude Code:  /agent-build \"mô tả agent của bạn\""
echo "   Gemini CLI:   /agent-build \"mô tả agent của bạn\""
echo "   Antigravity:  @[/agent-build] \"mô tả agent của bạn\""
echo ""
echo "📚 Examples:"
echo '   /agent-build "thu thập tiêu đề bài viết từ một trang web"'
echo '   /agent-build "review code Python và đưa ra gợi ý"'
