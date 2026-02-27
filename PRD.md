---
name: agent-builder
description: Meta-agent đa nền tảng (Claude Code, Gemini CLI, Antigravity) tự động sinh, test, và cải tiến agents từ yêu cầu ngôn ngữ tự nhiên — với 3 bản native riêng cho từng platform
status: backlog
priority: P0
created: 2026-02-27T10:26:34Z
---

# PRD: agent-builder

## Executive Summary

Chúng ta xây dựng một **meta-agent** có khả năng nhận yêu cầu bằng ngôn ngữ tự nhiên (tiếng Việt) từ người dùng, sau đó tự động sinh ra các agents/commands hoạt động được ngay trên platform người dùng đang sử dụng. Agent builder được triển khai dưới dạng **3 bản native riêng biệt** cho 3 platform: Claude Code (slash commands + subagents), Gemini CLI (custom commands + subagents), và Google Antigravity (workflows + skills). Điểm khác biệt cốt lõi so với các công cụ hiện có như claude-code-skill-factory là **vòng lặp cải tiến tự động (iterative refinement loop)**: agent không chỉ generate một lần mà tự validate format, chạy thử thực tế, phân tích kết quả, và tự sửa lỗi — lặp tối đa 5 vòng trước khi trả output cuối cùng. Đối tượng chính là người mới chưa quen các AI coding platforms, cần được hướng dẫn từng bước.

## Problem Statement

### Vấn đề từ góc nhìn người dùng

Người mới bắt đầu với các AI coding agent platforms (Claude Code, Gemini CLI, Antigravity) gặp rào cản lớn khi muốn tạo custom agents/commands:

1. **Không biết cấu trúc file — và mỗi platform một kiểu:** Claude Code dùng `.md` với YAML frontmatter và `$ARGUMENTS`, Gemini CLI dùng `.toml` với cú pháp riêng và `!{...}` shell injection, Antigravity dùng `.md` với schema khác và `// turbo` annotations. Người mới phải học 3 bộ format khác nhau.
2. **Quy trình trial-and-error tốn thời gian:** Viết file → chạy thử → lỗi format → sửa → chạy lại → output không đúng ý → sửa logic → chạy lại. Mỗi lần mất 10-30 phút, lặp lại 3-5 lần cho một command đơn giản. Nhân với 3 platforms = nightmare.
3. **Không biết best practices của từng platform:** Claude Code có `context: fork`, `allowed-tools`; Gemini CLI có `!{shell commands}`, extensions; Antigravity có `// turbo-all`, Agent Manager integration. Mỗi nơi một bộ patterns riêng.
4. **Không có feedback loop:** Sau khi tạo xong, không có cách tự động verify command/agent hoạt động đúng trên platform đó. Phải test thủ công.

### Tần suất và mức độ đau

- **Ai bị ảnh hưởng:** Mọi người dùng mới của bất kỳ AI coding platform nào muốn customize workflow.
- **Tần suất:** Mỗi lần muốn tạo/sửa agent mới — trung bình 2-5 lần/tuần cho active users.
- **Mức độ:** **Blocking** — nhiều người bỏ cuộc sau lần thất bại đầu tiên vì không hiểu lỗi, quay lại dùng platform vanilla mà không customize.

### Workaround hiện tại

- **Copy-paste từ templates:** Tìm trên GitHub, sửa thủ công. Vấn đề: templates thường outdated, chỉ cho 1 platform, không match project context.
- **Nhờ AI viết trực tiếp:** Gõ "help me create a command for X" — AI có thể viết file nhưng không tự verify, không nhất quán về format, không có iterative refinement.
- **claude-code-skill-factory:** Hỏi 4-5 câu → generate 1 lần → xong. Chỉ hỗ trợ Claude Code, không có vòng lặp test, output thường cần sửa thủ công 2-3 lần.

### Chi phí của việc không giải quyết

- Người dùng mới churn rate cao vì không customize được workflow.
- Productivity gap: users không tận dụng được sức mạnh thực sự của các AI coding platforms.
- Mỗi platform phát triển ecosystem riêng → fragmentation, không có tool thống nhất giúp người dùng.

## Target Users

### Persona 1: "Minh" — Developer mới, đang thử Claude Code
- **Context:** Vừa cài Claude Code 1-2 tuần, đã dùng được các tính năng cơ bản. Muốn tạo slash command đầu tiên nhưng không biết bắt đầu từ đâu. Không biết YAML frontmatter là gì.
- **Primary need:** Được hướng dẫn từng bước bằng tiếng Việt, từ mô tả ý tưởng đến có command hoạt động được.
- **Pain level:** **High**

### Persona 2: "Lan" — Developer có kinh nghiệm, dùng Gemini CLI
- **Context:** Đã dùng Gemini CLI vài tháng, biết cách viết `.toml` command thủ công nhưng muốn tốc độ. Thường cần tạo 2-3 commands mới mỗi tuần.
- **Primary need:** Mô tả nhanh bằng ngôn ngữ tự nhiên → nhận output `.toml` đã được test → dùng ngay.
- **Pain level:** **Medium**

### Persona 3: "Hùng" — Team Lead, dùng Antigravity
- **Context:** Quản lý team 5-8 devs, team dùng Antigravity IDE. Muốn chuẩn hóa workflow bằng shared skills và workflows.
- **Primary need:** Tạo workflows và skills production-ready, có error handling, documentation, share cho team.
- **Pain level:** **Medium**

### Persona 4: "Trang" — Freelancer, dùng nhiều platform
- **Context:** Nhận projects từ nhiều khách hàng, mỗi project dùng platform khác nhau. Cần tool thống nhất workflow.
- **Primary need:** Một mental model duy nhất — mô tả yêu cầu một cách, nhận output đúng format cho platform đang dùng.
- **Pain level:** **High**

## User Stories

**US-1: Tạo agent từ mô tả tự nhiên trên Claude Code**
As Minh (developer mới), I want to mô tả bằng tiếng Việt điều tôi muốn command làm so that tôi nhận được một Claude Code slash command hoạt động mà không cần hiểu YAML frontmatter.

Acceptance Criteria:
- [ ] Chạy `/agent-builder` trong Claude Code → được hỏi mô tả yêu cầu bằng tiếng Việt
- [ ] Agent hỏi tối đa 3-5 câu clarification, thân thiện, không dùng thuật ngữ kỹ thuật trừ khi cần
- [ ] Output là file `.md` đúng format Claude Code slash command (valid YAML frontmatter: `description`, `argument-hint`, `allowed-tools`; body dùng `$ARGUMENTS` syntax)
- [ ] Command được install vào `.claude/commands/` và chạy được ngay bằng `/command-name`
- [ ] Toàn bộ quá trình từ mô tả đến command hoạt động < 5 phút

**US-2: Tạo agent từ mô tả tự nhiên trên Gemini CLI**
As Lan (developer Gemini CLI), I want to mô tả yêu cầu bằng tiếng Việt so that tôi nhận được một Gemini CLI custom command đúng format TOML hoạt động ngay.

Acceptance Criteria:
- [ ] Chạy `/agent-builder` trong Gemini CLI → được hỏi mô tả yêu cầu
- [ ] Output là file `.toml` đúng format Gemini CLI custom command (valid TOML: `description`, `prompt` field, `!{...}` shell injection nếu cần)
- [ ] File được tạo tại `.gemini/commands/` và chạy được bằng `/command-name`
- [ ] Nếu cần subagent → output là `.md` trong `.gemini/agents/` đúng format Gemini subagent
- [ ] Toàn bộ quá trình < 5 phút

**US-3: Tạo agent từ mô tả tự nhiên trên Antigravity**
As Hùng (team lead dùng Antigravity), I want to mô tả workflow cần tạo so that tôi nhận được Antigravity workflow hoặc skill đúng format, có documentation cho team.

Acceptance Criteria:
- [ ] Trong Antigravity, trigger agent builder qua workflow hoặc command
- [ ] Output là file `.md` đúng format Antigravity workflow tại `.agent/workflows/`, hoặc skill folder với `SKILL.md` tại `.agent/skills/`
- [ ] Output bao gồm documentation section: purpose, usage, examples
- [ ] Toàn bộ quá trình < 10 phút cho workflow phức tạp

**US-4: Vòng lặp tự động validate và test**
As Minh (developer mới), I want agent builder tự kiểm tra output trước khi đưa cho tôi so that tôi nhận được agent đã được verify hoạt động đúng.

Acceptance Criteria:
- [ ] Validation platform-specific: Claude Code (YAML, `$ARGUMENTS`, `allowed-tools`), Gemini CLI (TOML syntax, `prompt` field), Antigravity (YAML, workflow steps)
- [ ] Chạy thử command/agent với ít nhất 1 test input, kiểm tra output hợp lý
- [ ] Nếu fail → tự sửa, không cần người dùng can thiệp
- [ ] Tối đa 5 vòng; hiển thị progress ("🔄 Vòng 2/5: Đang sửa lỗi TOML syntax...")
- [ ] Sau 5 vòng fail → dừng, hiển thị diagnostic, hỏi người dùng debug cùng

**US-5: Auto-detect loại output phù hợp**
As Trang (freelancer đa platform), I want agent builder tự suggest loại output phù hợp nhất so that tôi không cần biết sự khác biệt giữa command, agent, workflow, và skill.

Acceptance Criteria:
- [ ] Suggest loại output dựa trên mô tả: command (tác vụ đơn) vs agent (persona chuyên biệt) vs workflow (multi-step) vs skill (auto-triggered)
- [ ] Giải thích ngắn gọn bằng tiếng Việt tại sao loại này phù hợp
- [ ] Người dùng có thể override
- [ ] Logic nhất quán across platforms

**US-6: Cải tiến agent đã tạo**
As Lan (developer có kinh nghiệm), I want to quay lại sửa agent đã tạo bằng mô tả thay đổi so that tôi không cần edit file thủ công.

Acceptance Criteria:
- [ ] Chạy refine command để cải tiến agent đã tồn tại
- [ ] Đọc file hiện tại, hiểu context, hỏi muốn thay đổi gì
- [ ] Áp dụng thay đổi → chạy lại validate + test → output cải tiến
- [ ] Giữ nguyên phần không thay đổi

**US-7: Hướng dẫn người mới hiểu output**
As Minh (developer mới), I want agent builder giải thích output bằng tiếng Việt so that tôi học được cách tự viết agent sau này.

Acceptance Criteria:
- [ ] Hiển thị: file ở đâu, cách chạy, các phần chính
- [ ] Giải thích platform-specific concepts đơn giản (frontmatter, `$ARGUMENTS`, TOML, `!{...}`, workflow steps, turbo annotations...)
- [ ] 1-2 ví dụ cách chạy command/agent vừa tạo
- [ ] Optional: "💡 Tips" để hiểu thêm

## Requirements

### Functional Requirements (MUST)

**FR-1: Discovery conversation engine**
Agent hỏi người dùng 3-5 câu bằng tiếng Việt để hiểu yêu cầu. Câu hỏi platform-agnostic (tập trung "muốn làm gì" chứ không phải format). Nếu bỏ → output sai mục đích.

**FR-2: Claude Code generator**
Sinh slash commands (`.claude/commands/<n>.md` — YAML frontmatter, `$ARGUMENTS`, `allowed-tools`) và subagents (`.claude/agents/<n>.md` — persona, tools, instructions). Nếu bỏ → mất 1/3 platform coverage.

**FR-3: Gemini CLI generator**
Sinh custom commands (`.gemini/commands/<path>/<n>.toml` — TOML format, `prompt`, `!{shell}`) và subagents (`.gemini/agents/<n>.md` — YAML + system prompt). Nếu bỏ → mất 1/3 platform coverage.

**FR-4: Antigravity generator**
Sinh workflows (`.agent/workflows/<n>.md` — YAML + steps, `// turbo`) và skills (`.agent/skills/<n>/SKILL.md`). Nếu bỏ → mất 1/3 platform coverage.

**FR-5: Format validation — platform-specific**
Validate output đúng format: Claude (YAML, required fields, `$ARGUMENTS`), Gemini (TOML syntax, `prompt`), Antigravity (YAML, workflow steps, skill schema). Nếu bỏ → format errors người dùng mới không fix được.

**FR-6: Runtime test**
Chạy thử output với synthetic test input trên platform hiện tại. Kiểm tra crash, output hợp lý, error handling. Nếu bỏ → mất core differentiator.

**FR-7: Iterative refinement loop (max 5 vòng)**
Fail → phân tích → sửa → validate + test lại. Tối đa 5 vòng. Hiển thị progress. Sau 5 vòng → hỏi người dùng debug cùng. Nếu bỏ → mất core differentiator.

**FR-8: Auto-detect output type**
Suggest loại output phù hợp platform: Claude (command vs agent), Gemini (command vs agent), Antigravity (workflow vs skill). Cho confirm/override. Nếu bỏ → người dùng mới phải tự biết sự khác biệt.

**FR-9: File installation — platform-aware**
Install output vào đúng directory. Confirm trước khi overwrite. Nếu bỏ → thêm friction.

**FR-10: Post-creation explanation (tiếng Việt)**
Tóm tắt file ở đâu, cách chạy, giải thích concepts. Bao gồm ví dụ. Nếu bỏ → người dùng mới không biết dùng output.

### Functional Requirements (NICE-TO-HAVE)

**NTH-1: Refine existing agent** — Cải tiến agent đã tạo. Deferred: MVP focus creation flow.

**NTH-2: Template library per platform** — 5-10 presets mỗi platform. Deferred: cần validate generation quality trước.

**NTH-3: Cross-platform export** — Tạo trên 1 platform, export format khác. Deferred: quá phức tạp cho MVP.

**NTH-4: Project context awareness** — Đọc codebase để customize. Deferred: tăng complexity.

**NTH-5: Shared core prompt library** — 3 bản share prompts/templates qua git. Deferred: ổn định từng bản trước.

### Non-Functional Requirements

**NFR-1: Thời gian end-to-end** — < 5 phút command đơn giản, < 10 phút agent phức tạp, cả 3 platforms. Đo: timestamp logs.

**NFR-2: Tỷ lệ thành công** — Pass validation + runtime ≤ 3 vòng cho ≥ 80% cases standard, per platform. Đo: log vòng lặp.

**NFR-3: Tương thích platform version** — Latest stable của Claude Code, Gemini CLI, Antigravity. Test: install + run per platform.

**NFR-4: Ngôn ngữ** — Conversation tiếng Việt, output file tiếng Anh, cả 3 bản.

**NFR-5: Không external dependencies** — Offline, không API ngoài, per platform.

**NFR-6: Zero-config installation** — Claude Code: copy → `.claude/`. Gemini CLI: copy → `.gemini/`. Antigravity: copy → `.agent/`. Không package managers.

**NFR-7: Cross-platform consistency** — Cùng mô tả → cùng logic output, chỉ khác format. Đo: 10 scenarios test cả 3, so sánh quality.

## Success Criteria

| # | Criterion | Target | How to Measure | When |
|---|-----------|--------|----------------|------|
| SC-1 | Người mới tạo agent thành công | ≥ 90% per platform | Test 10 người mới / platform | Beta + 2 tuần |
| SC-2 | Thời gian command đơn giản | < 5 phút | Timestamp logs | Mỗi lần generate |
| SC-3 | Pass validation vòng 1 | ≥ 60% per platform | Log vòng lặp | Sau 50 lần / platform |
| SC-4 | Pass validation + runtime ≤ 3 vòng | ≥ 80% per platform | Log vòng lặp | Sau 50 lần / platform |
| SC-5 | Không cần edit thủ công | ≥ 70% | Survey per generate | Beta + 4 tuần |
| SC-6 | User satisfaction | ≥ 4/5 stars per platform | Rating prompt | Ongoing |
| SC-7 | Cross-platform quality consistency | Tương đương | 10 scenarios cả 3 platforms | Quarterly |

## Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| **3 bản drift apart** — Logic diverge, quality khác nhau, 3x maintenance. | High | High | Shared test suite: 20 scenarios chạy cả 3. Shared design doc cho core logic. Quarterly sync review. |
| **Runtime test không đáng tin** — Test input đơn giản, false positive. | High | High | Test suite đa dạng per platform. User feedback loop. Platform-specific test harness. |
| **Vòng lặp không converge** — Sửa lỗi A tạo lỗi B. | High | Medium | Cap 5 vòng, fail gracefully. Log mỗi vòng. Fix priority: format first, logic second. |
| **Platform format thay đổi** — 3 platforms = 3x rủi ro format change. | High | Medium | Format spec tách riêng per bản. Version pin. Monitor changelogs. Community channel. |
| **Gemini TOML complexity** — TOML khác biệt lớn so với Markdown-based. | Medium | High | TOML template library. Extra test coverage. Dedicated TOML validation. |
| **Antigravity spec unstable** — Platform mới (Nov 2025), spec evolving. | Medium | High | Antigravity bản launch sau (Phase 3). Monitor changelog. Design modular. |
| **Context window overflow** — Discovery + generation + 5 test rounds. | Medium | Medium | Compact giữa các vòng: chỉ giữ requirements + file + latest error. |
| **Prompt quality thấp** — Instructions sinh ra vague/verbose. | Medium | High | Curated templates per platform. Quality rubric. User feedback. |

## Constraints & Assumptions

### Constraints

- **3 bản riêng hoàn toàn:** Mỗi platform một codebase. Có thể share docs, test scenarios, design patterns nhưng không share runtime code.
- **Native format only:** Mỗi bản chỉ output native format platform đó. Không cross-platform export.
- **Platform-native packaging:** Claude Code (`.claude/`), Gemini CLI (`.gemini/`), Antigravity (`.agent/`).
- **Tiếng Việt conversation, tiếng Anh output.**
- **Single-user scope.** Không collaboration trong MVP.
- **Không external dependencies** ngoài platform.

### Assumptions

- **Formats ổn định 6 tháng.** Nếu sai → update format spec. Risk cao nhất với Antigravity.
- **Người dùng mô tả được bằng ngôn ngữ tự nhiên.** Nếu sai → cần template gallery.
- **5 vòng đủ cho 95% cases.** Nếu sai → tăng cap hoặc redesign.
- **Runtime test khả thi cả 3 platforms.** Nếu sai cho 1 platform → fallback dry-run.
- **3 bản manageable.** Nếu sai → consolidate sang hybrid approach.
- **Gemini model generate TOML reliably.** Nếu sai → template-based thay vì free generation.

## Out of Scope

- **Cross-platform export** — Tạo trên platform A, export sang B. Xem xét v2.
- **Hooks generation** — JSON-based, khác workflow hoàn toàn. Separate feature.
- **GUI/Web interface** — CLI/editor-native only.
- **Multi-language i18n** — Chỉ tiếng Việt MVP.
- **Agent marketplace / sharing** — Không registry.
- **Versioning / rollback** — Dùng git.
- **Agent composition / chaining** — Agent gọi agent. Quá phức tạp MVP.
- **Shared runtime code** — 3 bản riêng. Shared core là NTH-5.
- **Claude Code Skills** — MVP Claude Code bản focus commands + agents. Skills xem xét sau.

## Dependencies

### Claude Code Version
- **Claude Code CLI** — Runtime. Anthropic. ✅ Stable.
- **Slash Command spec** — Format. Anthropic. ✅ Documented.
- **Subagent spec** — Format. Anthropic. ✅ Documented.
- **Claude model** — LLM. Anthropic. ✅ Available.

### Gemini CLI Version
- **Gemini CLI** — Runtime. Google. ✅ Stable (Apache 2.0).
- **TOML command spec** — Format. Google. ✅ Documented.
- **Subagent spec** — Format. Google. ✅ Documented.
- **Gemini model** — LLM. Google. ✅ Available.

### Antigravity Version
- **Google Antigravity IDE** — Runtime. Google DeepMind. ⚠️ Public preview. Spec có thể thay đổi.
- **Workflow spec** — Format. Google. ⚠️ Evolving.
- **Agent Skills spec** — Format. Open standard. ✅ Stable.
- **Gemini model** — LLM. Google. ✅ Available.

## Appendix A: Platform Format Comparison

| Dimension | Claude Code | Gemini CLI | Antigravity |
|-----------|------------|------------|-------------|
| **Command format** | `.md` + YAML frontmatter | `.toml` | `.md` + YAML frontmatter |
| **Command location** | `.claude/commands/` | `.gemini/commands/` | `.agent/workflows/` |
| **Agent format** | `.md` + YAML frontmatter | `.md` + YAML frontmatter | N/A (Agent Manager) |
| **Agent location** | `.claude/agents/` | `.gemini/agents/` | N/A |
| **Skill format** | `SKILL.md` in folder | `SKILL.md` in folder | `SKILL.md` in folder |
| **Skill location** | `.claude/skills/*/` | `.gemini/skills/*/` | `.agent/skills/*/` |
| **Arguments** | `$ARGUMENTS` | Appended to prompt auto | Via prompt context |
| **Shell injection** | `` !`command` `` | `!{command}` | Via `run_command` tool |
| **Tool permissions** | `allowed-tools:` frontmatter | Via settings.json | Via security policies |
| **Invoke command** | `/command-name` | `/command-name` | Workflow trigger or `/` |
| **Invoke agent** | `@agent-name` | Implicit routing | Agent Manager |
| **Special features** | `context: fork`, `agent:` field | Extensions, TOML multiline | `// turbo`, Plan/Fast modes |

## Appendix B: Architecture Flow

```
User mô tả yêu cầu (tiếng Việt)
        │
        ▼
┌─────────────────────┐
│  Discovery Engine    │ ← Hỏi 3-5 câu (logic giống nhau cả 3 bản)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Type Detector       │ ← Auto-detect loại output phù hợp platform
│  (Platform-aware)    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Generator           │ ← Sinh file ĐÚNG FORMAT cho platform hiện tại
│  (Platform-specific) │   Claude: .md  |  Gemini: .toml  |  AGY: .md
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────┐
│  Refinement Loop (max 5 vòng)       │
│  ┌──────────────┐  ┌─────────────┐  │
│  │ Validator     │─▶│ Runtime Test │  │
│  │ (per platform)│  │(per platform)│  │
│  └──────┬───────┘  └──────┬──────┘  │
│         │ FAIL             │ FAIL    │
│         ▼                  ▼         │
│  ┌─────────────────────────────┐     │
│  │  Auto-Fix Engine            │─────┘
│  └─────────────────────────────┘     │
│         │ PASS                       │
│         ▼                            │
│  ┌──────────────┐                    │
│  │  Output ✅    │                    │
│  └──────────────┘                    │
└──────────────────────────────────────┘
          │
          ▼ (fail sau 5 vòng)
┌─────────────────────┐
│  Interactive Debug   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Install & Explain   │ ← Đúng directory, giải thích tiếng Việt
│  (Platform-aware)    │
└─────────────────────┘
```

## Appendix C: File Structure Per Platform

### Claude Code Version
```
agent-builder-claude/
├── .claude/
│   ├── commands/
│   │   └── agent-builder.md           # /agent-builder entry point
│   └── agents/
│       └── builder-engine.md          # Core subagent (optional)
├── templates/
│   ├── slash-command.md
│   └── subagent.md
├── validators/
│   └── validate-claude.sh
├── specs/
│   ├── command-spec.md
│   └── agent-spec.md
├── CLAUDE.md
├── README.md
└── install.sh
```

### Gemini CLI Version
```
agent-builder-gemini/
├── .gemini/
│   ├── commands/
│   │   └── agent-builder.toml         # /agent-builder entry point
│   └── agents/
│       └── builder-engine.md
├── templates/
│   ├── custom-command.toml
│   └── subagent.md
├── validators/
│   └── validate-gemini.sh
├── specs/
│   ├── command-spec.md
│   └── agent-spec.md
├── GEMINI.md
├── README.md
└── install.sh
```

### Antigravity Version
```
agent-builder-antigravity/
├── .agent/
│   ├── workflows/
│   │   └── agent-builder.md           # Workflow entry point
│   └── skills/
│       └── agent-builder/
│           └── SKILL.md               # Skill-based entry (alternative)
├── .antigravity/
│   └── rules/
│       └── builder-rules.md
├── templates/
│   ├── workflow.md
│   └── skill/
│       └── SKILL.md
├── validators/
│   └── validate-antigravity.sh
├── specs/
│   ├── workflow-spec.md
│   └── skill-spec.md
├── README.md
└── install.sh
```

## Appendix D: Phased Rollout Plan

| Phase | Platform | Lý do thứ tự | Timeline |
|-------|----------|--------------|----------|
| Phase 1 | Claude Code | Format đơn giản nhất (all Markdown), ecosystem mature, dễ test | Tuần 1-4 |
| Phase 2 | Gemini CLI | TOML phức tạp hơn nhưng platform ổn định, open source, docs tốt | Tuần 5-8 |
| Phase 3 | Antigravity | Platform mới nhất, spec evolving, rủi ro format change cao nhất | Tuần 9-12 |

Mỗi phase: Build → Internal test (20 scenarios) → Beta (5-10 users) → Feedback → Stable release → Lessons learned feed phase tiếp.
