"""Smoke Test 01: All deliverable files exist and are non-empty."""
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AB_DIR = os.path.join(PROJECT_ROOT, "agent-builder-claude")


REQUIRED_FILES = [
    ".claude/commands/agent-builder.md",
    ".claude/agents/builder-engine.md",
    "templates/slash-command.md",
    "templates/subagent.md",
    "specs/command-spec.md",
    "specs/agent-spec.md",
    "validators/validate-claude.sh",
    "install.sh",
    "README.md",
    "LESSONS_LEARNED.md",
    "tests/scenarios.md",
    "tests/results.md",
    "tests/run-validator-tests.sh",
]


def test_all_deliverable_files_exist():
    """Every required deliverable file must exist."""
    missing = []
    for f in REQUIRED_FILES:
        path = os.path.join(AB_DIR, f)
        if not os.path.isfile(path):
            missing.append(f)
    assert missing == [], f"Missing files: {missing}"


def test_all_deliverable_files_non_empty():
    """Every required deliverable file must be non-empty."""
    empty = []
    for f in REQUIRED_FILES:
        path = os.path.join(AB_DIR, f)
        if os.path.isfile(path) and os.path.getsize(path) == 0:
            empty.append(f)
    assert empty == [], f"Empty files: {empty}"


def test_test_fixtures_directory_has_10_files():
    """Test fixtures directory must have exactly 10 fixture files."""
    fixtures_dir = os.path.join(AB_DIR, "tests", "test-fixtures")
    assert os.path.isdir(fixtures_dir), "test-fixtures directory missing"
    fixtures = [f for f in os.listdir(fixtures_dir) if f.endswith(".md")]
    assert len(fixtures) == 10, f"Expected 10 fixtures, found {len(fixtures)}: {fixtures}"


def test_bash_scripts_are_executable():
    """All .sh files must have execute permission."""
    scripts = [
        "validators/validate-claude.sh",
        "install.sh",
        "tests/run-validator-tests.sh",
    ]
    non_exec = []
    for s in scripts:
        path = os.path.join(AB_DIR, s)
        if os.path.isfile(path) and not os.access(path, os.X_OK):
            non_exec.append(s)
    assert non_exec == [], f"Scripts not executable: {non_exec}"


def test_no_absolute_paths_in_deliverables():
    """No /Users/ or /home/ absolute paths in any deliverable."""
    result = subprocess.run(
        ["grep", "-r", "/Users/", AB_DIR],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, f"Found /Users/ paths:\n{result.stdout}"

    result2 = subprocess.run(
        ["grep", "-r", "/home/", AB_DIR],
        capture_output=True, text=True,
    )
    assert result2.returncode != 0, f"Found /home/ paths:\n{result2.stdout}"


def test_no_external_dependencies():
    """No package.json or requirements.txt in deliverable."""
    assert not os.path.isfile(os.path.join(AB_DIR, "package.json")), "package.json found"
    assert not os.path.isfile(os.path.join(AB_DIR, "requirements.txt")), "requirements.txt found"
