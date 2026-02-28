#!/usr/bin/env bash
# Smoke Test 03: Run validator test fixtures
# Verifies all test fixtures produce expected results
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEST_RUNNER="$PROJECT_ROOT/agent-builder-gemini/tests/run-validator-tests.sh"

echo "=== Smoke Test 03: Validator test fixtures ==="

# Test 1: Test runner exists
if [ -f "$TEST_RUNNER" ]; then
  echo "✅ Test runner exists"
else
  echo "❌ Test runner not found: $TEST_RUNNER"
  exit 1
fi

# Test 2: Run all fixtures
output=$(bash "$TEST_RUNNER" 2>&1)
echo "$output"

# Test 3: Check for failures
if echo "$output" | grep -q "FAIL"; then
  echo ""
  echo "❌ Some test fixtures failed"
  exit 1
else
  echo ""
  echo "✅ All test fixtures passed"
  exit 0
fi
