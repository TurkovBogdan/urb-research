# migrations: squash to one-per-table + rebuild dev (keep settings)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** research + web_search migrations · dev DB

## Goal

Collapse the accumulated migration chains to **one create-migration per table** (final schema,
no intermediate alter/drop), then **rebuild the dev sqlite** from the clean chain while preserving
`core_modules_settings` values (connector API keys + web_search settings). Prompted by: dev held
old prefixed codes after the bare-code refactor; and the chain had 14 research + 4 web_search
migrations full of churn (create→rename→drop→alter).

## What was done

### Squash (files)
- **research 14 → 5** (one per table, final shape): kept `rem_001_research`; wrote clean
  `rem_002_area` (no sort/brief), `rem_003_note` (kind CHECK already 6 values incl `clarification`),
  `rem_004_source_query`, `rem_005_source_document` (from the final source-table shape); deleted the
  13 old files (research_query/document/report creates, query_link, document, note, query_body,
  report_drop, source_tables, area_drop_sort, area_drop_brief, note_kind_clarification).
- **web_search 4 → 3**: folded the `content→body`/`content_hash→body_hash` rename (wsm_004) into
  `wsm_002_page` (columns created as `body`/`body_hash`); deleted `wsm_004_page_body`.
- **core** already one-per-table (`com_001..005`) — untouched.
- Fixed stale docstrings (`rem_001` no longer says `RS_`/`research_query`; `wsm_002` notes the
  squash). Chain stays 3 independent linear branches (heads: `rem_005_source_document`,
  `wsm_003_result`, `com_005_modules_state`); no cross-module/core FK, so branches are independent.

### Verify squash (before touching dev)
- Applied the chain on a **throwaway** sqlite (`DB_PATH=/tmp/...`): clean.
- Column-level compare migrated-schema vs model metadata for all 8 tables → **ALL MATCH** (names +
  nullability). CHECKs present (note 6 kinds, source_document status+relevance, page status);
  `body`/`body_hash` on page. No test references migration ids.

### Rebuild dev (gated → done on request)
1. `stop-all.sh` (backend held the file — killed to avoid deleted-inode).
2. Backup `core_modules_settings` read-only → 16 rows (PK `(module,key)`, **no FK** → trivial).
3. Drop `runtime/dev/app.sqlite3` (asserted path + sqlite header first).
4. `migrate upgrade` → rebuilt 14 tables via the squashed chain.
5. Re-insert the 16 settings rows.
6. `restart-backend.sh` → `/internal/health` ok; `/web-search/engines` reads restored settings
   (`search_default=xai`, connectors firecrawl/tavily/xai enabled — keys intact).

## Verification

Dev tables = 14 (core 6 + research 5 + web_search 3); `research_area` = 7 clean cols (no
sort/objective/scope/expectations), `research_note` = 8; `migrate check` up to date; `--all`-default
suite **341 passed**.

## Result

Clean migration history (one create per table), dev rebuilt from it with settings preserved,
backend healthy. Deferred (unchanged): `String(25)`→22 tightening, frontend research views, web/dist.
