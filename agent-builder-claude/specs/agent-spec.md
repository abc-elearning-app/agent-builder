# Claude Code Subagent Format Specification

## File Location
`.claude/agents/<name>.md` — invoked via `Task` tool with `subagent_type: "<name>"`.

## YAML Frontmatter

Frontmatter is enclosed between two `---` markers starting at line 1.

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | string | **Yes** | — | Agent identifier. Used as `subagent_type` value when invoking via Task tool. |
| `description` | string | **Yes** | — | Multi-line description. Used for trigger matching — Claude decides to invoke agent when user intent matches. Include `<example>` blocks. |
| `tools` | string | **Yes** | — | Comma-separated list of tools the agent can use. |
| `model` | string | No | `inherit` | Model to use: `haiku`, `sonnet`, `opus`, or `inherit` (use parent session model). |
| `color` | string | No | — | Visual indicator in UI: `blue`, `red`, `green`, `yellow`. |

### Field Details

#### `name` (required)
Kebab-case identifier. Must match the `subagent_type` parameter in Task tool calls.

```yaml
name: code-reviewer
```

#### `description` (required)
Describes when and how to use this agent. Claude reads this to decide whether to invoke the agent. Include concrete examples with `<example>` blocks for best matching.

```yaml
description: |
  Use this agent to review code for quality issues.
  <example>
  user: "Review this PR for bugs"
  assistant: Uses code-reviewer agent
  </example>
```

#### `tools`
Comma-separated list of tools the agent has access to.

```yaml
tools: Glob, Grep, Read, Write, Edit, Bash
```

**Common tool sets:**
- Read-only: `Glob, Grep, Read, LS, Search`
- Full access: `Glob, Grep, Read, Write, Edit, Bash, Task`
- With web: `Glob, Grep, Read, WebFetch, WebSearch`

#### `model`
```yaml
model: inherit    # Use parent session model (default)
model: haiku      # Use haiku for fast, simple tasks
model: opus       # Use opus for complex tasks
```

## Body (Agent Instructions)

Everything after the closing `---` defines the agent's persona, behavior, and instructions. Written in Markdown.

The body typically includes:
1. **Role/persona** — Who the agent is
2. **Capabilities** — What it can and should do
3. **Constraints** — What it must not do
4. **Output format** — How to present results

## Valid Examples

### Example 1: Code reviewer agent
```markdown
---
name: code-reviewer
description: |
  Use this agent to review code changes for quality, bugs, and best practices.
  <example>
  user: "Review the changes in auth module"
  assistant: Launches code-reviewer agent
  </example>
tools: Glob, Grep, Read, Search
model: inherit
color: blue
---

You are a senior code reviewer. Your job is to analyze code for:
- Potential bugs and logic errors
- Security vulnerabilities
- Performance issues
- Code style and readability

For each issue found, report:
1. File and line number
2. Severity (critical/warning/info)
3. Description of the issue
4. Suggested fix

Do NOT modify any files. Only report findings.
```

### Example 2: Test writer agent
```markdown
---
name: test-writer
description: |
  Use this agent to generate unit tests for existing code.
  <example>
  user: "Write tests for the user service"
  assistant: Launches test-writer agent
  </example>
tools: Glob, Grep, Read, Write, Edit, Bash
model: sonnet
---

You are a test engineer. Given a source file or module:

1. Read the source code to understand the API
2. Identify testable functions and edge cases
3. Write comprehensive unit tests
4. Run the tests to verify they pass

Follow existing test patterns in the project.
Use the same test framework already in use.
```

## Invalid Examples

### Invalid 1: Missing name
```markdown
---
description: "Review code for bugs"
tools: Read, Glob, Grep
---

Review code quality.
```
**Error:** `name` is required. Agent cannot be invoked without it.

### Invalid 2: Missing tools
```markdown
---
name: my-agent
description: "Helper agent"
---

Help with tasks.
```
**Error:** `tools` is required. Agent won't have access to any tools.

### Invalid 3: Name with spaces
```markdown
---
name: "my cool agent"
description: "Does cool things"
tools: Read, Write
---
```
**Error:** Name should be kebab-case (`my-cool-agent`). Spaces may cause invocation failures.

### Invalid 4: Tools as YAML list
```markdown
---
name: my-agent
description: "Helper"
tools:
  - Read
  - Write
  - Bash
---
```
**Error:** `tools` must be comma-separated string, not a YAML list.

## Common Pitfalls

1. **`name` must be kebab-case** — no spaces, no underscores
2. **`tools` is a comma-separated string**, not a YAML list
3. **`description` should include examples** — without them, Claude may not invoke the agent at the right time
4. **Don't give agents tools they don't need** — principle of least privilege
5. **`model: inherit`** is usually best — lets the user control model selection
6. **Body instructions define behavior** — be specific about what the agent should and shouldn't do
