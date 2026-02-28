"""Integration Test: Discovery command → builder-engine delegation."""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")


def read_file(rel_path):
    with open(os.path.join(AB_DIR, rel_path), "r") as f:
        return f.read()


def test_discovery_delegates_to_builder_engine():
    """agent-builder.md must reference builder-engine as subagent."""
    content = read_file(".claude/commands/agent-builder.md")
    assert "builder-engine" in content, "Discovery command must delegate to builder-engine"


def test_discovery_uses_task_tool():
    """agent-builder.md must use Task tool to launch builder-engine."""
    content = read_file(".claude/commands/agent-builder.md")
    assert "Task" in content, "Discovery command must use Task tool for delegation"


def test_builder_engine_has_generation_steps():
    """builder-engine.md must have structured generation steps."""
    content = read_file(".claude/agents/builder-engine.md")
    # Check for numbered steps
    steps = re.findall(r"(?:Step|Bước)\s+\d", content, re.IGNORECASE)
    assert len(steps) >= 3, f"Expected at least 3 steps, found {len(steps)}"


def test_discovery_detects_command_vs_agent():
    """agent-builder.md must have type detection logic."""
    content = read_file(".claude/commands/agent-builder.md")
    has_command = "command" in content.lower()
    has_agent = "agent" in content.lower()
    assert has_command and has_agent, "Must distinguish between command and agent types"


def test_discovery_has_vietnamese_interaction():
    """agent-builder.md must contain Vietnamese text for user interaction."""
    content = read_file(".claude/commands/agent-builder.md")
    # Check for Vietnamese-specific characters
    vietnamese_chars = any(c in content for c in "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệ")
    assert vietnamese_chars, "Discovery command must contain Vietnamese text"
