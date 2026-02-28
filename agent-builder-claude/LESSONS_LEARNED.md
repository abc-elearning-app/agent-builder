# Lessons Learned — Agent Builder Phase 1 (Claude Code)

## What Worked Well

### 1. Template + Spec separation
Keeping format specs (rules/docs) separate from templates (skeletons) proved effective.
The spec serves as both documentation and validation reference; the template gives
the generator a clear starting structure to fill.

### 2. Bash-only validator
Pure bash validation (no Python/Node) kept the zero-dependency promise.
`grep`, `awk`, `sed` are sufficient for YAML frontmatter checks. The structured
error output (`ERROR: ...`, `WARN: ...`, `RESULT: ...`) makes it easy for the
AI refinement loop to parse and act on.

### 3. Command + Subagent pattern (AD-1)
Splitting UX (discovery conversation) from generation (builder-engine) keeps
each file focused. The `/agent-builder` command handles all user interaction;
`builder-engine` receives clean, structured requirements and can focus purely
on generation quality.

### 4. Vietnamese discovery, English output
Users describe requirements in Vietnamese (natural), generated files are in
English (standard for Claude Code). This separation was straightforward to
implement — the command handles Vietnamese, the engine outputs English.

### 5. Overwrite confirmation
Both `install.sh` and `builder-engine` check for existing files before
overwriting. Simple safety net that prevents accidental data loss.

## What Was Tricky

### 1. grep -c with set -e in bash
`grep -c` returns exit code 1 when count is 0, which triggers `set -e`.
Using `|| echo "0"` caused double output ("0\n0") because grep still
prints "0" before failing. Fix: use `grep -q` for boolean checks instead.

### 2. YAML frontmatter parsing with bash
Bash can handle simple YAML (key: value), but multi-line values (description: |)
and nested structures require careful `awk`/`sed` patterns. Keep frontmatter
simple — flat keys, single-line values where possible, pipe-style for multi-line.

### 3. Tool name validation
Claude Code tools evolve — the VALID_TOOLS list in the validator may need
updating. Consider making it configurable or auto-extractable.

## Patterns for Phase 2 (Gemini CLI)

### Reuse
- **Specs format**: Gemini CLI will need its own spec files, but the structure
  (frontmatter fields, body format, valid/invalid examples) can be copied.
- **Test infrastructure**: `run-validator-tests.sh` pattern + fixture approach
  works for any platform. Just change fixtures.
- **Validator pattern**: Same structural checks (frontmatter, required fields,
  format rules) apply — just different rules per platform.

### Adapt
- **Templates**: Gemini CLI uses different frontmatter format — new templates needed.
- **Type detection logic**: Gemini may not distinguish command/agent the same way.
- **Vietnamese flow**: Same discovery questions work, but generation rules differ.
- **Tool names**: Gemini CLI has different tool names — update validator list.

### Watch Out For
- **Format differences**: Each platform has its own frontmatter schema.
  Don't assume Claude Code format works elsewhere.
- **Validation strictness**: Start permissive, tighten based on actual failures.
  Phase 1 validator catches 6+ error types — may need more or fewer for Gemini.
- **Refinement loop rounds**: 5 rounds worked for Claude Code. Gemini may need
  more or fewer depending on generation quality baseline.

## Key Metrics (Phase 1 Baseline)

| Metric | Target | Achieved |
|---|---|---|
| FR coverage | 100% | 8/8 (100%) |
| NFR coverage | 100% | 4/6 (67%) + 2 pending E2E |
| Validator test suite | 100% | 10/10 (100%) |
| Test scenarios designed | 20 | 20 |
| External dependencies | 0 | 0 |
| Files in deliverable | ≥ 10 | 13 + 10 fixtures |

## Handoff Notes for Phase 2

1. Start with `specs/` — define Gemini CLI format first
2. Copy `templates/` structure — adapt frontmatter
3. Fork `validate-claude.sh` → `validate-gemini.sh` — change rules
4. Keep `/agent-builder` command — add platform selection question
5. Fork `builder-engine` → `builder-engine-gemini` — different generation rules
6. Reuse test infrastructure — new fixtures for Gemini format
