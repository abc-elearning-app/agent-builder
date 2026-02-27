#!/usr/bin/env bash
# new-project.sh — Create a new project in the projects/ workspace
#
# Usage: ./new-project.sh <project-name>
#
# What it does:
#   1. Creates projects/<name>/ directory
#   2. Checks out a new branch: project/<name>
#   3. Updates .gitignore to track projects/<name> on this branch
#   4. Makes an initial commit
#
# To push to GitHub when ready:
#   git push origin project/<name>

set -e

# ── Validate input ─────────────────────────────────────────────────────────────

if [[ -z "$1" ]]; then
    echo "Usage: ./new-project.sh <project-name>"
    echo "Example: ./new-project.sh invoice-parser"
    exit 1
fi

NAME="$1"
BRANCH="project/$NAME"
PROJECT_DIR="projects/$NAME"

# Validate name: lowercase, letters/numbers/hyphens only
if [[ ! "$NAME" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
    echo "Error: project name must be lowercase letters, numbers, and hyphens (e.g. my-project)"
    exit 1
fi

# ── Must be on main with clean state ──────────────────────────────────────────

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo "Error: must be on main branch (currently on '$CURRENT_BRANCH')"
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: working tree has uncommitted changes — commit or stash first"
    exit 1
fi

# ── Check branch doesn't already exist ────────────────────────────────────────

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Error: branch '$BRANCH' already exists"
    exit 1
fi

# ── Create branch and project folder ──────────────────────────────────────────

echo "Creating branch: $BRANCH"
git checkout -b "$BRANCH"

echo "Creating folder: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"

# ── Update .gitignore to track this project on this branch ────────────────────

# Replace "projects/" (main ignores all) with "projects/*\n!projects/<name>"
sed -i.bak "s|^projects/$|projects/*\n!projects/$NAME|" .gitignore && rm -f .gitignore.bak

# ── Initial commit ─────────────────────────────────────────────────────────────

touch "$PROJECT_DIR/.gitkeep"
git add .gitignore "$PROJECT_DIR/.gitkeep"
git commit -m "chore: init project/$NAME"

# ── Done ───────────────────────────────────────────────────────────────────────

echo ""
echo "✅ Project created!"
echo "   Branch  : $BRANCH"
echo "   Folder  : $PROJECT_DIR"
echo ""
echo "   Work in: $PROJECT_DIR/"
echo ""
echo "   When ready to push:"
echo "   git push origin $BRANCH"
