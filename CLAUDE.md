# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

**Agent Builder** is a standalone AI workflow tool — a single markdown workflow file (`agent-build.md`) that can be installed into any project. When invoked via `/agent-build "<description>"`, it auto-generates an AI agent definition file, runs it immediately, and refines it through a feedback loop.

There is no build system, package manager, or test runner. The "code" is markdown-based workflow instructions.

## Installation

```bash
# Install into the current project (run from target project root)
./install.sh
```

`install.sh` detects the target directory in order: `.agent/workflows/` → `.claude/commands/` → creates `.agent/workflows/`. It copies `agent-build.md` and optionally copies example agents.

## Usage

After installation, invoke in any AI IDE that supports workflows:

```
/agent-build "thu thập tiêu đề bài viết từ VnExpress"
/agent-build "review Python code for security issues"
/agent-build "analyze data from a CSV file"
```

## Key Files

- `agent-build.md` — The main workflow definition (source of truth). Also symlinked/copied to `.agent/workflows/agent-build.md`.
- `install.sh` — Copies the workflow into a target project.
- `examples/` — Three reference agent files: `web-scraper.md`, `code-reviewer.md`, `data-analyzer.md`.

## Agent File Format

Generated agents use YAML frontmatter + markdown system prompt:

```yaml
---
name: kebab-case-name          # Required: [a-z0-9-], 3-40 chars
description: action-oriented description ≥10 words  # Required
tools: Read, Glob, Grep        # Required: comma-separated string
model: inherit                 # Required: sonnet|opus|haiku|inherit
color: green                   # Required: blue|green|red|purple|orange
field: data                    # Optional: frontend|backend|testing|security|data|ai|...
expertise: expert              # Optional: beginner|intermediate|expert
---

System prompt content here...
```

Generated agents are saved to the first detected directory: `./agents/` → `.claude/agents/` → `.agent/agents/`.

## Architecture: The Workflow Pipeline

The `agent-build.md` workflow runs these steps:

1. **Preflight** — Validate description, detect/create agent directory.
2. **Clarification** (conditional) — Ask ≤3 questions if description < 20 words and lacks input source, output format, or task scope.
3. **Type Classification** — Auto-detect one of 4 agent types by keyword matching (supports EN + VI).
4. **Learn Format** — Read an existing agent or example file to infer format conventions.
5. **Generate Agent** — Name (kebab-case), select tools (3-tier safety model), write system prompt, create file, validate (3-step).
6. **Immediate Execution** — Spawn the generated agent via Task tool.
7. **Refinement Loop** — Accept feedback, update agent definition, re-run (max 10 iterations).

## Agent Types & Tool Safety

| Type | Color | Default Tools | Parallelism |
|------|-------|---------------|-------------|
| Strategic | blue | Read, Glob, Grep, WebFetch, WebSearch | Up to 4-5 agents |
| Implementation | green | Read, Write, Edit, Glob, Grep (+ask Bash) | Up to 2-3 agents |
| Quality | red | Read, Write, Edit, Bash, Glob, Grep | Sequential only |
| Coordination | purple | Read, Glob, Grep (+ask Task/Agent) | Lightweight |

**3-tier tool safety:**
- **Safe** (auto): Read, Glob, Grep, LS, WebFetch, WebSearch
- **Cautious** (auto + warn): Write, Edit, NotebookEdit
- **Restricted** (always ask user): Bash, Task, Agent

## Editing the Workflow

The canonical source is `agent-build.md` in the repo root. The copy at `.agent/workflows/agent-build.md` is kept in sync — if you edit one, update the other (or re-run `install.sh`).

When modifying the workflow logic in `agent-build.md`, keep these constraints:
- Clarification step: max 3 questions total
- Type detection: max 1 additional fallback question
- Refinement loop: suggest restart at iteration 5, hard stop at iteration 10
- Tool safety tiers must not be relaxed without explicit user confirmation
