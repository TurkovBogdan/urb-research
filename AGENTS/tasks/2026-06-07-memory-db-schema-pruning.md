# Memory pruning — drop DB-schema dumps

**Date:** 2026-06-07
**Status:** completed

## Goal

Memory grew too large (MEMORY.md ~31 KB vs 24.4 KB load limit). User decision: stop
storing DB-schema column dumps in memory — they must be verified in code (`models/`)
anyway. Remove the email DB schema specifically, and generalize to *all* DB column blocks.
Read each note first to salvage non-derivable rationale before cutting.

## What was done

- **Deleted `mail_sync_schema.md`** entirely — it was nothing but 3 column tables
  (`mail_sync_threads`/`messages`/`filters`). Nothing non-derivable to salvage
  (lifecycle-timestamp convention already in [[conversations_lifecycle_timestamps]];
  multi-mailbox dup-thread limitation already tracked in tasks). Removed its index line.
- **Trimmed embedded column blocks** from mixed design docs, keeping rationale/decisions:
  - `project_core_llm_module.md` — replaced the «## DB schema (7 tables)» column dump with
    a 1-paragraph pointer (columns in `models/`; decisions stay under «Key decisions»);
    fixed front-matter description.
  - `conversations_module_layout.md` — dropped the «## Schema» enumeration + «CRUD-инвентарь»
    (method list = verify in code); kept PK formula, join-table no-soft-delete, hard-delete-removed,
    `get_min_ingested_at` no-deleted-filter as decisions.
  - `core_geo_module.md` — condensed «Schema highlights» to the only non-derivable bit
    (timezones carry **no lat/lon** — explicit decision) + M2M is_default/sort placement.
- **Fixed 2 dangling `[[mail_sync_schema]]` links** in `mail_history_stripper.md` +
  `project_modules_state.md`.

## Result

No dangling refs remain. DB column layouts no longer duplicated in memory — single source
of truth is `models/`. Design rationale (why-decisions) preserved in the module overview notes.

## Note

The broader MEMORY.md index-bloat (12 fat inline entries ~10 KB; the chunked-batch-rebuild
pattern spread across 4 cross-linked notes) was surveyed but NOT acted on — user redirected
to the DB-schema cleanup first. Still open as a follow-up.
