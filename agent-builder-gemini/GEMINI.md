# Agent Builder — Gemini CLI Version

> Meta-agent that generates Gemini CLI custom commands and subagents from natural language descriptions.

## Conventions

- **Conversation language:** Vietnamese (tiếng Việt)
- **Output file language:** English
- **No external dependencies** — everything runs with Gemini CLI built-in tools only
- **Zero-config installation** — copy files, run `/agent-builder`, done

## Project Structure

```
agent-builder-gemini/
├── .gemini/
│   ├── commands/
│   │   └── agent-builder.toml      # /agent-builder entry point (TOML)
│   └── agents/
│       └── builder-engine.md       # Core generation + refinement subagent
├── templates/
│   ├── custom-command.toml          # Template for generating TOML commands
│   └── subagent.md                  # Template for generating agents
├── validators/
│   └── validate-gemini.sh           # Bash TOML validation script
├── specs/
│   ├── command-spec.md              # Gemini CLI TOML command format spec
│   └── agent-spec.md                # Gemini CLI subagent format spec
├── tests/
│   ├── scenarios.md                 # 20 E2E test scenarios
│   ├── results.md                   # Test results + analysis
│   ├── run-validator-tests.sh       # Automated validator tests
│   └── test-fixtures/               # Valid/invalid test files
├── GEMINI.md                        # This file
├── README.md                        # User documentation
└── install.sh                       # Installation script
```

## Architecture

- **Entry point:** `/agent-builder` TOML command handles discovery conversation + type detection
- **Core engine:** `builder-engine` subagent (Markdown) handles generation + validation + refinement loop
- **Templates:** Provide format skeleton; AI fills in content intelligently
- **Validator:** Bash script for deterministic TOML structural checks (key=value, [sections], required fields)

### Key Differences from Claude Code Version

| Aspect | Claude Code | Gemini CLI |
|--------|------------|------------|
| Command format | Markdown (`.md`) | TOML (`.toml`) |
| Command path | `.claude/commands/` | `.gemini/commands/` |
| Agent path | `.claude/agents/` | `.gemini/agents/` |
| Shell injection | `$ARGUMENTS` | `!{shell command}` |
| Agent format | Markdown + YAML | Markdown + YAML (same) |

## Tool Permissions

The agent-builder uses these Gemini CLI tools:
- `Read` — Read templates, specs, existing files
- `Write` — Create generated command/agent files
- `Edit` — Modify files during refinement loop
- `Shell` — Run validator script, file operations
- `Glob` — Find files in user project
- `Grep` — Search file contents

## Development Workflow

1. Edit files in this directory
2. Test by copying to a test project via `install.sh`
3. Run `/agent-builder` in the test project
4. Iterate based on results

## Format References

- Command format spec: `specs/command-spec.md`
- Agent format spec: `specs/agent-spec.md`
- Command template: `templates/custom-command.toml`
- Agent template: `templates/subagent.md`
