"""Smoke Test 02: Validator works on valid and invalid fixtures."""
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")
VALIDATOR = os.path.join(AB_DIR, "validators", "validate-claude.sh")
FIXTURES_DIR = os.path.join(AB_DIR, "tests", "test-fixtures")


def run_validator(fixture_name, file_type):
    """Run validator on a fixture and return exit code."""
    fixture_path = os.path.join(FIXTURES_DIR, fixture_name)
    result = subprocess.run(
        ["bash", VALIDATOR, fixture_path, file_type],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_valid_command_passes():
    code, stdout, _ = run_validator("valid-command.md", "command")
    assert code == 0, f"valid-command.md should pass. Output: {stdout}"


def test_valid_agent_passes():
    code, stdout, _ = run_validator("valid-agent.md", "agent")
    assert code == 0, f"valid-agent.md should pass. Output: {stdout}"


def test_valid_command_with_args_passes():
    code, stdout, _ = run_validator("valid-command-args.md", "command")
    assert code == 0, f"valid-command-args.md should pass. Output: {stdout}"


def test_valid_agent_multi_tool_passes():
    code, stdout, _ = run_validator("valid-agent-multi-tool.md", "agent")
    assert code == 0, f"valid-agent-multi-tool.md should pass. Output: {stdout}"


def test_valid_command_no_hint_passes():
    code, stdout, _ = run_validator("valid-command-no-hint.md", "command")
    assert code == 0, f"valid-command-no-hint.md should pass. Output: {stdout}"


def test_invalid_no_frontmatter_fails():
    code, stdout, _ = run_validator("invalid-no-frontmatter.md", "command")
    assert code == 1, f"invalid-no-frontmatter.md should fail. Output: {stdout}"


def test_invalid_missing_desc_fails():
    code, stdout, _ = run_validator("invalid-missing-desc.md", "command")
    assert code == 1, f"invalid-missing-desc.md should fail. Output: {stdout}"


def test_invalid_tabs_fails():
    code, stdout, _ = run_validator("invalid-tabs.md", "command")
    assert code == 1, f"invalid-tabs.md should fail. Output: {stdout}"


def test_invalid_bad_tools_fails():
    code, stdout, _ = run_validator("invalid-bad-tools.md", "command")
    assert code == 1, f"invalid-bad-tools.md should fail. Output: {stdout}"


def test_invalid_agent_no_name_fails():
    code, stdout, _ = run_validator("invalid-agent-no-name.md", "agent")
    assert code == 1, f"invalid-agent-no-name.md should fail. Output: {stdout}"
