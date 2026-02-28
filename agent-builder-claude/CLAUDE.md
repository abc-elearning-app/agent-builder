# Agent Builder — Claude Code Version

> Meta-agent that generates Claude Code slash commands and subagents from natural language descriptions.

## Conventions

- **Conversation language:** Vietnamese (tiếng Việt)
- **Output file language:** English
- **No external dependencies** — everything runs with Claude Code built-in tools only
- **Zero-config installation** — copy files, run `/agent-builder`, done

## Project Structure

```
agent-builder-claude/
├── .claude/
│   ├── commands/
│   │   └── agent-builder.md       # /agent-builder entry point
│   └── agents/
│       └── builder-engine.md      # Core generation + refinement subagent
├── templates/
│   ├── slash-command.md            # Template for generating commands
│   └── subagent.md                 # Template for generating agents
├── validators/
│   └── validate-claude.sh          # Bash format validation script
├── specs/
│   ├── command-spec.md             # Claude Code command format spec
│   └── agent-spec.md               # Claude Code agent format spec
├── tests/
│   ├── scenarios.md                # 20 E2E test scenarios
│   ├── results.md                  # Test results + analysis
│   ├── run-validator-tests.sh      # Automated validator tests
│   └── test-fixtures/              # Valid/invalid test files
├── CLAUDE.md                        # This file
├── README.md                        # User documentation
└── install.sh                       # Installation script
```

## Architecture

- **Entry point:** `/agent-builder` slash command handles discovery conversation + type detection
- **Core engine:** `builder-engine` subagent handles generation + validation + refinement loop
- **Templates:** Provide format skeleton; AI fills in content intelligently
- **Validator:** Bash script for deterministic structural checks (YAML, frontmatter, required fields)

## Tool Permissions

The agent-builder uses these Claude Code tools:
- `Read` — Read templates, specs, existing files
- `Write` — Create generated command/agent files
- `Edit` — Modify files during refinement loop
- `Bash` — Run validator script, file operations
- `Glob` — Find files in user project
- `Grep` — Search file contents
- `Task` — Spawn builder-engine subagent

## Development Workflow

1. Edit files in this directory
2. Test by copying to a test project via `install.sh`
3. Run `/agent-builder` in the test project
4. Iterate based on results

## Format References

- Command format spec: `specs/command-spec.md`
- Agent format spec: `specs/agent-spec.md`
- Command template: `templates/slash-command.md`
- Agent template: `templates/subagent.md`
