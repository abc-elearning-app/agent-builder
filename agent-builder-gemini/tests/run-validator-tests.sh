#!/usr/bin/env bash
# Run all validator test fixtures
# Exit 0 = all pass, Exit 1 = some fail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../validators/validate-gemini.sh"
FIXTURES="$SCRIPT_DIR/test-fixtures"

pass=0; fail=0; total=0

# Test valid fixtures (should exit 0)
for f in "$FIXTURES/valid/"*; do
  [ -f "$f" ] || continue
  total=$((total+1))
  name=$(basename "$f")
  if bash "$VALIDATOR" "$f" >/dev/null 2>&1; then
    echo "  ✅ PASS (valid): $name"
    pass=$((pass+1))
  else
    echo "  ❌ FAIL (valid): $name — expected PASS but got FAIL"
    bash "$VALIDATOR" "$f" 2>&1 | head -5
    fail=$((fail+1))
  fi
done

# Test invalid fixtures (should exit 1)
for f in "$FIXTURES/invalid/"*; do
  [ -f "$f" ] || continue
  total=$((total+1))
  name=$(basename "$f")
  if bash "$VALIDATOR" "$f" >/dev/null 2>&1; then
    echo "  ❌ FAIL (invalid): $name — expected FAIL but got PASS"
    fail=$((fail+1))
  else
    echo "  ✅ PASS (invalid): $name"
    pass=$((pass+1))
  fi
done

echo ""
echo "Results: $pass/$total passed, $fail failed"
[ "$fail" -eq 0 ] && exit 0 || exit 1
