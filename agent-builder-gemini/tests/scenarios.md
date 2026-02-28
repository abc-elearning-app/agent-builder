# E2E Test Scenarios — Agent Builder (Gemini CLI)

20 scenarios to validate the full agent-builder pipeline: discovery → type detection → generation → validation → install → explanation.

Adapted from Phase 1 (Claude Code) scenarios for Gemini CLI TOML format.

## How to Run

Each scenario: run `/agent-builder` in Gemini CLI and provide the Vietnamese description. Measure:
- **Time**: total from start to completion
- **Rounds**: validation rounds before pass (target: ≤ 3)
- **Pass**: does generated file pass `validate-gemini.sh`?
- **Quality**: 1-5 rating of generated output (5 = usable as-is)

---

## Simple Commands (S01–S08)

### S01: Đếm dòng file
- **Input**: "tạo lệnh đếm số dòng trong file"
- **Expected type**: command (TOML)
- **Expected features**: `{{args}}` for file path, `!{wc -l}` or similar
- **Expected output**: `.gemini/commands/count-lines.toml`
- **Key validation**: valid TOML, has prompt field, `{{args}}` substitution

### S02: Format JSON
- **Input**: "tạo lệnh format file JSON cho đẹp"
- **Expected type**: command (TOML)
- **Expected features**: `{{args}}` for file path, `!{cat}` to read file
- **Expected output**: `.gemini/commands/format-json.toml`
- **Key validation**: valid TOML, shell injection syntax correct

### S03: Tìm TODO
- **Input**: "tạo lệnh tìm tất cả TODO trong project"
- **Expected type**: command (TOML)
- **Expected features**: `!{grep -r TODO .}` or similar
- **Expected output**: `.gemini/commands/find-todos.toml`
- **Key validation**: valid TOML, shell injection balanced braces

### S04: Git status summary
- **Input**: "tạo lệnh tóm tắt git status"
- **Expected type**: command (TOML)
- **Expected features**: `!{git status}`, `!{git diff --stat}`
- **Expected output**: `.gemini/commands/git-summary.toml`
- **Key validation**: valid TOML, multiple shell injections work

### S05: Tạo .gitignore
- **Input**: "tạo lệnh sinh file .gitignore cho project Node.js"
- **Expected type**: command (TOML)
- **Expected features**: plain prompt text (no injection needed)
- **Expected output**: `.gemini/commands/gen-gitignore.toml`
- **Key validation**: valid TOML, no unnecessary injection syntax

### S06: Chạy test
- **Input**: "tạo lệnh chạy test và báo cáo kết quả"
- **Expected type**: command (TOML)
- **Expected features**: `!{npm test}` or similar
- **Expected output**: `.gemini/commands/run-tests.toml`
- **Key validation**: valid TOML, shell injection correct

### S07: Đổi tên biến
- **Input**: "tạo lệnh đổi tên biến trong file"
- **Expected type**: command (TOML)
- **Expected features**: `{{args}}` for variable names
- **Expected output**: `.gemini/commands/rename-var.toml`
- **Key validation**: valid TOML, {{args}} used correctly

### S08: Kiểm tra port
- **Input**: "tạo lệnh kiểm tra port nào đang được sử dụng"
- **Expected type**: command (TOML)
- **Expected features**: `!{lsof -i -P -n}` or similar
- **Expected output**: `.gemini/commands/check-ports.toml`
- **Key validation**: valid TOML, shell command appropriate

## Complex Commands with Shell Injection (C01–C04)

### C01: Review PR changes
- **Input**: "tạo lệnh review những thay đổi trong PR hiện tại"
- **Expected type**: command (TOML)
- **Expected features**: `!{git diff}`, `!{git log}`, multi-step analysis
- **Expected output**: `.gemini/commands/review-pr.toml`
- **Key validation**: valid TOML, multiple `!{...}` blocks, balanced braces

### C02: Generate unit tests
- **Input**: "tạo lệnh sinh unit test cho file được chỉ định"
- **Expected type**: command (TOML)
- **Expected features**: `{{args}}` for file, `@{file}` injection, `!{...}` for test run
- **Expected output**: `.gemini/commands/gen-tests.toml`
- **Key validation**: valid TOML, mixed injection types

### C03: Analyze dependencies
- **Input**: "tạo lệnh phân tích dependencies trong package.json và tìm outdated packages"
- **Expected type**: command (TOML)
- **Expected features**: `@{package.json}` file injection, `!{npm outdated}` shell
- **Expected output**: `.gemini/commands/analyze-deps.toml`
- **Key validation**: valid TOML, @{} and !{} together

### C04: Database migration
- **Input**: "tạo lệnh sinh migration file cho database"
- **Expected type**: command (TOML)
- **Expected features**: `{{args}}` for migration name, structured output
- **Expected output**: `.gemini/commands/gen-migration.toml`
- **Key validation**: valid TOML, args substitution correct

## Agents (A01–A06)

### A01: Code reviewer
- **Input**: "tạo trợ lý chuyên review code Python"
- **Expected type**: agent (Markdown)
- **Expected tools**: `read_file`, `grep_search`, `list_directory`
- **Expected output**: `.gemini/agents/code-reviewer.md`
- **Key validation**: YAML frontmatter valid, tools as array, snake_case names

### A02: TypeScript tutor
- **Input**: "tạo chuyên gia giải thích TypeScript cho người mới"
- **Expected type**: agent (Markdown)
- **Expected tools**: `read_file`, `grep_search`
- **Expected output**: `.gemini/agents/typescript-tutor.md`
- **Key validation**: YAML frontmatter valid, description explains when to use

### A03: SQL helper
- **Input**: "tạo trợ lý viết và tối ưu SQL query"
- **Expected type**: agent (Markdown)
- **Expected tools**: `read_file`, `run_shell_command`, `grep_search`
- **Expected output**: `.gemini/agents/sql-helper.md`
- **Key validation**: YAML frontmatter valid, tools as YAML array

### A04: Documentation writer
- **Input**: "tạo trợ lý viết docs cho codebase"
- **Expected type**: agent (Markdown)
- **Expected tools**: `read_file`, `write_file`, `grep_search`, `list_directory`
- **Expected output**: `.gemini/agents/docs-writer.md`
- **Key validation**: YAML frontmatter valid, all fields present

## Edge Cases (E01–E02)

### E01: Mô tả rất ngắn
- **Input**: "tạo lệnh deploy"
- **Expected type**: command (TOML)
- **Expected behavior**: agent-builder should ask follow-up questions to clarify
- **Key test**: does not crash, asks reasonable questions, eventually produces valid TOML

### E02: Mô tả rất chi tiết
- **Input**: "tạo trợ lý chuyên review code TypeScript, focus vào type safety, kiểm tra null checks, verify interface implementations đúng, suggest generic types khi phù hợp, flag any usage, kiểm tra proper error handling với discriminated unions, và output báo cáo chi tiết theo format: file → issues → suggestions → severity"
- **Expected type**: agent (Markdown)
- **Expected behavior**: uses detailed description without over-asking
- **Key test**: captures all requirements in generated agent, valid YAML frontmatter, tools as array
