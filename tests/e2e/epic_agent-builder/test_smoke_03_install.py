"""Smoke Test 03: install.sh works on a fresh empty project."""
import os
import subprocess
import tempfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")
INSTALL_SH = os.path.join(AB_DIR, "install.sh")


def test_install_creates_command_file():
    """install.sh should create .claude/commands/agent-builder.md in target."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["bash", INSTALL_SH, tmpdir, "--force"],
            capture_output=True, text=True,
        )
        cmd_file = os.path.join(tmpdir, ".claude", "commands", "agent-builder.md")
        assert os.path.isfile(cmd_file), (
            f"Command file not created at .claude/commands/agent-builder.md\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def test_install_creates_agent_file():
    """install.sh should create .claude/agents/builder-engine.md in target."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["bash", INSTALL_SH, tmpdir, "--force"],
            capture_output=True, text=True,
        )
        agent_file = os.path.join(tmpdir, ".claude", "agents", "builder-engine.md")
        assert os.path.isfile(agent_file), (
            f"Agent file not created at .claude/agents/builder-engine.md\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def test_install_creates_supporting_files():
    """install.sh should copy templates, specs, and validator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["bash", INSTALL_SH, tmpdir, "--force"],
            capture_output=True, text=True,
        )
        expected = [
            "templates/slash-command.md",
            "templates/subagent.md",
            "specs/command-spec.md",
            "specs/agent-spec.md",
            "validators/validate-claude.sh",
        ]
        missing = []
        for f in expected:
            if not os.path.isfile(os.path.join(tmpdir, f)):
                missing.append(f)
        assert missing == [], (
            f"Missing supporting files: {missing}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


def test_install_exit_code_zero():
    """install.sh should exit 0 on success."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["bash", INSTALL_SH, tmpdir, "--force"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, (
            f"install.sh exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
