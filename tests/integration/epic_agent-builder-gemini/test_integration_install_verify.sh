#!/usr/bin/env bash
# Integration Test: Install then validate installed files
# Tests the interface between install.sh and validate-gemini.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
INSTALL_SCRIPT="$PROJECT_ROOT/agent-builder-gemini/install.sh"
TEMP_DIR=$(mktemp -d)

pass=0
fail=0
errors=""

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=== Integration: Install → Validate ==="

# Step 1: Install to temp directory
cd "$TEMP_DIR"
bash "$INSTALL_SCRIPT" --force 2>&1 > /dev/null

# Step 2: Find installed validator
INSTALLED_VALIDATOR=$(find "$TEMP_DIR" -name "validate-gemini.sh" -type f 2>/dev/null | head -1)
if [ -z "$INSTALLED_VALIDATOR" ]; then
  echo "❌ Validator not found after install"
  exit 1
fi

# Step 3: Validate installed command with installed validator
INSTALLED_CMD=$(find "$TEMP_DIR" -name "agent-builder.toml" -type f 2>/dev/null | head -1)
if [ -n "$INSTALLED_CMD" ]; then
  result=$(bash "$INSTALLED_VALIDATOR" "$INSTALLED_CMD" command 2>&1)
  exit_code=$?
  if [ "$exit_code" -eq 0 ]; then
    echo "✅ Installed command validates with installed validator"
    pass=$((pass + 1))
  else
    echo "❌ Installed command fails installed validator"
    echo "   $result"
    fail=$((fail + 1))
    errors="$errors\n- Installed command fails validation"
  fi
else
  echo "❌ agent-builder.toml not found after install"
  fail=$((fail + 1))
  errors="$errors\n- Command not installed"
fi

# Step 4: Validate installed agent with installed validator
INSTALLED_AGENT=$(find "$TEMP_DIR" -name "builder-engine.md" -type f 2>/dev/null | head -1)
if [ -n "$INSTALLED_AGENT" ]; then
  result=$(bash "$INSTALLED_VALIDATOR" "$INSTALLED_AGENT" agent 2>&1)
  exit_code=$?
  if [ "$exit_code" -eq 0 ]; then
    echo "✅ Installed agent validates with installed validator"
    pass=$((pass + 1))
  else
    echo "❌ Installed agent fails installed validator"
    echo "   $result"
    fail=$((fail + 1))
    errors="$errors\n- Installed agent fails validation"
  fi
else
  echo "❌ builder-engine.md not found after install"
  fail=$((fail + 1))
  errors="$errors\n- Agent not installed"
fi

# Step 5: Verify specs installed alongside
specs_count=$(find "$TEMP_DIR" -path "*/specs/*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$specs_count" -ge 2 ]; then
  echo "✅ Specs installed: $specs_count files"
  pass=$((pass + 1))
else
  echo "❌ Specs missing: found $specs_count (expected >= 2)"
  fail=$((fail + 1))
  errors="$errors\n- Specs not fully installed"
fi

# Step 6: Verify templates installed
templates_count=$(find "$TEMP_DIR" -path "*/templates/*" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$templates_count" -ge 2 ]; then
  echo "✅ Templates installed: $templates_count files"
  pass=$((pass + 1))
else
  echo "❌ Templates missing: found $templates_count (expected >= 2)"
  fail=$((fail + 1))
  errors="$errors\n- Templates not fully installed"
fi

cd "$PROJECT_ROOT"

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
