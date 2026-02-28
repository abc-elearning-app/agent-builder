#!/usr/bin/env bash
# validate-gemini.sh — Structural validator for Gemini CLI commands and agents
# Usage: validate-gemini.sh <file_path> [type]
#   type: "command" or "agent" (auto-detected from extension if omitted)
#   Exit 0 = valid, Exit 1 = invalid, Exit 2 = usage error
# Output: structured error messages (one per line, AI-parseable)

set -euo pipefail

# --- Known valid Gemini CLI agent tools (snake_case) ---
VALID_TOOLS="read_file write_file edit_file grep_search list_directory run_shell_command google_web_search write_todos"

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
if [ $# -lt 1 ]; then
  echo "Usage: validate-gemini.sh <file_path> [type]"
  echo "  type: command | agent (auto-detected from extension if omitted)"
  exit 2
fi

FILE="$1"
TYPE="${2:-}"

# Auto-detect type from extension if not provided
if [ -z "$TYPE" ]; then
  case "$FILE" in
    *.toml) TYPE="command" ;;
    *.md)   TYPE="agent" ;;
    *)
      echo "ERROR: Cannot detect type from extension. Specify 'command' or 'agent'."
      exit 2
      ;;
  esac
fi

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

# ============================================================
# TOML COMMAND VALIDATION
# ============================================================
if [ "$TYPE" = "command" ]; then

  # --- Check 2: Has prompt field ---
  if ! grep -q '^prompt' "$FILE"; then
    report_error "Missing required field: 'prompt'"
  fi

  # --- Check 3: Triple-quote balance ---
  triple_count=$(grep -c '"""' "$FILE" || true)
  [ -z "$triple_count" ] && triple_count=0
  if [ "$((triple_count % 2))" -ne 0 ]; then
    report_error "Unbalanced triple-quoted string: found $triple_count '\"\"\"' markers (must be even)"
  fi

  # --- Check 4: Basic TOML key=value structure ---
  # Check that non-empty, non-comment lines outside multiline strings have valid structure
  in_multiline=0
  line_num=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_num=$((line_num + 1))

    # Track multiline string state
    # Count triple-quotes on this line
    tq_on_line=$( (echo "$line" | grep -o '"""' || true) | wc -l | tr -d ' ')
    if [ "$tq_on_line" -gt 0 ]; then
      if [ "$in_multiline" -eq 0 ]; then
        # Check if opening and closing on same line
        if [ "$tq_on_line" -ge 2 ]; then
          continue  # Self-contained multiline on one line
        fi
        in_multiline=1
        continue
      else
        in_multiline=0
        continue
      fi
    fi

    # Skip lines inside multiline strings
    [ "$in_multiline" -eq 1 ] && continue

    # Skip empty lines and comments
    stripped=$(echo "$line" | sed 's/^[[:space:]]*//')
    [ -z "$stripped" ] && continue
    echo "$stripped" | grep -q '^#' && continue

    # Check for valid TOML patterns: key = value, [section], or bare key
    if ! echo "$stripped" | grep -qE '^[a-zA-Z_][a-zA-Z0-9_-]*[[:space:]]*=' &&
       ! echo "$stripped" | grep -qE '^\[' ; then
      report_error "Line $line_num: Invalid TOML syntax: '$stripped'"
    fi
  done < "$FILE"

  # Check if we ended inside a multiline string
  if [ "$in_multiline" -eq 1 ]; then
    report_error "Unclosed multiline string: opened with '\"\"\"' but never closed"
  fi

  # --- Check 5: Unquoted string values ---
  # Check key = value lines where value is not quoted, boolean, or number
  while IFS= read -r kv_line; do
    kv_linenum=$(echo "$kv_line" | cut -d: -f1)
    kv_value=$(echo "$kv_line" | sed 's/^[^=]*=[[:space:]]*//')
    # Skip if quoted, boolean, number, or triple-quoted
    if ! echo "$kv_value" | grep -qE '^".*"$|^"""' &&
       ! echo "$kv_value" | grep -qE '^(true|false)$' &&
       ! echo "$kv_value" | grep -qE '^[0-9]'; then
      if [ -n "$kv_value" ]; then
        report_error "Line $kv_linenum: Unquoted string value (wrap with quotes): $kv_value"
      fi
    fi
  done < <(grep -nE '^[a-zA-Z_][a-zA-Z0-9_-]*[[:space:]]*=' "$FILE" || true)

  # --- Check 6: Shell injection !{} balance ---
  # Extract all !{...} blocks and check brace balance
  if grep -q '!{' "$FILE"; then
    # Simple check: count !{ and ensure each has a closing }
    open_count=$(grep -o '!{' "$FILE" | wc -l | tr -d ' ')
    # This is a heuristic — doesn't handle nested braces perfectly
    if [ "$open_count" -gt 0 ]; then
      # Check for empty !{} blocks
      if grep -q '!{}' "$FILE"; then
        report_error "Empty shell injection block: !{} (must contain a command)"
      fi
    fi
  fi

  # --- Check 7: description field (recommended) ---
  if ! grep -q '^description' "$FILE"; then
    report_warn "No 'description' field (recommended for /help display)"
  fi

# ============================================================
# MARKDOWN AGENT VALIDATION
# ============================================================
elif [ "$TYPE" = "agent" ]; then

  # --- Check 2: YAML frontmatter structure ---
  first_line=$(head -1 "$FILE")
  if [ "$first_line" != "---" ]; then
    report_error "Frontmatter missing: first line must be '---', got '${first_line}'"
  fi

  # Find closing ---
  closing_line=$(awk 'NR>1 && /^---$/{print NR; exit}' "$FILE")
  if [ -z "$closing_line" ]; then
    report_error "Frontmatter not closed: missing second '---' marker"
    echo "RESULT: FAIL ($error_count errors, $warn_count warnings)"
    exit 1
  fi

  # Extract frontmatter
  frontmatter=$(sed -n "2,$((closing_line - 1))p" "$FILE")

  # --- Check 3: Required fields ---
  if ! echo "$frontmatter" | grep -q '^name:'; then
    report_error "Missing required field: 'name' (required for agents)"
  fi
  if ! echo "$frontmatter" | grep -q '^description:'; then
    report_error "Missing required field: 'description' (required for agents)"
  fi

  # --- Check 4: Name format ---
  if echo "$frontmatter" | grep -q '^name:'; then
    name_value=$(echo "$frontmatter" | grep '^name:' | sed 's/^name: *//' | tr -d '"' | tr -d "'")
    if echo "$name_value" | grep -qE '[^a-z0-9_-]'; then
      report_error "Agent name must be slug format (lowercase, hyphens, underscores): got '$name_value'"
    fi
  fi

  # --- Check 5: Tools format (must be YAML array, not comma string) ---
  if echo "$frontmatter" | grep -q '^tools:'; then
    tools_line=$(echo "$frontmatter" | grep '^tools:' | sed 's/^tools: *//')
    if [ -n "$tools_line" ] && echo "$tools_line" | grep -q ','; then
      report_error "tools must be YAML array (list with '- '), not comma-separated string"
    fi

    # Validate tool names from array entries
    echo "$frontmatter" | awk '/^tools:/,/^[a-z]/' | (grep '^ *- ' || true) | sed 's/^ *- //' | while IFS= read -r tool; do
      tool=$(echo "$tool" | tr -d '[:space:]')
      [ -z "$tool" ] && continue
      if ! echo "$VALID_TOOLS" | grep -qw "$tool"; then
        report_error "Unknown tool: '$tool' (valid: $VALID_TOOLS)"
      fi
    done
  fi

  # --- Check 6: Tabs in frontmatter ---
  tab_lines=$(echo "$frontmatter" | grep -n "	" 2>/dev/null || true)
  if [ -n "$tab_lines" ]; then
    while IFS= read -r line; do
      tab_linenum=$(echo "$line" | cut -d: -f1)
      actual_line=$((tab_linenum + 1))
      report_error "Tab character in frontmatter at line $actual_line (use spaces only)"
    done <<< "$tab_lines"
  fi

  # --- Check 7: Empty body ---
  body=$(sed "1,${closing_line}d" "$FILE")
  body_trimmed=$(echo "$body" | sed '/^$/d' | tr -d '[:space:]')
  if [ -z "$body_trimmed" ]; then
    report_warn "File body is empty (no system prompt after frontmatter)"
  fi
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
