#!/usr/bin/env bash
# validate-claude.sh — Structural validator for Claude Code commands and agents
# Usage: validate-claude.sh <file_path> <type>
#   type: "command" or "agent"
#   Exit 0 = valid, Exit 1 = invalid
# Output: structured error messages (one per line, AI-parseable)

set -euo pipefail

# --- Known valid tools ---
VALID_TOOLS="Read Write Edit Bash Glob Grep Task WebFetch WebSearch NotebookEdit LS Search MultiEdit Agent TodoWrite BashOutput KillBash"

# --- Helpers ---
error_count=0
warn_count=0

report_error() {
  echo "ERROR: $1"
  error_count=$((error_count + 1))
}

report_warn() {
  echo "WARN: $1"
  warn_count=$((warn_count + 1))
}

# --- Args ---
if [ $# -lt 2 ]; then
  echo "Usage: validate-claude.sh <file_path> <type>"
  echo "  type: command | agent"
  exit 2
fi

FILE="$1"
TYPE="$2"

if [ "$TYPE" != "command" ] && [ "$TYPE" != "agent" ]; then
  echo "ERROR: type must be 'command' or 'agent', got '$TYPE'"
  exit 2
fi

# --- Check 1: File exists and non-empty ---
if [ ! -f "$FILE" ]; then
  report_error "File not found: $FILE"
  echo "RESULT: FAIL ($error_count errors, $warn_count warnings)"
  exit 1
fi

if [ ! -s "$FILE" ]; then
  report_error "File is empty: $FILE"
  echo "RESULT: FAIL ($error_count errors, $warn_count warnings)"
  exit 1
fi

# --- Check 2: YAML frontmatter structure ---
first_line=$(head -1 "$FILE")
if [ "$first_line" != "---" ]; then
  report_error "Frontmatter missing: first line must be '---', got '${first_line}'"
fi

# Find closing --- (second occurrence, skip line 1)
closing_line=$(awk 'NR>1 && /^---$/{print NR; exit}' "$FILE")
if [ -z "$closing_line" ]; then
  report_error "Frontmatter not closed: missing second '---' marker"
  # Cannot continue validation without frontmatter
  echo "RESULT: FAIL ($error_count errors, $warn_count warnings)"
  exit 1
fi

# Extract frontmatter content (between the two --- markers)
frontmatter=$(sed -n "2,$((closing_line - 1))p" "$FILE")

# --- Check 3: Tabs in YAML frontmatter ---
tab_lines=$(echo "$frontmatter" | grep -n "	" 2>/dev/null || true)
if [ -n "$tab_lines" ]; then
  while IFS= read -r line; do
    line_num=$(echo "$line" | cut -d: -f1)
    actual_line=$((line_num + 1))
    report_error "Tab character in frontmatter at line $actual_line (use spaces only)"
  done <<< "$tab_lines"
fi

# --- Check 4: Required fields by type ---
if [ "$TYPE" = "command" ]; then
  # Command: description is required
  if ! echo "$frontmatter" | grep -q '^description:'; then
    report_error "Missing required field: 'description' (required for commands)"
  fi

  # Check allowed-tools format (if present)
  if echo "$frontmatter" | grep -q '^allowed-tools:'; then
    tools_value=$(echo "$frontmatter" | grep '^allowed-tools:' | sed 's/^allowed-tools: *//')
    # Check it's not a YAML list (next line starts with -)
    next_after_tools=$(echo "$frontmatter" | grep -A1 '^allowed-tools:' | tail -1)
    if echo "$next_after_tools" | grep -q '^ *-'; then
      report_error "allowed-tools must be comma-separated string, not YAML list"
    fi
    # Validate each tool name
    for tool in $(echo "$tools_value" | tr ',' '\n' | sed 's/^ *//;s/ *$//;s/(.*//' | grep -v '^$'); do
      if ! echo "$VALID_TOOLS" | grep -qw "$tool"; then
        report_error "Unknown tool in allowed-tools: '$tool'"
      fi
    done
  fi

elif [ "$TYPE" = "agent" ]; then
  # Agent: name, description, tools are required
  if ! echo "$frontmatter" | grep -q '^name:'; then
    report_error "Missing required field: 'name' (required for agents)"
  fi
  if ! echo "$frontmatter" | grep -q '^description:'; then
    report_error "Missing required field: 'description' (required for agents)"
  fi
  if ! echo "$frontmatter" | grep -q '^tools:'; then
    report_error "Missing required field: 'tools' (required for agents)"
  fi

  # Check name is kebab-case
  if echo "$frontmatter" | grep -q '^name:'; then
    name_value=$(echo "$frontmatter" | grep '^name:' | sed 's/^name: *//' | tr -d '"' | tr -d "'")
    if echo "$name_value" | grep -qE '[^a-z0-9-]'; then
      report_error "Agent name must be kebab-case (lowercase, hyphens only): got '$name_value'"
    fi
  fi

  # Check tools format
  if echo "$frontmatter" | grep -q '^tools:'; then
    tools_value=$(echo "$frontmatter" | grep '^tools:' | sed 's/^tools: *//')
    # Check it's not a YAML list
    next_after_tools=$(echo "$frontmatter" | grep -A1 '^tools:' | tail -1)
    if echo "$next_after_tools" | grep -q '^ *-'; then
      report_error "tools must be comma-separated string, not YAML list"
    fi
    # Validate each tool name
    for tool in $(echo "$tools_value" | tr ',' '\n' | sed 's/^ *//;s/ *$//;s/(.*//' | grep -v '^$'); do
      if ! echo "$VALID_TOOLS" | grep -qw "$tool"; then
        report_error "Unknown tool in tools: '$tool'"
      fi
    done
  fi
fi

# --- Check 5: $ARGUMENTS consistency (commands only) ---
if [ "$TYPE" = "command" ]; then
  body=$(sed "1,${closing_line}d" "$FILE")
  has_arguments=0
  has_hint=0
  echo "$body" | grep -q '\$ARGUMENTS' && has_arguments=1
  echo "$frontmatter" | grep -q '^argument-hint:' && has_hint=1

  if [ "$has_arguments" -eq 1 ] && [ "$has_hint" -eq 0 ]; then
    report_warn "\$ARGUMENTS used in body but no argument-hint in frontmatter (users won't know they can pass arguments)"
  fi
fi

# --- Check 6: Empty body warning ---
body=$(sed "1,${closing_line}d" "$FILE")
body_trimmed=$(echo "$body" | sed '/^$/d' | tr -d '[:space:]')
if [ -z "$body_trimmed" ]; then
  report_warn "File body is empty (no instructions after frontmatter)"
fi

# --- Result ---
if [ "$error_count" -gt 0 ]; then
  echo "RESULT: FAIL ($error_count errors, $warn_count warnings)"
  exit 1
else
  if [ "$warn_count" -gt 0 ]; then
    echo "RESULT: PASS ($warn_count warnings)"
  else
    echo "RESULT: PASS"
  fi
  exit 0
fi
