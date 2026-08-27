---
title: Study — task system and content-fetch statuses
date: 2026-08-27
status: completed
description: "Onboarding study of the project with emphasis on the scheduler/task system and on the fetch-status machines (web_search page/query + research source)."
tags: [study, scheduler, web_search, research]
---

## Task

«Изучи проект, особый упор в систему задач и статусы получения контента.»

## Context

Read-only study session. Records read: `CLAUDE.md`, `AGENTS/docs/INDEX.md`, `AGENTS/tasks/INDEX.md`,
`AGENTS/tools/INDEX.md`, task `2026-08-27-web-search-fetch-failures-invisible.md`. Code read:
`src/core/scheduler/*`, `src/core/tasks/heartbeat_task.py`, `src/modules/web_search/{constants,module}.py`,
`services/searcher.py`, `src/modules/research/{constants}.py`, `mcp/{research,source_document}.py`.

## What was done

Diagnosis/notes only, no code changed. Findings worth keeping:

**Task system (scheduler).** Full machinery exists in `src/core/scheduler/` (registry + cron ticker +
runner with task-lock, heartbeat, zombie cleanup, partial-unique index on `(module, code) WHERE
status='running'`), but the registry currently holds exactly **one** task — `core/heartbeat`
(`src/core/tasks/heartbeat_task.py`, `* * * * *`). No domain module registers a task: `web_search`
explicitly runs synchronously (`module.py` docstring, no `configure()`), so the search/fetch pipeline
has no queue, no retries and no reaper task. `core_monitoring` is a read-only UI over `core_tasks` /
`core_tasks_logs`. Dev DB confirms: `core_tasks` = heartbeat/success × 2642, nothing else.

**Status machines — three, in two modules.**
- `web_search_query.status` (`SEARCH_STATUS_*`) and `web_search_page.status` (`FETCH_STATUS_*`) share
  `pending → processing → done | error`; both terminal, no retry.
- `research_source_document.status` (`DOC_*` = `error | pending | kept | filtered`) is a different
  axis — review state, bridged to the fetch machine by `_initial_source_status(page)`
  (`research/mcp/research.py`) and by `source_document_revive_by_pages` after `sources_refetch`.
- The only self-healing paths: `_store_results` now hands `error` pages back to the fetch step on a
  repeat search, and `Searcher.refetch` / MCP `sources_refetch`. Queries have an inline reaper
  (`query_expire_stale`, 15 min stale `processing`); pages have none.

**Live state of the dev DB (2026-08-27).** Pages: 3119 `error/ConnectError/web_scrapper`, 188
`error/empty`, 464 `done/web_scrapper`, 548 `done/firecrawl`, 17 `error` on firecrawl. Sources: 3857
`error` / 862 `kept` / 579 `filtered` / 24 `pending` — i.e. the `rem_008` backfill is in place.
Queries: 1104 `done`, 43 `error` (mostly xai HTTP/timeout, 3 `stale`), 23 `pending`, 1 stuck
`processing`.

**Changed since the diagnosis task was written:** the `web_scrapper` daemon on 127.0.0.1:19020 is now
**up** (answers, 404 on `/`), and pages fetched on 2026-08-27 are `done` (4) with one `empty`; the last
`ConnectError` burst is 2026-08-26 (49 pages). So the failure cause is gone, but the ~3.1k historic
`error` pages still need `sources_refetch` per research to revive.

## Result

No files changed. Open items observed (not acted on): 23 `pending` + 1 `processing` query rows are
orphans of dead processes with no reaper for `pending`; the historic `error` backlog is only revivable
by an explicit per-research `sources_refetch`.
