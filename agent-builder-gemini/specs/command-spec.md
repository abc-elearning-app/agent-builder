# Gemini CLI Custom Command Format Specification

> Reference: [Gemini CLI Custom Commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md)

## File Location

`.gemini/commands/<name>.toml` — invoked via `/<name>` in Gemini CLI.

Subdirectories create namespaced commands: `.gemini/commands/git/commit.toml` → `/git:commit`

Commands can be placed in:
- **Project-level:** `<project-root>/.gemini/commands/` (shared with team)
- **User-level:** `~/.gemini/commands/` (personal)

Project commands override user commands with the same name.

## TOML Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | **Yes** | The prompt sent to the Gemini model. Single-line or multi-line (`"""`). |
| `description` | string | No | Brief one-line description shown in `/help`. Auto-generated from filename if omitted. |

### Field Details

#### `prompt` (required)

The core instruction text. Can be single-line or multi-line using TOML triple-quoted strings.

**Single-line:**
```toml
prompt = "Explain what this project does based on the README."
```

**Multi-line (triple-quoted):**
```toml
prompt = """
Analyze the current codebase and provide:
1. Architecture overview
2. Key dependencies
3. Potential improvements
"""
```

#### `description` (optional but recommended)

Brief text displayed in the command list.

```toml
description = "Analyze codebase architecture"
```

## Injection Syntax

### `!{shell command}` — Shell Command Injection

Execute a shell command and inject its output into the prompt.

```toml
prompt = """
Review the following staged changes:
!{git diff --staged}
"""
```

**Rules:**
- Braces inside `!{...}` must be balanced
- Complex commands with unbalanced braces should be wrapped in external scripts
- User sees a confirmation dialog before execution
- On failure, error message and exit code are injected into the prompt

### `@{file/path}` — File Content Injection

Embed file or directory contents into the prompt.

```toml
prompt = """
Review this file against our coding standards:
@{docs/coding-standards.md}
"""
```

**Rules:**
- Paths are relative to workspace root
- Supports: text files, images (PNG/JPEG), PDFs, audio, video
- Directory paths traverse subdirectories (respects `.gitignore` and `.geminiignore`)
- Processed BEFORE shell commands and argument substitution

### `{{args}}` — Argument Substitution

Replaced with whatever the user types after the command name.

```toml
prompt = "Fix this issue: {{args}}"
```

**Behavior:**
- Outside `!{...}`: injected exactly as typed (raw)
- Inside `!{...}`: automatically shell-escaped for safety
- If no `{{args}}` in prompt and user provides arguments: appended to prompt with two newlines

## Processing Order

1. **File injection** `@{...}` — first
2. **Shell commands** `!{...}` — second (with `{{args}}` shell-escaping if inside)
3. **Argument substitution** `{{args}}` — third

## Valid Examples

### Example 1: Simple command with description
```toml
description = "Count lines of code by file type"

prompt = """
Count the lines of code in this project, grouped by file type.
Show top 10 file types by line count.
Use the output of this command:

!{find . -name '*.py' -o -name '*.js' -o -name '*.ts' | head -50}
"""
```

### Example 2: Command with arguments and shell injection
```toml
description = "Search codebase for a pattern"

prompt = """
Please summarize the findings for the pattern `{{args}}`.

Search Results:
!{grep -r {{args}} . --include='*.py' --include='*.js' -l}
"""
```

### Example 3: Simple prompt without shell injection
```toml
description = "Explain the current project"

prompt = "Analyze the project structure and explain what this project does, its architecture, and key components."
```

## Invalid Examples

### Invalid 1: Missing prompt field
```toml
description = "My command"
```
**Error:** `prompt` is required. Without it, the command has no instructions to send.

### Invalid 2: Unbalanced triple quotes
```toml
description = "Broken command"

prompt = """
Do something useful.
The closing quotes are missing.
```
**Error:** Multi-line string opened with `"""` but never closed. Must have matching `"""` at the end.

### Invalid 3: Unbalanced braces in shell injection
```toml
prompt = """
!{echo "hello {world"}
"""
```
**Error:** Braces inside `!{...}` must be balanced. The `{world` has no closing brace. Wrap complex commands in a script instead.

### Invalid 4: Wrong string quoting
```toml
description = My command without quotes
prompt = Do something
```
**Error:** TOML string values must be quoted with `"..."` or `"""..."""`. Unquoted values are only valid for booleans, numbers, and dates.

## Common TOML Pitfalls

1. **Strings must be quoted** — use `"..."` for single-line, `"""..."""` for multi-line
2. **Triple-quoted strings** (`"""`) — opening and closing must match. Content starts on the line AFTER `"""`
3. **Escape sequences in basic strings** — `\"` for literal quotes, `\\` for backslash, `\n` for newline
4. **Literal strings** (`'...'`) — no escape processing, but cannot contain single quotes
5. **`!{...}` brace balance** — all braces inside must be paired. Use external scripts for complex commands
6. **`{{args}}` is literal** — write exactly `{{args}}`, not `$ARGUMENTS` or `$1`
7. **No YAML frontmatter** — TOML commands use TOML syntax, not `---` markers
8. **File extension must be `.toml`** — `.md` files are not recognized as commands
9. **Reload after changes** — use `/commands reload` to apply changes without restarting
