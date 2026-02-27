# CLAUDE.md

> Think carefully and implement the most concise solution that changes as little code as possible.

## Communication

- Always call the user "Chef"
- Always respond in Vietnamese
- Always suggest next steps at the end of each response (e.g., which `/pm:` command to run next)
- Always display the model being used (e.g., `[sonnet]`, `[opus]`) before starting any work

### Next Steps Convention
- Always suggest `/pm:` commands first when one exists; only suggest direct actions when no `/pm:` command covers it
- Annotate every suggestion with `[tier/model]`:
  - `[medium/sonnet]`: status, list, show, help, search, standup, blocked, gaps, coverage, start, complete, edit, sync, write, run, verify, reset; read-only git, code edits, tests, file creation
  - `[heavy/opus]`: new, parse, decompose, oneshot, merge, analyze, fix-gap; architecture decisions, complex debugging
- Example: `→ /pm:issue-complete [medium/sonnet]` or `→ git status [medium/sonnet]`

### Model Tiers Quick Reference
| Tier | `/pm:` commands | Direct actions |
|---|---|---|
| `[medium/sonnet]` | status, list, show, help, search, standup, blocked, gaps, start, complete, edit, sync, write, run, verify, reset | git ops, code edits, tests |
| `[heavy/opus]` | new, parse, decompose, oneshot, merge, analyze, fix-gap | architecture, debug |

## About This Project

This **IS** the CCPM (Claude Code Project Manager) project — a fork of [automazeio/ccpm](https://github.com/automazeio/ccpm) with enhanced task lifecycle, verification, and epic-level features.

CCPM dogfoods itself: the `.claude/` directory contains CCPM tooling that manages the development of CCPM itself.

### Project Structure

```
ccpm/                          # ← Project root
├── .claude/                   # ← Tooling: CCPM instance managing THIS project
│   └── ...                    #    (settings, internal state — don't edit for features)
│
│  # ── CCPM Source Code (edit these for feature work) ──
├── agents/                    # Task-oriented agents
├── commands/                  # PM slash command definitions (/pm:*)
├── config/                    # Configuration (lifecycle.json, etc.)
├── context/                   # Project-wide context system
├── epics/                     # Epic management
├── hooks/                     # Hook system (pre-task, post-task, stop, pre-tool-use)
├── install/                   # Installation scripts
├── prds/                      # PRD management
├── prompts/                   # Prompt templates (epic verify, semantic review)
├── rules/                     # Rule files (auto-loaded)
├── scripts/                   # Core scripts (verify, handoff, superpowers detection)
├── docs/                      # Feature documentation & PRDs
├── tests/                     # Test suites (E2E, integration)
│
│  # ── Config files ──
├── CLAUDE.md                  # This file
├── CLAUDE.md.example          # Template for end users
├── ccpm.config                # CCPM configuration
├── settings.json.example      # Claude Code settings template
├── settings.local.json        # Local settings (gitignored)
└── .gitignore
```

**Key distinction:**
- Root-level folders (`commands/`, `hooks/`, `scripts/`, etc.) = CCPM source code being developed
- `.claude/` = CCPM tooling instance that orchestrates development of THIS project

All code changes, new features, bug fixes → edit files at **project root**.
Never edit `.claude/` for feature work — that's the tooling layer.

## Python

- Always create and use `.venv` virtual environment
- Always run `python` and `pip` from `.venv`, never from global
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Development Workflow (CCPM manages CCPM)

```
PRD → Epic → Tasks → GitHub Issues → epic-start → epic-run (or manual loop) → epic-verify → epic-merge
```

### Key Commands

**Planning:**
- `/pm:prd-new <name>` - Create new PRD
- `/pm:prd-parse <name>` - Convert PRD to epic
- `/pm:epic-oneshot <name>` - Decompose + sync to GitHub

**Epic lifecycle:**
- `/pm:epic-start <name>` - Start epic (loads context, creates branch, checks verify state)
- `/pm:epic-run <name>` - Automate full epic execution (plan → execute → verify, parallel agents)
- `/pm:epic-status <name>` - View epic progress
- `/pm:epic-verify <name>` - Full verification pipeline (Phase A → Phase B)
- `/pm:epic-merge <name>` - Merge epic to main
- `/pm:epic-close <name>` - Close and archive epic

**Issue lifecycle (manual mode):**
- `/pm:issue-start <#>` - Start work on an issue (loads context)
- `/pm:verify-run` - Run verification checks mid-work
- `/pm:issue-complete` - Complete issue (handoff + verify + close)
- `/pm:handoff-write` - Write handoff notes for next session

**Epic verification:**
- `/pm:epic-verify-a <name>` - Phase A only (semantic review)
- `/pm:epic-verify-b <name>` - Phase B only (integration tests, Ralph loop)
- `/pm:epic-verify-status <name>` - Current verify state
- `/pm:epic-verify-report <name>` - View latest report
- `/pm:epic-gaps <name>` - View gap report
- `/pm:epic-accept-gaps <name>` - Accept gaps as tech debt
- `/pm:epic-fix-gap <name>` - Create issue from gap

**Dashboard:**
- `/pm:status` - Project dashboard
- `/pm:help` - Full command reference

## Rules

### DateTime & Frontmatter
- Always use real system time: `date -u +"%Y-%m-%dT%H:%M:%SZ"` — never placeholders
- All markdown files with metadata use YAML frontmatter
- Never modify `created` field after initial creation; always update `updated`
- See `.claude/rules/frontmatter.md`

### GitHub Operations
- **Always check remote origin** before any write operation to prevent syncing with the wrong repo
- Use `gh` CLI for all GitHub operations
- Strip frontmatter before posting to GitHub issues (see `.claude/rules/frontmatter.md`)
- Use relative paths in all public-facing content (no absolute paths with usernames)
- See `.claude/rules/github-operations.md`, `.claude/rules/path-standards.md`

### Git & Branching
- **NEVER `git add` files from `.claude/` directory** — it is in `.gitignore` and will always fail, wasting tokens
- One branch per epic: `epic/{name}`
- Commit format: `Issue #{number}: {description}`
- Small, focused, atomic commits
- Never use `--force` flags
- See `.claude/rules/git-workflows.md`

### Testing
- Always use the test-runner agent from `.claude/agents/`
- No mocking — use real services
- Run with verbose output
- Clean up test processes after execution
- See `docs/rules-reference/test-execution.md`

### Code Patterns
- Fail fast with clear error messages
- Trust the system — don't over-validate
- Minimal output — show what matters
- Use AST-grep for structural code analysis when available
- See `.claude/rules/standard-patterns.md`, `docs/rules-reference/use-ast-grep.md`

### Task Lifecycle

**Context Loading Protocol** (both `epic-start` and `issue-start`):
1. Load `context/handoffs/latest.md` → summarize "I understand that..."
2. Load epic context from `context/epics/{name}.md`
3. Review task/epic details
4. Wait for user confirmation before starting work
5. Run `hooks/pre-task.sh` if available

**Issue-level lifecycle:**
- **Start**: `/pm:issue-start` loads context via protocol above
- **During**: `hooks/pre-tool-use.sh` guards against destructive operations
- **Complete**: `/pm:issue-complete` runs handoff → verify → close in one step
- **Stop hook**: `hooks/stop-verify.sh` enforces verification before session end (Ralph loop)
- **Verification**: Tech-specific profiles in `context/verify/profiles/` (node, python, go, rust, swift, generic)
- **Handoff**: Always write notes via `/pm:handoff-write` — archived automatically
- **Config**: `config/lifecycle.json` controls verification mode, max iterations, cost limits
- Other commands: `/pm:verify-run`, `/pm:verify-skip`, `/pm:verify-status`, `/pm:handoff-show`, `/pm:context-health`, `/pm:context-reset`

**Epic-level lifecycle:**
- **Start**: `/pm:epic-start` loads context, creates branch, initializes `context/epics/{name}.md`, checks verify state
- **Verify**: `/pm:epic-verify` runs 2-phase pipeline:
  - **Phase A (Semantic Review)**: Claude reads all epic docs, produces Coverage Matrix + Gap Report + Quality Scorecard. No code execution. Assessment: EPIC_READY / EPIC_GAPS / EPIC_NOT_READY
  - **Phase B (Integration Verify)**: Runs 4-tier tests (smoke → integration → regression → performance). Ralph loop: fail → fix → retry. Max 30 iterations
- **Gap management**: `/pm:epic-gaps`, `/pm:epic-accept-gaps`, `/pm:epic-fix-gap`
- **Stop hook**: `hooks/stop-epic-verify.sh` enforces epic-level verification (Ralph loop)
- **Config**: `config/epic-verify.json` controls phases, max iterations, cost limits
- **State**: `context/verify/epic-state.json` tracks verify progress; `context/verify/epic-reports/` stores reports

### Agent Coordination
- Agents work on assigned file patterns only
- Commit early and often
- Communicate through commits and progress files
- Never attempt automatic merge conflict resolution
- See `.claude/rules/agent-coordination.md`

## Code Style

Follow existing patterns in the codebase.

## Testing

Always run tests before committing.