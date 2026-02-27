# Claude Code Slash Command Format Specification

## File Location
`.claude/commands/<name>.md` — invoked via `/<name>` in Claude Code.

Subdirectories supported: `.claude/commands/pm/status.md` → `/pm:status`

## YAML Frontmatter

Frontmatter is enclosed between two `---` markers starting at line 1.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `description` | string | **Yes** | — | Short description shown in command list. 1 line. |
| `argument-hint` | string | No | — | Placeholder text for arguments (e.g., `"<file_path>"`). Shown in UI. |
| `allowed-tools` | string | No | all tools | Comma-separated list of tools this command can use. Can include tool-specific args: `Bash(command)`. |
| `model` | string | No | session default | Which model to use: `haiku`, `sonnet`, `opus`. |

### Field Details

#### `description` (required)
Single-line text describing what the command does. Displayed when user types `/` to browse commands.

```yaml
description: "Generate a new React component with tests"
```

#### `argument-hint`
Placeholder text shown after the command name. Helps users understand what input is expected.

```yaml
argument-hint: "<component_name>"
```

#### `allowed-tools`
Restricts which tools the command can use. If omitted, all tools are available.

**Simple list:**
```yaml
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
```

**With tool-specific restrictions:**
```yaml
allowed-tools: Bash(npm test), Read, Glob
```

This restricts Bash to only run `npm test`.

**Valid tool names:**
`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `Task`, `WebFetch`, `WebSearch`, `NotebookEdit`, `LS`, `Search`, `MultiEdit`, `Agent`, `TodoWrite`, `BashOutput`, `KillBash`

#### `model`
Override the session model for this command.

```yaml
model: haiku
```

Valid values: `haiku`, `sonnet`, `opus`

## Body (Instructions)

Everything after the closing `---` is the command prompt/instructions. Written in Markdown.

### `$ARGUMENTS` Syntax

`$ARGUMENTS` is replaced with whatever the user types after the command name.

Example: User runs `/greet Hello World` → `$ARGUMENTS` = `Hello World`

**Usage patterns:**

```markdown
# In body text:
Analyze the file: $ARGUMENTS

# Conditional:
If $ARGUMENTS is empty, ask the user which file to analyze.

# As part of a command:
Run: `bash scripts/deploy.sh $ARGUMENTS`
```

If `argument-hint` is set but user provides no arguments, `$ARGUMENTS` is empty string.

## Valid Examples

### Example 1: Simple command with arguments
```markdown
---
description: "Count lines in a file"
argument-hint: "<file_path>"
allowed-tools: Read, Bash
---

Count the number of lines in the file: $ARGUMENTS

Display the result as:
- Total lines
- Non-empty lines
- Comment lines (lines starting with # or //)
```

### Example 2: Command with restricted tools
```markdown
---
description: "Run project tests"
allowed-tools: Bash(npm test), Read
model: haiku
---

Run the test suite and report results.

If tests fail, read the failing test file and suggest a fix.
Do not modify any files.
```

## Invalid Examples

### Invalid 1: Missing description
```markdown
---
argument-hint: "<name>"
allowed-tools: Read, Write
---

Create a new component called $ARGUMENTS.
```
**Error:** `description` is required. Command won't appear in command list.

### Invalid 2: Frontmatter not at line 1
```markdown

---
description: "My command"
---

Do something.
```
**Error:** Empty line before first `---`. Frontmatter must start at line 1.

### Invalid 3: Tabs in YAML
```markdown
---
description:	"My command"
allowed-tools:	Read, Write
---
```
**Error:** Tabs in YAML frontmatter. Use spaces only.

### Invalid 4: $ARGUMENTS without argument-hint
```markdown
---
description: "Process input"
---

Process: $ARGUMENTS
```
**Warning:** Works but users won't know they can pass arguments. Add `argument-hint` for better UX.

## Common Pitfalls

1. **Frontmatter must start at line 1** — no blank lines before first `---`
2. **Use spaces, not tabs** in YAML frontmatter
3. **`description` is required** — without it, command won't show in list
4. **`allowed-tools` is a comma-separated string**, not a YAML list
5. **`$ARGUMENTS` is literal** — write it exactly as `$ARGUMENTS`, not `${ARGUMENTS}` or `$args`
