#!/usr/bin/env bash
# Smoke Test 04: All shell scripts pass syntax check
# Verifies no syntax errors in any .sh file
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GEMINI_DIR="$PROJECT_ROOT/agent-builder-gemini"

pass=0
fail=0
errors=""

echo "=== Smoke Test 04: Shell script syntax check ==="

while IFS= read -r script; do
  if bash -n "$script" 2>/dev/null; then
    echo "✅ $(basename "$script")"
    pass=$((pass + 1))
  else
    echo "❌ $(basename "$script")"
    bash -n "$script" 2>&1 || true
    fail=$((fail + 1))
    errors="$errors\n- Syntax error: $script"
  fi
done < <(find "$GEMINI_DIR" -name "*.sh" -type f)

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
