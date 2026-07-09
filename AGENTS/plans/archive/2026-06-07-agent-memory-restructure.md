---
title: Restructure agent memory & docs for findability (module-axis navigation)
date: 2026-06-07
status: completed
description: "Reorganize AGENTS/memory + AGENTS/docs so the agent finds any fact in one hop: thin always-loaded router, module-centric hubs as the primary navigation axis, code-shape conventions moved out of the always-loaded tier."
tags: [agents, memory, docs, knowledge-base]
---

## Goal

A knowledge base where the agent reaches any fact in **one hop** from the always-loaded tier, and where every topic has exactly one home.

Finished state:
- `MEMORY.md` is a thin router (~50 lines): always-on behavioral rules + a routing table (area → hub) + a handful of genuinely-atomic gotchas. No multi-line digests.
- Navigation has **one primary axis = modules** (`docs/<module>/INDEX.md`), mirroring `src/modules/<m>/`, plus a small set of cross-cutting hubs (platform, frontend, conventions, workflow) for what no single module owns.
- Code-shape conventions live in `docs/conventions/` (on-demand), not in the always-loaded index.
- No duplicated topics across memory↔docs; no orphan memory files; no stale entries.

## Context

Current volume: `MEMORY.md` index = **148 lines** (always loaded), **87** memory files (2756 lines), **34** docs (4191 lines).

The framework is already healthy and half-migrated:
- **`docs-audit` (completed 2026-06-07)** — docs verified against post-refactor code; staleness in docs is largely gone.
- **`memory-docs-boundary` (in_progress)** — decision **Model B** taken: split by *loading model* not content; one home per topic; memory entry that grows sections → promote to doc + pointer. MEMORY.md already trimmed 31 KB → 23 KB. A concrete "Remaining" list exists.

What the in-flight task does **not** address — and what actually causes "не найти нужное":
- **Navigation.** Even deduped, a 148-line flat index + ~120 files is unnavigable. There is no faceting; three parallel navigation surfaces (`MEMORY.md`, `docs/INDEX.md`, per-module hubs) overlap.
- **Conventions miscategorized.** ~25 of 87 memory files are `feedback_*`/conventions. They split into two classes the current scheme treats identically:
  - *behavioral/process* (must apply always, unprompted) → belong in always-tier;
  - *code-shape* (only relevant when touching that code) → belong on-demand.
  Today all ~25 cost a line in the always-loaded index.

Primary consumer = **the agent** (confirmed). Optimize the agent's retrieval model: fixed per-session load (MEMORY.md + tasks INDEX + docs INDEX) + on-demand grep/read. Navigation axis = **modules** (confirmed), cross-cutting hubs kept as the secondary axis.

This plan **supersedes and absorbs** `memory-docs-boundary` — its "Remaining" becomes Phase 1 here.

## Scope

**In scope:**
- Full inventory of all 87 memory files → classification (keep-always / atomic-fact / promote-to-doc / dedup-delete) and target home.
- Finish Model-B dedup + promotion (the `memory-docs-boundary` remainder).
- New `docs/conventions/` home for code-shape conventions.
- Rebuild `MEMORY.md` as a thin router with a module-keyed routing table.
- Complete per-module hub docs where missing; collapse the three navigation surfaces toward module hubs.
- Update governing rule text (`agent-primary.md`/CLAUDE.md, `README.md`, INDEX headers) to describe the new structure.

**Out of scope:**
- Rewriting doc *content* (audit already verified it; we move/link, not re-author).
- Changing `tasks/`, `research/`, `education/`, `plans/` internal structure (only their index cross-links if a path moves).
- Any `src/`/`web/` code change. This is records-only.
- The `i18n.md` `fallbackLocale` open question (belongs to docs-audit, leave flagged).

## Approach

Two layers, executed bottom-up so navigation is built on a deduped base:

1. **Consolidate (Model B finish)** — kill dupes and promote oversized memory files to their doc home. Prerequisite: nothing should be navigable in two places.
2. **Navigate (new)** — reclassify conventions, build the module-axis routing table, thin `MEMORY.md`, complete module hubs.

**Module-axis** chosen over layer-axis because the agent always works *inside* a module (`src/modules/<m>/`); a hub per module matches the unit of work and most facts already cluster per module. Pure layer-axis (backend/frontend/db) was rejected: it splits a single module's knowledge across hubs and fits the agent's task boundary worse. Cross-cutting hubs cover the residue that no module owns.

Each phase ends at a **stop-and-review** checkpoint with a concrete metric (index line count, dup count) before the next begins.

File moves use `mv` (preserve history) then `Edit` only the changed lines — never wholesale rewrite to relocate (`feedback_move_files`). Every file edited is `Read` immediately before editing (`feedback_reread_before_edit`).

## Steps

### Phase 0 — Inventory (read-only, produces the migration map)

1. Classify every `AGENTS/memory/*.md` into: `{keep-always, atomic-fact, promote→doc, dedup-delete}` + target home (module hub / cross-cutting hub / stays). Output a table inside this plan (or a scratch note). Files touched: this plan.
   - Delegate the fan-out read to subagents (≤87 small files); collate the table here.

### Phase 1 — Consolidate (finish Model B; removes dupes)

2. **conversation_insights** — fold `conversation_insights_axes/inferred_status/research_fields/tagger_version_idea/reports` into `docs/conversation_insights/INDEX.md`; leave ≤1-line pointers. Files: `docs/conversation_insights/INDEX.md`, the 5 memory files, `MEMORY.md`.
3. **llm_providers** — fold `project_agent_dispatch`, `project_agents_feature`, `project_llm_providers_mcp_servers`, `project_llm_providers_replay`, `llm_model_registry_pricing_gap`, `fastmcp_metadata_gotchas` into `docs/llm_providers/INDEX.md`; pointers. Files: that hub, the 6 memory files, `MEMORY.md`.
4. **intercom / mcp / frontend-rules** — `intercom_module.md` → `docs/intercom/module.md`; `mcp_server_surface.md` → new `docs/mcp/INDEX.md` (also home for `mcp_https_only`); `frontend_rules.md` → `docs/frontend-rules.md`. Pointers left.
5. **Dedup pairs** — pick the doc home and reduce the memory side to a pointer: `soft_delete_pattern`↔`soft-delete.md`; `versioning_pattern` (conversations vs general); conversations content/lifecycle ↔ `conversations/schema.md` + `dates.md`; core_nlp (`mail_history_stripper` + `project_core_nlp_module`) ↔ core_nlp README. Files: the doc homes + memory files + `MEMORY.md`.
   - **Checkpoint 1:** zero topic appears in both tiers; `MEMORY.md` < 20 KB.

### Phase 2 — Reclassify conventions

6. Create `docs/conventions/` with area files: `backend.md` (CRUD one-file-per-entity, DTO layout, field-change=3-layers, crud-descriptive-names, crud-session-ownership, minimal-indirection, api-url-style, table-column-order, hard-delete-breaks-aggregates), `frontend.md` (vuetify-date-input, vbtntoggle, btngroup-size, pagelayout-scroll), `db-migrations.md` (cross-module depends_on — or pointer to `migrations.md`). Each = the convention text moved verbatim. Files: new `docs/conventions/*.md`, the source memory files, `docs/INDEX.md`.
7. Keep in always-tier (behavioral/process, consolidated into one block in `MEMORY.md`): discussion≠go, never-guess-verify, commit-protocol, commit-language-english, edit-by-hand, reread-before-edit, comment-before-command, move-files. Delete the standalone files once inlined as a compact block, OR keep as files with a single grouped index line — decide at Checkpoint 2.
   - **Checkpoint 2:** code-shape conventions no longer cost individual index lines.

### Phase 3 — Rebuild MEMORY.md as a router

8. Rewrite `MEMORY.md` to three sections: **[1] Always-apply rules** (compact behavioral block), **[2] Routing table** (`module/area → hub doc path`, one row each), **[3] Atomic gotchas** (only true ≤3-line facts that don't belong to any hub). Target ~50 lines. Files: `MEMORY.md`.

### Phase 4 — Complete module hubs (the primary axis)

9. Ensure every active module with knowledge has a `docs/<module>/INDEX.md` hub linking its reference + facts + relevant conventions. Add missing hubs (e.g. `conversations`, `intercom` already partial, `mail_sync`, `twenty`, `core_nlp`). Each hub: short intro + links to its docs + its atomic gotchas (by pointer). Files: `docs/<module>/INDEX.md`, `docs/INDEX.md`.
10. Reconcile the three navigation surfaces: `docs/INDEX.md` = library map keyed by the same module axis; `MEMORY.md` routing table points at hubs; per-module hubs are the leaf. No fact reachable in >1 hop from MEMORY.md.

### Phase 5 — Governing text + final sweep

11. Update `agent-primary.md` (= `CLAUDE.md`), `AGENTS/README.md`, `MEMORY.md` + `docs/INDEX.md` headers to describe the module-axis + conventions home. Files: those 4.
12. Final sweep: no orphan memory files (every file linked from MEMORY.md or a hub), no dup topics, no broken cross-links. Re-run a link check.
    - **Checkpoint 3 (done):** pick 5 random facts, confirm each is one hop from MEMORY.md and lives in exactly one place.

## Tests

Records-only change — no automated tests. Validation is structural (see below).

## Validation

- `MEMORY.md` line count ≤ ~55 and byte size well under the 24.4 KB load limit.
- Grep audit: no topic string appears in both a memory file and a doc (spot-check the known former-dup pairs).
- Link check: every `[[name]]` / relative link in `MEMORY.md` + `docs/INDEX.md` + hubs resolves.
- One-hop test: for 5 sampled facts (one per axis), the path MEMORY.md → hub → fact is ≤1 intermediate hop.
- Orphan check: every `AGENTS/memory/*.md` is referenced from `MEMORY.md` or a hub; every `docs/**` is in `docs/INDEX.md` or a hub.

## Risks / open questions

- Risk: broken cross-links after mass `mv` — mitigation: link check in Phase 5; move per-module in small batches with a checkpoint each.
- Risk: over-thinning MEMORY.md drops a rule the agent relied on being always-present — mitigation: behavioral rules stay in always-tier by explicit allow-list (Step 7), only code-shape moves out.
- Open question (Step 7): inline behavioral rules as one block vs keep files + one grouped index line. Decide at Checkpoint 2 based on resulting line count.
- Open question: does `conventions` become `docs/conventions/` (subdir) or flat `docs/conventions-*.md`? Leaning subdir for the module-axis symmetry; confirm at Phase 2.

## Inventory outcome (Phase 0 — done 2026-06-07)

Classified 85 memory files via 5 parallel Explore agents. Decisions:
- **Q1 resolved:** behavioral rules inline as a compact block in `MEMORY.md`; delete the 8 source files.
- **Q2 resolved:** conventions live in subdir `docs/conventions/{backend,frontend,db-migrations}.md`.

**KEEP-ALWAYS (8 → inline block in MEMORY.md, delete files):** discussion_not_go, never_guess_verify, commit_protocol, commit_language_english, edit_by_hand, reread_before_edit, comment_before_command, move_files.

**CODE-SHAPE → docs/conventions/ (delete files):**
- backend.md: field_change_three_layers, crud_one_file_per_entity, dto_layout, minimal_indirection, api_url_style, crud_descriptive_names, hard_delete_breaks_aggregates, crud_session_ownership, versioning_pattern.
- frontend.md: vuetify_date_input, vbtntoggle_small_enums, vuetify_btngroup_size, pagelayout_scroll.
- db-migrations.md: table_column_order, migration_cross_module_depends_on.

**PROMOTE → existing platform docs (dup; verify-then-delete):** project_architecture→core-architecture, project_modules_state→core-module-system, project_loggers→core-loggers, core_api_standards→api-zones, permissions_rollout_policy→permissions, db_tls_strict_contract→database, soft_delete_pattern→soft-delete, project_bench_layout→benches, project_live_tests+test_parallelism_per_worker_db→testing.
**PROMOTE → new platform/cross-cutting docs:** project_overview+run_configs→docs/platform/, mcp_server_surface (124 lines)→docs/mcp/INDEX.md (also home for mcp_https_only).
**PROMOTE → module hubs:** conversations_module_layout+content_hash→conversations/; ci reports/axes/research_fields/tagger_version_idea→conversation_insights/INDEX.md; agent_dispatch/agents_feature/llm_providers_mcp_servers/llm_providers_replay/model_registry_pricing_gap→llm_providers/INDEX.md; intercom_module/fin_body_part_types/batch_upsert_chunk→docs/intercom/module.md (new); mail_html_security→docs/mail_sync/INDEX.md (new); project_core_nlp_module+mail_history_stripper→core_nlp README.
**PROMOTE frontend:** frontend_rules (146 lines)→docs/frontend-rules.md (new); design_system_state→docs/design-system.md (new).
**DEDUP frontend (verify-then-delete):** frontend_auth_permissions→permissions+frontend-route-meta; frontend_transitions→frontend-route-meta; i18n_frontend_setup→i18n.

**ATOMIC (stay as memory files, linked from hub/MEMORY.md):** env_prefix_scheme, project_test_runtime_dev_leak, project_src_pythonpath_shadow, project_app_path_tmp, dead_deps_pruned, project_qwen_lineage, miro_mcp_rendering, fastmcp_metadata_gotchas, full_update_task_split_skip_guard, conversations_lifecycle_timestamps, conversation_insights_inferred_status, intercom_source_id_not_unique, intercom_search_day_granularity, intercom_import_http_bound, mail_thread_builder_rebuild, twenty_import_scope, frontend_auth_bootstrap, frontend_pagelayout_meta_snapshot, user_profile_feature, responsive_testing_process, mobile_action_sheet_pattern, clickable_card_default, layout_scss_page_layout, table_pagination_bar, vue_i18n_special_chars, safe_email_body_sizing.

**Orchestration rule:** execution subagents own DISJOINT doc homes and must NOT touch `MEMORY.md` or `docs/INDEX.md` — those are rebuilt centrally in Phase 3/5 to avoid write conflicts.

## References

- Supersedes task: `AGENTS/tasks/2026-06-07-memory-docs-boundary.md` (its "Remaining" = Phase 1 here)
- Related task: `AGENTS/tasks/2026-06-07-docs-audit.md` (docs already verified vs code)
- This task: `AGENTS/tasks/2026-06-07-agent-memory-restructure.md`
- Governing text: `AGENTS/agent-primary.md` (= `CLAUDE.md`), `AGENTS/README.md`
- Indexes: `AGENTS/memory/MEMORY.md`, `AGENTS/docs/INDEX.md`
