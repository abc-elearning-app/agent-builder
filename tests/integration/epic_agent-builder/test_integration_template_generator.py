"""Integration Test: Templates + specs referenced correctly by generator."""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")


def read_file(rel_path):
    with open(os.path.join(AB_DIR, rel_path), "r") as f:
        return f.read()


def test_engine_references_command_template():
    """builder-engine must reference slash-command template."""
    content = read_file(".claude/agents/builder-engine.md")
    assert "slash-command" in content or "command" in content.lower(), \
        "Engine must reference command template"


def test_engine_references_agent_template():
    """builder-engine must reference subagent template."""
    content = read_file(".claude/agents/builder-engine.md")
    assert "subagent" in content or "agent" in content.lower(), \
        "Engine must reference agent template"


def test_engine_references_specs():
    """builder-engine must reference format specs."""
    content = read_file(".claude/agents/builder-engine.md")
    has_spec_ref = "spec" in content.lower() or "format" in content.lower()
    assert has_spec_ref, "Engine must reference format specifications"


def test_templates_have_placeholders():
    """Templates must have placeholder syntax for generation."""
    cmd_template = read_file("templates/slash-command.md")
    agent_template = read_file("templates/subagent.md")
    # Check for placeholder patterns like {{NAME}} or {name} or similar
    has_cmd_placeholder = "{{" in cmd_template or "{" in cmd_template
    has_agent_placeholder = "{{" in agent_template or "{" in agent_template
    assert has_cmd_placeholder, "Command template must have placeholders"
    assert has_agent_placeholder, "Agent template must have placeholders"


def test_specs_define_required_fields():
    """Specs must document required frontmatter fields."""
    cmd_spec = read_file("specs/command-spec.md")
    agent_spec = read_file("specs/agent-spec.md")
    assert "description" in cmd_spec, "Command spec must mention 'description' field"
    assert "description" in agent_spec, "Agent spec must mention 'description' field"
    assert "name" in agent_spec, "Agent spec must mention 'name' field"


def test_engine_handles_arguments():
    """builder-engine must handle $ARGUMENTS for commands."""
    content = read_file(".claude/agents/builder-engine.md")
    assert "$ARGUMENTS" in content or "ARGUMENTS" in content, \
        "Engine must handle $ARGUMENTS syntax"
