# Memory ↔ Docs boundary — redraw by loading model (Model B)

**Date:** 2026-06-07
**Status:** completed — remainder absorbed and finished by `2026-06-07-agent-memory-restructure` (Model B dedup/promotion = its Phase 1).

## Goal

Memory and Docs were blending — both defined by content type ("things not in code"),
so topics duplicated across the two (`soft-delete.md`↔`soft_delete_pattern.md`,
`dates.md`↔`conversations_lifecycle_timestamps.md`, `migrations.md`↔`migration_cross_module_depends_on.md`),
module overviews lived as mini-docs in memory (`project_*_module.md`), and docs already
reached into memory ("Conventions captured in memory" section). User wants the two
reconciled.

## Decision

**Model B — divide by loading model, not content; one home per topic.**

- **Memory** = always-in-context recall tier (index loads every session → keep small):
  `user` prefs, `feedback`/conventions, sharp ≤3-line gotchas, and one-line pointers to docs.
- **Docs** = on-demand reference tier (length is free): all structured/multi-section prose —
  architecture, contracts, runbooks, module references, DB schemas.
- **Single-home rule:** sections/prose → doc (+ optional ≤1-line memory pointer); lone 1–3 line
  fact → memory only. A memory entry that grows sections gets **promoted to a doc + pointer**.
  Never describe the same topic in both.

Rejected: Model A (merge into one — loses always-loaded recall) and Model C (memory becomes
pure pointer layer — more migration than needed now).

## What was done

- **Rule recorded** (first step, per user) in three places:
  - `AGENTS/agent-primary.md` (= `CLAUDE.md` symlink target) — new "Memory vs Docs — two tiers,
    one home per topic" subsection replacing the old Memory blurb; Docs section realigned.
  - `AGENTS/memory/MEMORY.md` header — Rules rewritten: recall tier, promote-on-sections,
    one-topic-one-home (the old "long entries → separate file alongside" rule was what bred mini-docs).
  - `AGENTS/docs/INDEX.md` header — Rules: reference tier, home for prose incl. promotions from memory.
  - `AGENTS/README.md` — new "В чём разница между разделами" subsection: 7-folder table (when-loaded / holds / key distinction) + the memory↔docs single-home boundary.

## Migration done so far

- **Batch 1 — module overviews → `docs/<module>/INDEX.md`:** promoted `core_geo` (+ business-data plan),
  `core_users`, `core_security`, `core_monitoring`, `llm_providers`; deleted the source memory files;
  index lines → one-line pointers; added 5 entries to `docs/INDEX.md` Modules section.
- **Batch 2 — fat INLINE entries → docs (the real index-size driver):** folded the ~12 multi-line inline
  blocks into their doc home + left a one-line pointer:
  - AlembicRunner.status → `migrations.md`
  - llm_providers indexing → `llm_providers/INDEX.md` §Indexing
  - ci06 provenance + «Обработанные чаты» → `conversation_insights/INDEX.md`
  - importer perf + member-resolve batch + `(row,count)` pairs → **new** `conversations/internals.md`
  - mobile nav + sidebar header-divider → `frontend-layout.md`; browser width gotcha → `debugging.md`
  - ThreadBuilder rebuild → **new** memory file `mail_thread_builder_rebuild.md` (atomic gotcha, one-line pointer)
  - core_users password change + FE 403-redirect → already in docs (`core_users`, `frontend-api-client`) → deleted dup, pointer only.
- **Result:** `MEMORY.md` 31257 → **23066 bytes** (under the 24.4 KB load limit). ✅

## Remaining

1. **conversation_insights linked files** — fold `conversation_insights_axes/inferred_status/research_fields/`
   `tagger_version/reports` into `conversation_insights/INDEX.md` (hub TODO note invites it), leave pointers.
2. **llm_providers linked files** — fold `project_agent_dispatch`, `project_agents_feature`,
   `project_llm_providers_mcp_servers`, `project_llm_providers_replay`, `llm_model_registry_pricing_gap`,
   `fastmcp_metadata_gotchas` into `llm_providers/INDEX.md` (note already lists them).
3. **Rest of Batch A** — `intercom_module.md` → `docs/intercom/module.md`; `mcp_server_surface.md` →
   `docs/mcp/INDEX.md`; `frontend_rules.md` → flat `docs/frontend-rules.md`.
4. **Rest of Batch B dedup** — `soft_delete_pattern`↔`soft-delete.md`, `versioning_pattern`,
   conversations content/lifecycle ↔ `conversations/schema.md`+`dates.md`, core_nlp (`mail_history_stripper`
   + `project_core_nlp_module`) — pick doc home, leave pointer.
