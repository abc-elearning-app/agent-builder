# Agent Builder for Gemini CLI

Meta-agent that generates Gemini CLI custom commands and subagents from natural language descriptions in Vietnamese.

## Installation

```bash
# From agent-builder-gemini directory:
bash install.sh /path/to/your/project

# Or from your project directory:
bash /path/to/agent-builder-gemini/install.sh

# Force overwrite existing files:
bash install.sh /path/to/your/project --force
```

## Usage

In your Gemini CLI project, run:

```
/agent-builder
```

The agent builder will:
1. Ask 3-5 clarifying questions in Vietnamese
2. Auto-detect whether to create a command or agent
3. Generate the file with correct format (TOML for commands, Markdown for agents)
4. Validate and auto-fix (up to 5 rounds)
5. Install to the correct directory
6. Explain how to use it

## What Gets Generated

- **Custom commands** → `.gemini/commands/<name>.toml` (TOML format)
- **Subagents** → `.gemini/agents/<name>.md` (Markdown + YAML frontmatter)

## TOML Command Format

Gemini CLI custom commands use TOML:

```toml
description = "Brief description of what this command does"

[prompt]
content = """
Your prompt instructions here.
Can use !{shell command} for dynamic content.
"""
```

## Requirements

- Gemini CLI (latest stable)
- No other dependencies
