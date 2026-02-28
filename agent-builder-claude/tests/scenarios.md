# E2E Test Scenarios — Agent Builder

20 scenarios to validate the full agent-builder pipeline: discovery → type detection → generation → validation → install → explanation.

## How to Run

Each scenario: run `/agent-builder` in Claude Code and provide the Vietnamese description. Measure:
- **Time**: total from start to completion
- **Rounds**: validation rounds before pass (target: ≤ 3)
- **Pass**: does generated file pass `validate-claude.sh`?
- **Quality**: 1-5 rating of generated instructions (5 = usable as-is)

---

## Simple Commands (S01–S08)

### S01: Đếm dòng file
- **Input**: "tạo lệnh đếm số dòng trong file"
- **Expected type**: command
- **Expected tools**: Read, Bash
- **Expected**: `argument-hint` with file path, `$ARGUMENTS` in body

### S02: Format JSON
- **Input**: "tạo lệnh format file JSON cho đẹp"
- **Expected type**: command
- **Expected tools**: Read, Write, Bash
- **Expected**: reads file, formats, writes back

### S03: Tìm TODO
- **Input**: "tạo lệnh tìm tất cả TODO trong project"
- **Expected type**: command
- **Expected tools**: Grep, Glob
- **Expected**: searches for TODO/FIXME/HACK patterns

### S04: Git status summary
- **Input**: "tạo lệnh tóm tắt git status"
- **Expected type**: command
- **Expected tools**: Bash
- **Expected**: runs git commands, summarizes output

### S05: Tạo .gitignore
- **Input**: "tạo lệnh sinh file .gitignore cho project Node.js"
- **Expected type**: command
- **Expected tools**: Write
- **Expected**: creates .gitignore with node_modules, dist, .env, etc.

### S06: Chạy test
- **Input**: "tạo lệnh chạy test và báo cáo kết quả"
- **Expected type**: command
- **Expected tools**: Bash, Read
- **Expected**: runs test suite, parses output, reports summary

### S07: Đổi tên biến
- **Input**: "tạo lệnh đổi tên biến trong file"
- **Expected type**: command
- **Expected tools**: Read, Edit, Grep
- **Expected**: `argument-hint`, finds and replaces variable name

### S08: Kiểm tra port
- **Input**: "tạo lệnh kiểm tra port nào đang được sử dụng"
- **Expected type**: command
- **Expected tools**: Bash
- **Expected**: runs lsof/netstat, displays results

## Complex Commands (C01–C06)

### C01: Review PR changes
- **Input**: "tạo lệnh review những thay đổi trong PR hiện tại"
- **Expected type**: command
- **Expected tools**: Bash, Read, Grep, Glob
- **Expected**: git diff analysis, categorized findings

### C02: Generate unit tests
- **Input**: "tạo lệnh sinh unit test cho file được chỉ định"
- **Expected type**: command
- **Expected tools**: Read, Write, Bash, Glob
- **Expected**: reads source file, generates test file, runs tests

### C03: Analyze bundle size
- **Input**: "tạo lệnh phân tích kích thước bundle của project JavaScript"
- **Expected type**: command
- **Expected tools**: Bash, Read, Glob
- **Expected**: runs build/analyze, reports sizes, suggests optimizations

### C04: Database migration
- **Input**: "tạo lệnh sinh migration file cho database"
- **Expected type**: command
- **Expected tools**: Read, Write, Bash
- **Expected**: `argument-hint` for migration name, creates migration file

### C05: API documentation
- **Input**: "tạo lệnh sinh API docs từ code TypeScript"
- **Expected type**: command
- **Expected tools**: Read, Glob, Grep, Write
- **Expected**: scans for endpoints/types, generates markdown docs

### C06: Refactor imports
- **Input**: "tạo lệnh sắp xếp lại và dọn import trong file TypeScript"
- **Expected type**: command
- **Expected tools**: Read, Edit
- **Expected**: sorts imports, removes unused, groups by type

## Agents (A01–A04)

### A01: Code reviewer
- **Input**: "tạo trợ lý chuyên review code Python"
- **Expected type**: agent
- **Expected tools**: Read, Glob, Grep
- **Expected**: persona as senior Python dev, structured review output

### A02: TypeScript tutor
- **Input**: "tạo chuyên gia giải thích TypeScript cho người mới"
- **Expected type**: agent
- **Expected tools**: Read, Glob, Grep
- **Expected**: teacher persona, step-by-step explanations, examples

### A03: SQL helper
- **Input**: "tạo trợ lý viết và tối ưu SQL query"
- **Expected type**: agent
- **Expected tools**: Read, Bash, Grep
- **Expected**: DBA persona, query optimization suggestions, explain plans

### A04: Documentation writer
- **Input**: "tạo trợ lý viết docs cho codebase"
- **Expected type**: agent
- **Expected tools**: Read, Glob, Grep, Write
- **Expected**: tech writer persona, generates README/docs from code

## Edge Cases (E01–E02)

### E01: Mô tả rất ngắn
- **Input**: "tạo lệnh deploy"
- **Expected type**: command
- **Expected behavior**: agent-builder should ask follow-up questions to clarify
- **Key test**: does not crash, asks reasonable questions

### E02: Mô tả rất chi tiết
- **Input**: "tạo trợ lý chuyên review code TypeScript, focus vào type safety, kiểm tra null checks, verify interface implementations đúng, suggest generic types khi phù hợp, flag any usage, kiểm tra proper error handling với discriminated unions, và output báo cáo chi tiết theo format: file → issues → suggestions → severity"
- **Expected type**: agent
- **Expected behavior**: uses detailed description without over-asking
- **Key test**: captures all requirements in generated output
