# research: research_query → link table (RQ_)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — research_query redesigned as a link table

## Goal

Redesign `research_query` from a plan-time subquery (int id + status) into a **link table** created
post-hoc (after a web_search run produced documents). It binds research + area + the web_search query.

Fields (6): code (RQ_ PK) · research_code (FK→research_index) · area_code (FK→research_area) ·
search_code (soft-ref→web_search_query WQ_, no FK) · query (Text) · created_at. `unique(area_code,
search_code)`. No status/updated_at/lifecycle (it's a completed-fact link).

Forces FK rewires (research_query.id disappears): research_document.query_id → query_code,
research_report.query_id → query_code (String FK → research_query.code). Dev tables all empty (0 rows).

## Decisions

- Prefix RQ_ now (2-letter; → RSQ_ in the deferred prefix task). code String(25).
- Both research_code AND area_code stored (denormalized per canvas).
- MCP: `research_add_queries` (text-list planning) → `query_link(research_code, area_code, search_code,
  query)` (post-hoc link). document/report tools: query_id → query_code.
- Migration rem_006_query_link: drop report/document/query, recreate all three (empty; forward-only).
- Frontend query views deferred (own TS types → vue-tsc stays green; runtime nav stale until redesign).
- Full document/report table redesign (canvas: url/domain/summary/body/relevance) — later; now only the
  FK column changes.

## What was done

- **models/query.py**: rewritten as link table — code(25) PK, research_code FK→research_index,
  area_code FK→research_area (both CASCADE), search_code String(25) (soft-ref, no FK), query Text,
  created_at. `unique(area_code, search_code)` + indexes. Dropped id/status/text/updated_at.
- **models/document.py, models/report.py**: query_id(int FK→research_query.id) → query_code(String(25)
  FK→research_query.code); unique/index renamed.
- **migrations/rem_006_query_link.py** (forward-only, down=rem_005): drops report/document/query (empty),
  recreates query (link) + document/report (query_code FK). Applied via `migrate upgrade` — no rebuild.
- **crud/query.py**: rewritten — `query_code()`=RQ_<random>, `query_create(research_code, area_code,
  search_code, query)`, `query_get(code)`, `query_list_by_research`, `query_list_by_area`,
  `query_count_by_research_codes`. Dropped query_create_many.
- **crud/document.py, crud/report.py**: query_id → query_code.
- **dto.py**: ResearchQueryRow = code/research_code/area_code/search_code/query/created_at (no id/status/
  text/updated_at); ResearchDocumentRow.query_code, ResearchReportRow.query_code.
- **api.py**: get_query(query_code); document/report lookups by query_code.
- **mcp**: research.py `research_add_queries` → `query_link(research_code, area_code, search_code, query)`
  (+ research_get now returns areas too); document.py/report.py query_id → query_code; instructions rewritten
  (query = post-hoc link; new typical flow). 20 tools; `query_link` in, `research_add_queries` out.
- **constants.py**: removed QUERY_* statuses + sql_in (unused now) — only AREA_* remain.
- **bench** seed_queues_research.py: new flow (research → 1 area → per query `query_create` with fake WQ_
  search_code → documents by query_code → report by query_code); dropped status set.

## Verification

- Dev empty (0 rows) → clean restructure. `migrate check` up to date; PRAGMA confirms research_query 6-field
  link schema + document/report query_code.
- Smoke: RQ_ code, research/area/search bound; document/report reference query_code; list by research/area;
  `unique(area_code, search_code)` raises IntegrityError on dup.
- `uv run pytest --core` — 266 passed; `vue-tsc --noEmit` — EXIT 0; MCP registers query_link (20 tools).

## Problems

None. FK dependency (document/report → research_query.id) forced their FK rewire to query_code in the same
migration; safe because all research tables were empty.

## Result

research_query is now a link table (RQ_): research + area + web_search run (search_code), created post-hoc.
Documents/reports hang off it by query_code. MCP `query_link` replaces the old planning tool.
Deferred: frontend query views (own TS types → tsc green, but nav/shape stale — redo with the frontend
redesign); full document/report table redesign (canvas: url/domain/summary/body/relevance); 3-letter prefix
task; `web/dist` rebuild.
