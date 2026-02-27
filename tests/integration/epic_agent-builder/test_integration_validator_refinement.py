"""Integration Test: Validator + refinement loop integration in builder-engine."""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")


def read_file(rel_path):
    with open(os.path.join(AB_DIR, rel_path), "r") as f:
        return f.read()


def test_engine_calls_validator():
    """builder-engine must reference validate-claude.sh."""
    content = read_file(".claude/agents/builder-engine.md")
    assert "validate-claude" in content or "validator" in content.lower(), \
        "Engine must call the validator script"


def test_engine_has_max_rounds():
    """Refinement loop must have a max round limit."""
    content = read_file(".claude/agents/builder-engine.md")
    # Look for max round references (5 is the expected max)
    has_max = bool(re.search(r"(?:max|tối đa|maximum)\s*[\=:]*\s*5", content, re.IGNORECASE))
    if not has_max:
        has_max = "5 round" in content.lower() or "5 vòng" in content.lower()
    assert has_max, "Refinement loop must have max 5 rounds"


def test_engine_has_progress_display():
    """Refinement loop must show progress (round number)."""
    content = read_file(".claude/agents/builder-engine.md")
    has_progress = "🔄" in content or "vòng" in content.lower() or "round" in content.lower()
    assert has_progress, "Refinement loop must display progress"


def test_validator_accepts_type_arg():
    """validate-claude.sh must accept type argument (command|agent)."""
    content = read_file("validators/validate-claude.sh")
    has_type = "command" in content and "agent" in content
    assert has_type, "Validator must handle both 'command' and 'agent' types"


def test_validator_checks_frontmatter():
    """validate-claude.sh must check YAML frontmatter."""
    content = read_file("validators/validate-claude.sh")
    has_frontmatter_check = "---" in content and ("frontmatter" in content.lower() or "yaml" in content.lower())
    assert has_frontmatter_check, "Validator must check frontmatter"


def test_validator_checks_description():
    """validate-claude.sh must verify description field exists."""
    content = read_file("validators/validate-claude.sh")
    assert "description" in content, "Validator must check for description field"


def test_engine_write_output_step_exists():
    """builder-engine must have a write/save output step."""
    content = read_file(".claude/agents/builder-engine.md")
    has_write = "write output" in content.lower() or "ghi đè" in content.lower() or "write" in content.lower()
    assert has_write, "Engine must have a write output step"


def test_engine_explanation_step_exists():
    """builder-engine must have a Vietnamese explanation step."""
    content = read_file(".claude/agents/builder-engine.md")
    # Check for Vietnamese explanation indicators
    has_explain = "giải thích" in content.lower() or "explanation" in content.lower()
    assert has_explain, "Engine must have an explanation step"
