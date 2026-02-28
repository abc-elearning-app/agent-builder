#!/usr/bin/env bash
# Smoke Test 05: No external dependencies
# Verifies project doesn't require pip, npm, curl, wget, etc.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GEMINI_DIR="$PROJECT_ROOT/agent-builder-gemini"

pass=0
fail=0
errors=""

echo "=== Smoke Test 05: No external dependencies ==="

# Check for dependency installation commands in all files
dep_patterns=("pip install" "npm install" "yarn add" "curl " "wget " "apt-get" "brew install")

for pattern in "${dep_patterns[@]}"; do
  matches=$(grep -r "$pattern" "$GEMINI_DIR" --include="*.sh" --include="*.toml" --include="*.md" -l 2>/dev/null || true)
  if [ -z "$matches" ]; then
    echo "✅ No '$pattern' found"
    pass=$((pass + 1))
  else
    # Check if it's in a documentation context (not actual usage)
    real_usage=false
    while IFS= read -r file; do
      # Skip test fixtures, scenarios, specs, and lessons learned (documentation)
      if echo "$file" | grep -qE "(test-fixtures|scenarios|LESSONS|specs|README)"; then
        continue
      fi
      real_usage=true
    done <<< "$matches"

    if [ "$real_usage" = true ]; then
      echo "❌ Found '$pattern' in: $matches"
      fail=$((fail + 1))
      errors="$errors\n- Found dependency: $pattern"
    else
      echo "✅ No '$pattern' in production files (only in docs)"
      pass=$((pass + 1))
    fi
  fi
done

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
