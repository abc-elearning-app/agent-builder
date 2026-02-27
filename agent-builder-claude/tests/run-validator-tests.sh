#!/usr/bin/env bash
# run-validator-tests.sh — Automated validator tests against test fixtures
# Usage: bash run-validator-tests.sh
# Runs validate-claude.sh against all fixtures in test-fixtures/ and reports results.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../validators/validate-claude.sh"
FIXTURES="$SCRIPT_DIR/test-fixtures"

pass=0
fail=0
errors=""

run_test() {
  local name="$1"
  local file="$2"
  local type="$3"
  local expect_pass="$4"

  output=$("$VALIDATOR" "$file" "$type" 2>&1) || true
  exit_code=$?
  # Re-run to get actual exit code (set -e may interfere)
  "$VALIDATOR" "$file" "$type" > /dev/null 2>&1 && exit_code=0 || exit_code=1

  if [ "$expect_pass" = "true" ] && [ "$exit_code" -eq 0 ]; then
    echo "  ✅ $name — PASS (expected PASS)"
    pass=$((pass + 1))
  elif [ "$expect_pass" = "false" ] && [ "$exit_code" -eq 1 ]; then
    echo "  ✅ $name — FAIL (expected FAIL)"
    pass=$((pass + 1))
  else
    if [ "$expect_pass" = "true" ]; then
      echo "  ❌ $name — FAIL (expected PASS)"
      errors="$errors\n  - $name: expected PASS but got FAIL\n    Output: $output"
    else
      echo "  ❌ $name — PASS (expected FAIL)"
      errors="$errors\n  - $name: expected FAIL but got PASS"
    fi
    fail=$((fail + 1))
  fi
}

echo "🧪 Running validator tests..."
echo ""

echo "Valid fixtures (should PASS):"
run_test "valid-command"          "$FIXTURES/valid-command.md"          "command" "true"
run_test "valid-agent"            "$FIXTURES/valid-agent.md"            "agent"   "true"
run_test "valid-command-args"     "$FIXTURES/valid-command-args.md"     "command" "true"
run_test "valid-agent-multi-tool" "$FIXTURES/valid-agent-multi-tool.md" "agent"   "true"
run_test "valid-command-no-hint"  "$FIXTURES/valid-command-no-hint.md"  "command" "true"
echo ""

echo "Invalid fixtures (should FAIL):"
run_test "invalid-no-frontmatter" "$FIXTURES/invalid-no-frontmatter.md" "command" "false"
run_test "invalid-missing-desc"   "$FIXTURES/invalid-missing-desc.md"   "command" "false"
run_test "invalid-tabs"           "$FIXTURES/invalid-tabs.md"           "command" "false"
run_test "invalid-bad-tools"      "$FIXTURES/invalid-bad-tools.md"      "command" "false"
run_test "invalid-agent-no-name"  "$FIXTURES/invalid-agent-no-name.md"  "agent"   "false"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
total=$((pass + fail))
echo "Results: $pass/$total passed"

if [ "$fail" -gt 0 ]; then
  echo ""
  echo "Failures:"
  printf "$errors\n"
  echo ""
  echo "RESULT: FAIL"
  exit 1
else
  echo "RESULT: ALL PASS"
  exit 0
fi
