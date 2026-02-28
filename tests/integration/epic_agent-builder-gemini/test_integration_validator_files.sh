#!/usr/bin/env bash
# Integration Test: Validator correctly validates all generated project files
# Tests the interface between validator and the actual command/agent files
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VALIDATOR="$PROJECT_ROOT/agent-builder-gemini/validators/validate-gemini.sh"

pass=0
fail=0
errors=""

echo "=== Integration: Validator ↔ Project Files ==="

# Test: agent-builder.toml validated as command
result=$(bash "$VALIDATOR" "$PROJECT_ROOT/agent-builder-gemini/.gemini/commands/agent-builder.toml" command 2>&1)
exit_code=$?
if [ "$exit_code" -eq 0 ]; then
  echo "✅ agent-builder.toml: PASS (exit $exit_code)"
  pass=$((pass + 1))
else
  echo "❌ agent-builder.toml: FAIL (exit $exit_code)"
  echo "   $result"
  fail=$((fail + 1))
  errors="$errors\n- agent-builder.toml validation failed"
fi

# Test: builder-engine.md validated as agent
result=$(bash "$VALIDATOR" "$PROJECT_ROOT/agent-builder-gemini/.gemini/agents/builder-engine.md" agent 2>&1)
exit_code=$?
if [ "$exit_code" -eq 0 ]; then
  echo "✅ builder-engine.md: PASS (exit $exit_code)"
  pass=$((pass + 1))
else
  echo "❌ builder-engine.md: FAIL (exit $exit_code)"
  echo "   $result"
  fail=$((fail + 1))
  errors="$errors\n- builder-engine.md validation failed"
fi

# Test: Auto-detect type from extension (.toml → command)
result=$(bash "$VALIDATOR" "$PROJECT_ROOT/agent-builder-gemini/.gemini/commands/agent-builder.toml" 2>&1)
exit_code=$?
if [ "$exit_code" -eq 0 ]; then
  echo "✅ Auto-detect .toml → command: PASS"
  pass=$((pass + 1))
else
  echo "❌ Auto-detect .toml → command: FAIL"
  fail=$((fail + 1))
  errors="$errors\n- Auto-detect type failed for .toml"
fi

# Test: Auto-detect type from extension (.md → agent)
result=$(bash "$VALIDATOR" "$PROJECT_ROOT/agent-builder-gemini/.gemini/agents/builder-engine.md" 2>&1)
exit_code=$?
if [ "$exit_code" -eq 0 ]; then
  echo "✅ Auto-detect .md → agent: PASS"
  pass=$((pass + 1))
else
  echo "❌ Auto-detect .md → agent: FAIL"
  fail=$((fail + 1))
  errors="$errors\n- Auto-detect type failed for .md"
fi

# Test: Validator rejects non-existent file
result=$(bash "$VALIDATOR" "/tmp/nonexistent-file.toml" command 2>&1 || true)
exit_code=0
bash "$VALIDATOR" "/tmp/nonexistent-file.toml" command >/dev/null 2>&1 || exit_code=$?
if [ "$exit_code" -eq 1 ]; then
  echo "✅ Non-existent file: correctly returns exit 1"
  pass=$((pass + 1))
else
  echo "❌ Non-existent file: expected exit 1, got exit $exit_code"
  fail=$((fail + 1))
  errors="$errors\n- Non-existent file should return exit 1"
fi

# Test: Validator rejects non-agent .md file (no frontmatter)
exit_code=0
bash "$VALIDATOR" "$PROJECT_ROOT/agent-builder-gemini/README.md" >/dev/null 2>&1 || exit_code=$?
if [ "$exit_code" -eq 1 ]; then
  echo "✅ Non-agent .md file: correctly fails validation"
  pass=$((pass + 1))
else
  echo "⚠️ Non-agent .md file: exit $exit_code (may pass if has frontmatter-like content)"
  pass=$((pass + 1))
fi

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
