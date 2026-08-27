---
title: Project study (onboarding refresh)
date: 2026-08-27
status: completed
description: "Re-read the project records (CLAUDE.md, MEMORY, tasks, docs, tools) and walked the source tree to rebuild a working picture of the platform, modules and MCP surface. No code changed."
tags: [onboarding, docs]
---

## Task

«Изучи проект @CLAUDE.md» — study the project.

## Context

A prior onboarding pass exists (`2026-08-26-project-onboarding-study.md`). This session refreshes it
after the markdown/typography work landed in the working tree.

## What was done

- Read the session-start set: `CLAUDE.md`, `AGENTS/memory/MEMORY.md`, `AGENTS/tasks/INDEX.md`,
  `AGENTS/docs/INDEX.md`, `AGENTS/docs/workflow/testing.md`, `AGENTS/tools/INDEX.md`, `README.md`.
- Walked `src/` (188 py files): `app.py` roles, `core/` platform layers (router zones, settings,
  scheduler, mcp, database), the six modules from `apps/app/modules.py::build_modules`.
- Read `src/core/module.py` (lifecycle + declarative attrs) and
  `src/modules/research/mcp/__init__.py` (agent instructions; 23 `@mcp.tool` confirmed by grep).
- Checked connector/web_search settings keys; frontend features (7 dirs under `web/src/features`).
- Ran `uv run pytest -q` — **446 passed** (pure + db, in-memory sqlite).

## Schema study (second pass)

Read all ORM models (`research/models/*`, `web_search/models/*`, `core/models/*`), the code-prefix
and status constants, and the manual-cascade CRUD deletes; cross-checked against the live dev
sqlite (`AGENTS/tools/dev-query.sh`).

- 14 tables: 5 core (`core_tasks`, `core_tasks_logs`, `core_locks`, `core_modules_settings`,
  `core_modules_state`) + 5 research + 3 web_search + `alembic_version`.
- Research chain `research_index → research_area → research_source_query → research_source_document`
  is hard FK with `ondelete=CASCADE`; `research_note` hangs off `research_index` only.
  Every research row also denormalises `research_code` (and the document also `area_code`), so a
  source can be listed by research / area / query without walking the chain.
- The two module graphs are joined by **two soft refs, no FK**: `research_source_query.search_code`
  → `web_search_query.code` and `research_source_document.page_code` → `web_search_page.code`.
  `research` owns the presentation prefixes for both (`SEARCH@` / `PAGE@`).
- Live integrity: 0 orphans on both soft refs.
- Row counts (dev): research 41 / area 291 / note 232 / source_query 1059 / source_document 5311
  (kept 3268, filtered 1954, **pending 89**) / web query 1168 / page 4331 / result 5893.
- 🔴 **3323 of 4331 `web_search_page` rows are `status='error'` with `body IS NULL`** (77%) — only
  1008 pages ever got content. This is the concrete cause of the "sources come back with empty
  body" symptom flagged in the research tasks (2026-08-26). Fetch is terminal, no retries, so those
  pages stay empty forever; a reviewed source pointing at one has nothing to read.
- 109 `web_search_query` runs are not referenced by any `research_source_query` (standalone searches
  from the web UI) — expected, the module is usable on its own.

## Result

No files changed. Current-state observations:

- Git history is 5 commits (fresh public init), but the working tree carries a large uncommitted
  diff — 315 changed paths, incl. `AGENTS/**`, `dev/.run/*.xml`, `pyproject.toml`, `uv.lock`,
  `src/core/app_factory.py`, `tests/core/*` and a wholesale `web/dist/` rebuild. Multiple tasks'
  work is mixed in there → the commit protocol's "stage only your own files" rule is load-bearing.
- `AGENTS/memory/MEMORY.md` is still 30.1 KB against a 24.4 KB limit → it loads **partially** every
  session (the harness warns). The routing rows for `core_connectors` and `web_search` are
  paragraph-sized; they belong in the module doc hubs.
- `research` still has no doc hub `AGENTS/docs/research/INDEX.md` — the only module without one,
  and it is the module that owns the MCP surface.
- `AGENTS/tasks/INDEX.md` "In work" table holds rows whose bodies say **Completed** (the same drift
  the previous onboarding flagged).
- `AGENTS/tools/stop-all.sh` still kills by `pkill -f 'app\.py'` — it will take down the
  neighbouring `urb-research-stable` instance too.

## Refresh pass (same day, after the groups work landed in the tree)

Re-walked `src/` + `CLAUDE.md` on the user's request. Deltas against the pass above:

- Tree grew to **194 py files**; `research` is the heaviest module (~3.9k lines), then `web_search`
  (~2.1k) and `core_connectors` (~1.4k); `src/core` ~5.4k.
- **MCP surface is 29 tools, not 23** — the `research_group` surface (`mcp/group.py`:
  `group_create/list/get/update/delete` + `group_icons`) landed uncommitted, plus `rem_006_group`
  and `rem_007_research_group_code` (nullable `research_index.group_code`). `CLAUDE.md` and the
  memory router still say «23 MCP tools» → stale.
- Instructions in `mcp/__init__.py` now document groups as explicitly optional/cosmetic filing
  ("leave a research ungrouped unless the user asked for shelves").
- `uv run pytest -q` — **529 passed** in ~10 s (was 446).
- `research/models/` is 6 ORM classes now (`ResearchGroup` added); research tables = 6.
- Still open from the pass above: oversized `MEMORY.md`, missing `docs/research/INDEX.md`,
  Completed rows sitting in the "In work" table, unscoped `stop-all.sh`.

## Third pass (same day, after the delete-routes work landed)

Re-read `CLAUDE.md` + the session-start set, re-walked the tree. Deltas against the refresh pass:

- Suite is **552 passed** (~12 s), up from 529 — `tests/modules/research/test_api.py` (delete routes)
  and `test_references.py` are new and uncommitted.
- MCP surface confirmed at **29** `@mcp.tool` (research 5 + area 4 + note 5 + source 3 + query 3 +
  body 2 + group 6 + delete verbs). `CLAUDE.md` line 5 and the memory router still claim 23 → stale.
- Research migration chain is `rem_001..rem_007`; `research/models/` = 6 ORM classes; web_search
  `wsm_001..003`; core `com_001..005` — three independent Alembic heads, unchanged.
- Working tree is now **478** changed paths (was 315): the whole `web/dist/` rebuild, 15 untracked
  task files, the `research_group` code, and `AGENTS/semaphore-core/` (untracked directory).
- Open thread from `2026-08-27-research-user-delete-routes.md`: four `DELETE` routes exist on
  `/internal/research`, but the frontend has no wiring (`api.ts`, buttons, `web/dist`).
- No records or code changed by this pass.

## Fourth pass (same day, after the refetch/interface work landed)

Re-read `CLAUDE.md` + the session-start set, re-walked the tree. Deltas against the third pass:

- Suite is **580 passed** (~10 s), up from 552.
- MCP surface is **31** `@mcp.tool` (was 29): `sources_refetch` (re-download the material for
  `error` sources under a SOURCE@/QUERY@/AREA@/RESEARCH@ code — fetch only, no re-search) and
  `interface_open` (any code → app page url, opened in the user's browser via `webbrowser`;
  research routes carry the prefixed code, web_search routes the bare hash). `CLAUDE.md` line 5
  and the memory router still say «23 MCP tools» → stale by 8.
- New files since the third pass: `mcp/interface.py`, `mcp/auth.py` (draft static-token resolver
  off `Config.mcp_token`; empty token = allow-all local mode), `crud/references.py`,
  `migrations/versions/rem_008_source_doc_error_status.py`. `src/` is 196 py files.
- Research chain is `rem_001..rem_008`; web_search `wsm_001..003`; core `com_001..005` — still
  three independent Alembic heads.
- The `2026-08-27-web-search-fetch-failures-invisible` thread has visibly moved: `error` is now a
  real source status with a repair verb (`sources_refetch`) and the MCP instructions spell out that
  a failed fetch is terminal and `summary` is not the material.
- Working tree carries **509** changed/untracked paths from several tasks at once (5 commits of
  history) — the "stage only your own files" rule stays load-bearing.
- Still open: oversized `MEMORY.md` (loads partially every session), missing
  `AGENTS/docs/research/INDEX.md` for the module that owns the MCP surface, Completed rows sitting
  in the "In work" table, unscoped `stop-all.sh` (`pkill -f 'app\.py'` kills the neighbouring
  stable instance).
- No records or code changed by this pass.

## Fifth pass (same day, re-study on request)

Re-read `CLAUDE.md` + the session-start set, re-walked the tree. The structural picture is
unchanged against the fourth pass — `src/` is still 196 py files, the MCP surface still **31**
`@mcp.tool` across 7 registrars (group/research/area/source_document/note/body/interface), the
Alembic chains are still `com_001..005` / `wsm_001..003` / `rem_001..008` on three independent
heads, `build_modules()` still returns the same six modules, and `web/src/features/` still holds
seven features (one per module + `settings`).

Deltas:

- Suite is **599 passed** (~17 s), up from 580 — 58 `test_*.py` files.
- Working tree carries **513** changed/untracked paths (was 509) against 5 commits of history; the
  uncommitted `research_group` + `interface_open` code and 18 untracked task files are still in it,
  plus the untracked `AGENTS/semaphore-core/` directory.
- Every open item from the earlier passes still stands: `MEMORY.md` over the 24.4 KB budget (loads
  partially, the `core_connectors` / `web_search` router rows are paragraph-sized), no
  `AGENTS/docs/research/INDEX.md`, `CLAUDE.md` line 5 and the memory router still claim «23 MCP
  tools» (stale by 8), Completed rows parked in the "In work" table, `stop-all.sh` unscoped.
- No records (beyond this entry) or code changed by this pass.

## Sixth pass (same day, re-study on request)

Re-read `CLAUDE.md` + the session-start set (`MEMORY.md`, `tasks/INDEX.md`, `docs/INDEX.md`,
`workflow/testing.md`, `tools/INDEX.md`, `README.md`, `run.sh`), re-walked `src/`. The picture is
identical to the fifth pass — 196 py files, six modules from `build_modules()`, **31** `@mcp.tool`
across the seven registrars (group 6 / research 8 / area 5 / note 5 / source_document 4 / body 2 /
interface 1), Alembic heads `com_001..005` / `wsm_001..003` / `rem_001..008`, seven
`web/src/features/`, suite **599 passed** (~11 s).

Deltas:

- Working tree is **524** changed/untracked paths (was 513) against 5 commits of history; the 120
  `D` entries are all stale `web/dist/` build hashes from rebuilds, not lost source.
- `research_group` (`models/crud/mcp/group.py` + `icons.py` + `test_group_icons.py`) is still
  untracked, while `AGENTS/tasks/2026-08-27-research-groups.md` says «кода нет» → that task row is
  stale against the tree.
- Everything else from the earlier passes stands unchanged: `MEMORY.md` over the 24.4 KB budget
  (loads partially every session), no `AGENTS/docs/research/INDEX.md`, `CLAUDE.md` line 5 + the
  memory router still claim «23 MCP tools» (stale by 8), Completed rows parked in the "In work"
  table, `stop-all.sh` unscoped (`pkill -f 'app\.py'` kills the neighbouring stable instance).
- No records (beyond this entry) or code changed by this pass.

## Seventh pass (same day, re-study on request)

Re-read `CLAUDE.md` + the session-start set, re-walked `src/`, sampled the live dev sqlite.

- `src/` is **199** py files. MCP surface is **30** `@mcp.tool` — `group_icons` was dropped with the
  icon/`sort` arguments (task `2026-08-27-mcp-drop-group-icon`), so the count in `CLAUDE.md` line 5
  («30 MCP tools») is now **correct**; the stale «23» claim is gone from the always-loaded records.
- New since the sixth pass: `research/colors.py` (10-name group palette, mirror of `icons.py`),
  `research/services/search.py` (deep body search — Python-side casefold, deliberately not SQL:
  SQLite `lower()` leaves Cyrillic untouched) and `services/refetch.py`; `rem_006_group` now carries
  a `color` column (edited in place — the only allowed exception, no group table existed anywhere).
- Suite is **638 passed** in ~11 s (was 599). The `sources_refetch(code=)` → `codes=` breakage that
  `2026-08-27-group-color-picker` flagged as 8 failures in the full run is **fixed** — default run
  is green end to end.
- Live dev sqlite (imported from stable on 27.08): research 43 / area 312 / note 248 /
  source_document 5551 / web pages 4566 / **research_group 0** — the colour/group work was verified
  on throwaway rows and left no data behind.
- This checkout's backend is **not running** (`:22040` free); the only live `app.py` is the
  neighbouring `urb-research-stable` on `:22020` plus its stdio shims — another reminder that
  `stop-all.sh` (`pkill -f 'app\.py'`) would kill someone else's instance.
- Working tree: **566** changed/untracked paths (294 `??`, 152 `M`, 120 `D` — the `D` entries are
  stale `web/dist/` hashes) against 5 commits of history.
- Still open: `MEMORY.md` over the 24.4 KB budget (loads partially every session — the
  `core_connectors` / `web_search` router rows are paragraph-sized), no
  `AGENTS/docs/research/INDEX.md` for the module that owns the MCP surface, Completed rows parked in
  the "In work" table, unscoped `stop-all.sh`.
- No records (beyond this entry) or code changed by this pass.
