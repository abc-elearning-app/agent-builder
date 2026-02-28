# Gemini CLI Subagent Format Specification

> Reference: [Gemini CLI Subagents](https://geminicli.com/docs/core/subagents/)
> Status: Experimental — requires `enableAgents: true` in settings.json

## File Location

`.gemini/agents/<name>.md` — invoked automatically by the main agent when user intent matches the description.

Agents can be placed in:
- **Project-level:** `<project-root>/.gemini/agents/` (shared with team)
- **User-level:** `~/.gemini/agents/` (personal)

## Enablement

Custom subagents require explicit activation in `.gemini/settings.json`:

```json
{
  "experimental": {
    "enableAgents": true
  }
}
```

## YAML Frontmatter

Frontmatter is enclosed between two `---` markers starting at line 1.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | **Yes** | — | Unique identifier (slug). Lowercase letters, numbers, hyphens, underscores only. |
| `description` | string | **Yes** | — | Brief explanation of agent purpose. Helps main agent decide when to invoke. |
| `kind` | string | No | `local` | Agent type: `local` (runs in CLI) or `remote` (external service). |
| `tools` | array | No | default set | List of tool names the agent can use. YAML array format. |
| `model` | string | No | session default | Specific model to use (e.g., `gemini-2.5-pro`). |
| `temperature` | number | No | — | Sampling temperature (0.0–2.0). Lower = more deterministic. |
| `max_turns` | number | No | 15 | Maximum conversation turns before stopping. |
| `timeout_mins` | number | No | 5 | Maximum execution time in minutes. |

### Field Details

#### `name` (required)

Slug-format identifier. Must be unique across all agents.

```yaml
name: code-reviewer
```

**Valid:** `code-reviewer`, `test_writer`, `deploy-helper`
**Invalid:** `Code Reviewer` (spaces), `my.agent` (dots)

#### `description` (required)

The main agent reads this to decide whether to invoke the subagent. Be specific about when and how to use it.

```yaml
description: Specialized in finding security vulnerabilities in code. Use when reviewing code for security issues.
```

#### `tools` (optional, YAML array)

List of tools the agent can access. If omitted, uses the default tool set.

```yaml
tools:
  - read_file
  - grep_search
  - list_directory
  - write_file
  - run_shell_command
```

**Common Gemini CLI tool names:**
- `read_file` — Read file contents
- `write_file` — Create or overwrite files
- `edit_file` — Modify existing files
- `grep_search` — Search file contents
- `list_directory` — List directory contents
- `run_shell_command` — Execute shell commands
- `google_web_search` — Web search
- `write_todos` — Create TODO items

#### `model` (optional)

Override the session model for this agent.

```yaml
model: gemini-2.5-pro
```

## Body (System Prompt)

Everything after the closing `---` defines the agent's persona, behavior, and instructions. Written in Markdown.

The body typically includes:
1. **Role/persona** — Who the agent is
2. **Capabilities** — What it can and should do
3. **Constraints** — What it must not do
4. **Output format** — How to present results

## Valid Examples

### Example 1: Security auditor agent
```markdown
---
name: security-auditor
description: Specialized in finding security vulnerabilities in code. Use when reviewing code for security issues, checking for OWASP top 10, or auditing authentication flows.
kind: local
tools:
  - read_file
  - grep_search
  - list_directory
model: gemini-2.5-pro
temperature: 0.2
max_turns: 10
---

You are a senior security auditor. Your job is to analyze code for:
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting)
- Authentication and authorization issues
- Sensitive data exposure
- Input validation gaps

For each issue found, report:
1. File and line number
2. Severity (critical/high/medium/low)
3. Description of the vulnerability
4. Recommended fix with code example

Do NOT modify any files. Only report findings.
```

### Example 2: Test writer agent
```markdown
---
name: test-writer
description: Generates comprehensive unit tests for existing code. Use when you need to add test coverage for a module or function.
tools:
  - read_file
  - write_file
  - grep_search
  - run_shell_command
max_turns: 20
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
tools:
  - read_file
  - grep_search
---

Review code quality.
```
**Error:** `name` is required. Agent cannot be identified or invoked without it.

### Invalid 2: Missing description
```markdown
---
name: my-helper
tools:
  - read_file
---

Help with tasks.
```
**Error:** `description` is required. Main agent cannot determine when to invoke this agent.

### Invalid 3: Name with spaces
```markdown
---
name: "my cool agent"
description: "Does cool things"
---
```
**Error:** Name must be slug format — lowercase letters, numbers, hyphens, underscores only. Use `my-cool-agent` instead.

### Invalid 4: Tools as comma-separated string
```markdown
---
name: my-agent
description: "Helper agent"
tools: read_file, write_file, grep_search
---
```
**Error:** `tools` must be a YAML array (list format with `- `), not a comma-separated string. This is different from Claude Code agents.

## Common Pitfalls

1. **`name` must be slug format** — lowercase, hyphens/underscores only, no spaces
2. **`tools` is a YAML array** — use `- tool_name` format, NOT comma-separated string
3. **Tool names use snake_case** — `read_file`, not `Read` or `readFile`
4. **`description` drives invocation** — be specific about when to use this agent
5. **Frontmatter must start at line 1** — no blank lines before first `---`
6. **Enable agents in settings** — add `enableAgents: true` or agents won't load
7. **`kind: local` is default** — only specify `kind: remote` for external agents
8. **Temperature affects output** — use low (0.1-0.3) for deterministic tasks, higher for creative ones
