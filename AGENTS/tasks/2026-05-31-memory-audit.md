---
title: Memory audit — staleness + consolidation
date: 2026-05-31
status: completed
description: "Audit AGENTS/memory against real code: fix stale facts, delete obsolete entries, propose consolidation."
tags: [memory, maintenance]
---

## Task

"изучи память, давай посмотрим что можно объединить или что потеряло актуальность. Обязательно сверяйся с реальным кодом" — review memory files, find what to merge / what is stale, verifying against the real code.

## Context

70 memory files accumulated over many sessions. Some predate large refactors (module growth 3→9 registered, intercom_insights removed, mail_sync thread schema, i18n migrations, run-config rename).

## What was done

Verified every memory file against code via parallel Explore agents + direct grep/Read. Findings below.

### Stale — fixed
- `intercom_insights_module.md` — DELETED (module removed 2026-05-31; not in `build_modules()`, dir gone). Index line removed.
- `project_modules_state.md` — said 3-4 modules; now 9 registered + core_security util. Rewritten.
- `run_configs.md` — all `.run/` filenames changed (verb-prefix scheme). Rewritten.
- `mail_sync_schema.md` — `admin`/`contact`/`builder_version` columns dropped; `contact_members`→`client_members`; reply-time columns renamed; `created_at/updated_at`→`first_message_at/last_message_at`; `synced_at`→`processed_at`; `initiated_email`/`content_hash` added.
- `i18n_frontend_setup.md` — `fallbackLocale` is `'en'` not `'ru'`; ConversationsView pagination since migrated (all per-feature i18n done).
- `design_system_state.md` — 19→24 pages (+dividers/line-chart/world-map); "Next candidates" all shipped.
- `project_architecture.md` — "8 modules" updated; module list lives in `apps/app/modules.py` (not server.py); added `on_startup` hook; headhunter template ref replaced.
- `project_core_llm_module.md` — "8-table"→"7-table".
- `project_agent_dispatch.md` — `budget_tokens` dropped from `agent_configs` table (still a runtime setting + AgentBase attr).
- `project_agents_feature.md` — "no tools, no agent-loop" stale; chat supports tools via `mcp_codes`, agent loop implemented.

### Consolidation proposed (pending user confirmation)
- `intercom_batch_upsert_chunk.md` + `intercom_import_http_bound.md` → one import-architecture file.
- `mail_html_security.md` + `safe_email_body_sizing.md` → one SafeEmailBody file.

## Problems

`budget_tokens` was NOT fully removed (one sub-agent overstated): only the `agent_configs` DB column was dropped (`l1m0p0r0v4d0`); it survives as a runtime setting + `AgentBase` attr → `ResolvedAgentConfig`. Fixed accordingly.

Bash tool output was intermittently unreliable this session — a flaky empty grep made me briefly conclude `ChatView` had no tool loop and mis-edit `project_agents_feature.md`. Re-read of `ChatView.vue:193` (`while (resp.finish_reason === 'tool_use' && guard < 20)`) confirmed the frontend DOES drive the tool loop; reverted to the correct statement and marked the corresponding TODO done in `project_core_llm_module.md`. Lesson: verify with Read/Grep tools, not bash grep, this session.

## Result

Edited (all verified against code): `project_modules_state.md`, `run_configs.md`, `mail_sync_schema.md`, `i18n_frontend_setup.md`, `design_system_state.md`, `project_architecture.md`, `project_core_llm_module.md`, `project_agent_dispatch.md`, `project_agents_feature.md`, plus matching `MEMORY.md` index lines. Deleted `intercom_insights_module.md`. Consolidation of the two overlapping pairs is left pending the user's call.
