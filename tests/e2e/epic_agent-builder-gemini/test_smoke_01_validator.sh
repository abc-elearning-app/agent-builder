#!/usr/bin/env bash
# Smoke Test 01: Validator runs on all project TOML files
# Verifies validate-gemini.sh works correctly on project's own files
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VALIDATOR="$PROJECT_ROOT/agent-builder-gemini/validators/validate-gemini.sh"

pass=0
fail=0
errors=""

echo "=== Smoke Test 01: Validator on project TOML files ==="

# Test 1: Validator script exists and is executable
if [ -x "$VALIDATOR" ]; then
  echo "✅ Validator is executable"
  pass=$((pass + 1))
else
  echo "❌ Validator not executable: $VALIDATOR"
  fail=$((fail + 1))
  errors="$errors\n- Validator not executable"
fi

# Test 2: Validate agent-builder.toml (command)
TOML_FILE="$PROJECT_ROOT/agent-builder-gemini/.gemini/commands/agent-builder.toml"
if bash "$VALIDATOR" "$TOML_FILE" command 2>&1 | grep -q "PASS"; then
  echo "✅ agent-builder.toml passes validation"
  pass=$((pass + 1))
else
  echo "❌ agent-builder.toml fails validation"
  bash "$VALIDATOR" "$TOML_FILE" command 2>&1 || true
  fail=$((fail + 1))
  errors="$errors\n- agent-builder.toml fails validation"
fi

# Test 3: Validate builder-engine.md (agent)
AGENT_FILE="$PROJECT_ROOT/agent-builder-gemini/.gemini/agents/builder-engine.md"
if bash "$VALIDATOR" "$AGENT_FILE" agent 2>&1 | grep -q "PASS"; then
  echo "✅ builder-engine.md passes validation"
  pass=$((pass + 1))
else
  echo "❌ builder-engine.md fails validation"
  bash "$VALIDATOR" "$AGENT_FILE" agent 2>&1 || true
  fail=$((fail + 1))
  errors="$errors\n- builder-engine.md fails validation"
fi

# Test 4: Validate custom-command.toml template (should fail — has placeholders)
TEMPLATE="$PROJECT_ROOT/agent-builder-gemini/templates/custom-command.toml"
if bash "$VALIDATOR" "$TEMPLATE" command 2>&1 | grep -q "PASS\|FAIL"; then
  echo "✅ Template validation runs without crash"
  pass=$((pass + 1))
else
  echo "❌ Template validation crashed"
  fail=$((fail + 1))
  errors="$errors\n- Template validation crashed"
fi

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
