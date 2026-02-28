#!/usr/bin/env bash
# Smoke Test 02: Install script works in fresh directory
# Verifies install.sh copies all files to correct locations
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

echo "=== Smoke Test 02: Install in fresh directory ==="

# Test 1: Install script exists and is executable
if [ -x "$INSTALL_SCRIPT" ]; then
  echo "✅ install.sh is executable"
  pass=$((pass + 1))
else
  echo "❌ install.sh not executable"
  fail=$((fail + 1))
  errors="$errors\n- install.sh not executable"
fi

# Test 2: Run install in temp directory
cd "$TEMP_DIR"
install_output=$(bash "$INSTALL_SCRIPT" --force 2>&1) || true
if echo "$install_output" | grep -qi "install\|success\|complete"; then
  echo "✅ install.sh ran successfully"
  pass=$((pass + 1))
else
  echo "❌ install.sh failed"
  echo "   Output: $install_output"
  fail=$((fail + 1))
  errors="$errors\n- install.sh failed to run"
fi

# Test 3: Check core files installed
expected_files=(
  ".gemini/commands/agent-builder.toml"
  ".gemini/agents/builder-engine.md"
)
for f in "${expected_files[@]}"; do
  if [ -f "$TEMP_DIR/$f" ]; then
    echo "✅ Installed: $f"
    pass=$((pass + 1))
  else
    echo "❌ Missing: $f"
    fail=$((fail + 1))
    errors="$errors\n- Missing: $f"
  fi
done

# Test 4: Validator has execute permission after install
INSTALLED_VALIDATOR=$(find "$TEMP_DIR" -name "validate-gemini.sh" 2>/dev/null | head -1)
if [ -n "$INSTALLED_VALIDATOR" ] && [ -x "$INSTALLED_VALIDATOR" ]; then
  echo "✅ Installed validator is executable"
  pass=$((pass + 1))
else
  echo "❌ Installed validator not executable or not found"
  fail=$((fail + 1))
  errors="$errors\n- Validator not executable after install"
fi

# Test 5: Count total installed files (expect >= 7)
file_count=$(find "$TEMP_DIR" -type f | wc -l | tr -d ' ')
if [ "$file_count" -ge 7 ]; then
  echo "✅ File count: $file_count (>= 7)"
  pass=$((pass + 1))
else
  echo "❌ File count: $file_count (expected >= 7)"
  fail=$((fail + 1))
  errors="$errors\n- Only $file_count files installed (expected >= 7)"
fi

cd "$PROJECT_ROOT"

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
