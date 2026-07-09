---
title: web_search — drop retry machinery + scheduler tasks (synchronous execution)
date: 2026-07-05
status: completed  # in-work | completed | deferred
description: "Simplify web_search: remove all retry logic (error_count/error_at/backoff/max_attempts/retry+fail statuses/claim+reclaim) and the two scheduler tasks (run_searches/fetch_pages). Execution becomes synchronous — a service call runs search+fetch inline and returns the finished query. Failure → terminal `error` status (no retries), exception NOT propagated; single `error_code` column kept."
tags: [web_search, refactor, synchronous, remove-tasks]
---

## Task

«убираем логику ретраев, убираем задачи» + confirmed: execution синхронно по вызову;
сбой → терминальный статус `error` (без повторов, `error_code` остаётся).

## Target design

- **Execution:** `web_search.services.searcher.search(query, ...)` runs the whole pipeline
  synchronously in one await (provider.search → store → inline fetch of pending pages) and
  returns the finished `WebSearchQuery`. No queue polling, no cron.
- **Statuses:** query = `processing` (in-flight) → `done` | `empty` | `error`. page = `pending`
  (transient in-call) → `fetched` | `error`.
- **Failure:** engine/fetch error → terminal `error` (query or page), NOT re-raised.
- **Removed:** error_count/error_at columns; retry/fail/fetching statuses; backoff+max_attempts
  settings; search_concurrency (task-batch only); `claim_due`/`reclaim_stuck`/`mark_fetching`/
  `finalize_ready`/`_due_predicate`; `ProviderHandler` (queue orchestration); `tasks/` dir;
  `module.configure`/`register_tasks`; `SEARCH_BATCH`.
- **Kept:** `error_code` (nullable) on query+page; `finished_at`; settings provider/default_pages/
  fetch_concurrency; registry now holds `SearchProvider` instances directly (not handlers).

## What was done

- **constants** — statuses trimmed to query `processing/done/empty/error`, page `pending/fetched/error`;
  removed all retry/batch/backoff/attempt constants.
- **models** query/page — dropped `error_count`/`error_at`; kept `error_code`; query default status `processing`.
- **migrations** `wsm_001_query`/`wsm_002_page` — column lists + CHECK updated (retry cols/statuses gone).
- **module_settings** — only `provider`/`fetch_concurrency`/`default_pages` (removed search_concurrency +
  all *_max_attempts/*_retry_backoff).
- **crud/query** — kept create/get/list/count/finish; `query_mark_error` simplified (terminal `error`,
  no counters); removed claim/reclaim/mark_fetching/finalize_ready/_due_predicate.
- **crud/page** — `page_set_error` (terminal) replaces `page_mark_error`; removed claim/reclaim/list_by_status.
- **crud/result** — removed `nonterminal_page_count`.
- **services/save** — `store_results` returns pending pages (those needing fetch).
- **services/searcher** — `enqueue` → synchronous `search()` running the full pipeline (create→search→store→
  inline fetch→finalize), returns finished query; `_fetch_pages` helper (batched, `fetch_concurrency` semaphore).
- **providers** — `ProviderHandler` deleted; registry holds `SearchProvider` instances;
  `tavily/firecrawl/__init__` register the provider directly; `handlers.py` removed.
- **tasks/** dir removed; `module.py` `configure`/`register_tasks` removed.
- **dto** — `QueryRow`/`PageRow` drop `error_count`/`error_at`.
- **tests** — removed `test_provider_handler.py` + `test_tasks.py`; added `test_search.py` (synchronous
  pipeline: done/empty/error, inline + deferred fetch, page error); rewrote crud/save/searcher tests.
- **frontend** (subagent): status label/color sets trimmed to `processing/done/empty/error` +
  `pending/fetched/error`; api types dropped `error_count`/`error_at`; build PASS.
- **docs/memory** (subagent): web_search INDEX + MEMORY router rewritten to the synchronous model.

## Verification

- `uv run pytest` → **311 passed**; `migrate check` heads match; fresh-sqlite AlembicRunner applies —
  `web_search_query`/`web_search_page` have no `error_count`/`error_at`.
- Dev sqlite rebuilt (dropped stale web_search_* with old cols, create_all rebuilt trimmed schema).

## Result

Done. `web_search` is now a synchronous library: `services.searcher.search()` runs search+fetch inline
and returns the finished query; no queue, no scheduler tasks, no retries (terminal `error` status +
`error_code`). Statuses: query `processing/done/empty/error`, page `pending/fetched/error`.
`ProviderHandler` removed (registry holds `SearchProvider`). Full suite green after this step (311 passed);
superseded by the follow-up string-PK task. See [2026-07-05-web-search-string-pk-codes].
