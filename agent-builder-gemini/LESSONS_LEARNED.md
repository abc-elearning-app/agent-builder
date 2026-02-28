# Lessons Learned — Phase 2: Agent Builder for Gemini CLI

## What Worked

### 1. Template-based generation with AI enhancement
- Same pattern from Phase 1 proved effective: spec + template + validator loop
- TOML template is simpler than Claude Code's Markdown format — fewer moving parts
- Builder-engine's 5-round validation loop catches format issues reliably

### 2. Bash-only validator
- No external dependencies (no Python TOML parser needed)
- Portable across macOS and Linux
- 15/15 test fixtures catch real-world mistakes: unquoted strings, unbalanced triple-quotes, empty shell injection blocks
- Process substitution (`< <(...)`) solved subshell variable scoping issues with `grep | while` pipelines

### 3. Phase 1 as blueprint
- Having Claude Code version as reference dramatically reduced design time
- Reusable patterns: discovery flow, type detection, validation loop, install script structure
- Test scenarios adapted directly — just changed expected format from Markdown to TOML

### 4. Spec-driven development
- `command-spec.md` and `agent-spec.md` serve dual purpose: guide for builder-engine AND reference for users
- Common pitfalls sections (9 for TOML, 8 for agents) prevent the most frequent mistakes
- Specs are the single source of truth — templates, validator, and generator all reference them

## What Didn't Work

### 1. macOS vs Linux shell differences
- `awk` syntax differs between BSD (macOS) and GNU versions
- `grep -c` returns exit code 1 when count is 0 with `set -e` / `pipefail`
- `grep -o` in pipelines needs `|| true` protection
- **Lesson**: Always use `|| true` after grep in pipelines, test on both platforms

### 2. GitHub CLI extensions limitations
- `gh sub-issue create` doesn't support `--body-file` flag
- Workaround: create issue first with `gh issue create`, then link with `gh sub-issue add`
- **Lesson**: Check extension CLI flags before building automation around them

### 3. zsh reserved variables
- `status` is read-only in zsh, causing silent failures in scripts
- **Lesson**: Avoid common names (`status`, `type`, `path`) as variable names in scripts that may run in zsh

## Key Differences: Claude Code vs Gemini CLI

| Aspect | Claude Code | Gemini CLI |
|--------|-------------|------------|
| Command format | Markdown with YAML frontmatter | TOML |
| Arguments | `$ARGUMENTS` | `{{args}}` |
| Shell injection | Not native | `!{command}` |
| File injection | Not native | `@{file/path}` |
| Agent tools | `allowed-tools` comma string | `tools` YAML array |
| Tool naming | PascalCase (`Read`, `Write`) | snake_case (`read_file`, `write_file`) |
| Agent enablement | Always enabled | Requires `enableAgents: true` in settings.json |

## Recommendations for Phase 3

### 1. Cross-platform testing
- Add CI/CD with both macOS and Ubuntu runners
- Validator tests should run on both platforms before release

### 2. Live E2E testing
- 20 scenarios defined but need Gemini CLI runtime to execute
- Consider containerized testing environment with Gemini CLI pre-installed
- Automate result collection into `results.md`

### 3. Shared validation library
- Both phases use similar validation patterns (frontmatter, required fields, syntax)
- Extract common validation functions into a shared library
- Would reduce maintenance burden for Phase 3

### 4. User feedback integration
- Install script works but lacks uninstall/update commands
- Consider adding `--update` flag to install.sh for in-place upgrades
- Add `--dry-run` flag to show what would be installed without writing

## Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Tasks completed | 8/8 | 8/8 |
| Validator tests | 15/15 | 15/15 |
| Files created | ~25 | 28 |
| External dependencies | 0 | 0 |
| Validator bugs found & fixed | — | 3 |
