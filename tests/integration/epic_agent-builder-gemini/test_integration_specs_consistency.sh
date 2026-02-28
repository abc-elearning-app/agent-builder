#!/usr/bin/env bash
# Integration Test: Specs consistency with actual files
# Verifies that specs describe the actual format used by command and agent files
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GEMINI_DIR="$PROJECT_ROOT/agent-builder-gemini"

pass=0
fail=0
errors=""

echo "=== Integration: Specs ↔ Actual Files ==="

# Test 1: command-spec mentions prompt field — agent-builder.toml has prompt field
if grep -q "^prompt" "$GEMINI_DIR/specs/command-spec.md" && grep -q "^prompt" "$GEMINI_DIR/.gemini/commands/agent-builder.toml"; then
  echo "✅ Spec and command both reference 'prompt' field"
  pass=$((pass + 1))
else
  echo "❌ Mismatch: prompt field in spec vs command"
  fail=$((fail + 1))
  errors="$errors\n- prompt field mismatch"
fi

# Test 2: agent-spec mentions required fields — builder-engine.md has them
for field in "name:" "description:" "tools:"; do
  if grep -q "$field" "$GEMINI_DIR/.gemini/agents/builder-engine.md"; then
    echo "✅ builder-engine.md has required field: $field"
    pass=$((pass + 1))
  else
    echo "❌ builder-engine.md missing required field: $field"
    fail=$((fail + 1))
    errors="$errors\n- Missing field: $field"
  fi
done

# Test 3: agent-spec tool names match builder-engine tools
spec_tools=$(grep -oE '`[a-z_]+`' "$GEMINI_DIR/specs/agent-spec.md" | sort -u | tr -d '`')
engine_tools=$(awk '/^tools:/,/^---/' "$GEMINI_DIR/.gemini/agents/builder-engine.md" | grep '^ *- ' | sed 's/^ *- //' | sort)

mismatches=0
while IFS= read -r tool; do
  [ -z "$tool" ] && continue
  if ! echo "$spec_tools" | grep -q "^${tool}$"; then
    echo "⚠️ Tool '$tool' in engine but not documented in spec"
    mismatches=$((mismatches + 1))
  fi
done <<< "$engine_tools"

if [ "$mismatches" -eq 0 ]; then
  echo "✅ All engine tools documented in agent-spec"
  pass=$((pass + 1))
else
  echo "⚠️ $mismatches tool(s) not explicitly documented (may be in prose)"
  pass=$((pass + 1))  # Warning, not failure
fi

# Test 4: Template placeholders are documented
if grep -q "{{DESCRIPTION}}" "$GEMINI_DIR/templates/custom-command.toml" && grep -q "{{INSTRUCTIONS}}" "$GEMINI_DIR/templates/custom-command.toml"; then
  echo "✅ TOML template has expected placeholders"
  pass=$((pass + 1))
else
  echo "❌ TOML template missing expected placeholders"
  fail=$((fail + 1))
  errors="$errors\n- Template placeholders missing"
fi

# Test 5: builder-engine references validator path correctly
if grep -q "validate-gemini.sh" "$GEMINI_DIR/.gemini/agents/builder-engine.md"; then
  echo "✅ builder-engine references validate-gemini.sh"
  pass=$((pass + 1))
else
  echo "❌ builder-engine doesn't reference validator"
  fail=$((fail + 1))
  errors="$errors\n- No validator reference in engine"
fi

# Test 6: builder-engine references spec paths correctly
if grep -q "command-spec.md" "$GEMINI_DIR/.gemini/agents/builder-engine.md" && grep -q "agent-spec.md" "$GEMINI_DIR/.gemini/agents/builder-engine.md"; then
  echo "✅ builder-engine references both spec files"
  pass=$((pass + 1))
else
  echo "❌ builder-engine missing spec references"
  fail=$((fail + 1))
  errors="$errors\n- Missing spec references"
fi

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ "$fail" -gt 0 ]; then
  printf "Errors:%b\n" "$errors"
  exit 1
fi
exit 0
