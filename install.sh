#!/bin/bash
# Agent Builder — Install Script
# Copy agent-build workflow vào project hiện tại

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_FILE="$SCRIPT_DIR/agent-build.md"

# Detect target directory
if [ -d ".agent/workflows" ]; then
    TARGET_DIR=".agent/workflows"
elif [ -d ".claude/commands" ]; then
    TARGET_DIR=".claude/commands"
else
    TARGET_DIR=".agent/workflows"
fi

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ agent-build.md not found at $SCRIPT_DIR"
    echo "   Make sure you're running this script from the agent-builder directory."
    exit 1
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# Copy workflow
cp "$WORKFLOW_FILE" "$TARGET_DIR/agent-build.md"

# Copy examples if they exist
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
echo "✅ Agent Builder installed!"
echo "   Workflow: $TARGET_DIR/agent-build.md"
echo ""
echo "📖 Usage:"
echo '   @[/agent-build] "mô tả agent của bạn"'
echo ""
echo "📚 Examples:"
echo '   @[/agent-build] "thu thập tiêu đề bài viết từ một trang web"'
echo '   @[/agent-build] "review code Python và đưa ra gợi ý"'
