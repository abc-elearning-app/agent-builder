#!/bin/bash
# Agent Factory — Install Script
# Copy agent-factory workflow vào project hiện tại

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_FILE="$SCRIPT_DIR/agent-factory.md"
SHARED_WORKFLOW_FILE="$SCRIPT_DIR/agent-shared.md"
TOML_FILE="$SCRIPT_DIR/.gemini/commands/agent-factory.toml"

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ agent-factory.md not found at $SCRIPT_DIR"
    echo "   Make sure you're running this script from the agent-factory directory."
    exit 1
fi

# ── Claude Code (.claude/commands/) ──────────────────────────────────────────
mkdir -p ".claude/commands"
cp "$WORKFLOW_FILE" ".claude/commands/agent-factory.md"
echo "✅ Claude Code: .claude/commands/agent-factory.md"
if [ -f "$SHARED_WORKFLOW_FILE" ]; then
    cp "$SHARED_WORKFLOW_FILE" ".claude/commands/agent-shared.md"
    echo "✅ Claude Code: .claude/commands/agent-shared.md"
fi

# ── Gemini CLI (.gemini/commands/) ───────────────────────────────────────────
mkdir -p ".gemini/commands"
cp "$WORKFLOW_FILE" ".gemini/commands/agent-factory.md"
if [ -f "$SHARED_WORKFLOW_FILE" ]; then
    cp "$SHARED_WORKFLOW_FILE" ".gemini/commands/agent-shared.md"
    echo "✅ Gemini CLI:  .gemini/commands/agent-shared.md"
fi
if [ -f "$TOML_FILE" ]; then
    cp "$TOML_FILE" ".gemini/commands/agent-factory.toml"
    echo "✅ Gemini CLI:  .gemini/commands/agent-factory.toml"
else
    # Generate TOML on the fly if source doesn't exist
    cat > ".gemini/commands/agent-factory.toml" <<'EOF'
description = "Auto-generate an AI agent from a natural language description, run it immediately, and refine through a feedback loop"

prompt = """
@{agent-factory.md}

---

User description: {{args}}
"""
EOF
    echo "✅ Gemini CLI:  .gemini/commands/agent-factory.toml (generated)"
fi

# ── Antigravity / generic (.agent/workflows/) ─────────────────────────────────
mkdir -p ".agent/workflows"
cp "$WORKFLOW_FILE" ".agent/workflows/agent-factory.md"
echo "✅ Antigravity:  .agent/workflows/agent-factory.md"
if [ -f "$SHARED_WORKFLOW_FILE" ]; then
    cp "$SHARED_WORKFLOW_FILE" ".agent/workflows/agent-shared.md"
    echo "✅ Antigravity:  .agent/workflows/agent-shared.md"
fi

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
echo "✅ Agent Factory installed for all supported IDEs!"
echo ""
echo "📖 Usage:"
echo "   Claude Code:  /agent-factory \"mô tả agent của bạn\""
echo "   Gemini CLI:   /agent-factory \"mô tả agent của bạn\""
echo "   Antigravity:  @[/agent-factory] \"mô tả agent của bạn\""
echo ""
echo "📚 Examples:"
echo '   /agent-factory "thu thập tiêu đề bài viết từ một trang web"'
echo '   /agent-factory "review code Python và đưa ra gợi ý"'
echo ""
echo "🏪 Browse shared agents:"
echo "   /agent-shared"
