# web_content — rename + tables + crud

- **Date:** 2026-07-01
- **Status:** completed
- **Area:** module / web_content

## Request

Rename module `web_ingestion` → `web_content`; create migrations, models, CRUD and everything needed to save the three core tables (`web_content_search` → `web_content_search_result` → `web_content_page`). Reference modules: `AGENTS/semaphore-core/src/modules`. Providers + queue locks deferred to next.

## What was done

- **Rename** `web_ingestion` → `web_content` (mv): module dir, classes (`WebContentModule`/`WebContentConfig`), `build_modules`, bench `dev/bench/web_content/`, docs hub `docs/web_content/INDEX.md`, tests dir, memory routing row, research/bench refs. `core_setup` ENV group «Веб-источники» (`TAVILY_API_KEY`/`FIRECRAWL_API_KEY`) unchanged.
- **Models** `models/{search,page,search_result}.py` — portable types (`timestamp()`/`json_value()` → create_all on sqlite). `id` numeric everywhere; hash `code` only on `web_content_page` (`text_hash(normalize_url)`, unique → dedup by url). `search_result.page_code` FK → `page.code`; `unique(search_id, page_code)`. Status check-constraints. `normalize.py` (url → always https).
- **Migrations** `migrations/versions/wcm_001_search → wcm_002_page → wcm_003_search_result`, per the `conversations` ГОСТ; `module.py` has `migrations_dir`. **Dialect-agnostic types**: switched from `postgresql.JSONB`/`TIMESTAMP` to portable `json_value()`/`timestamp()` (`core/database/types.py`, `.with_variant`) — so `migrate upgrade` runs on **both SQLite and Postgres** (core `com_001..005` converted the same way). Verified: `migrate upgrade` on fresh SQLite builds full schema + `migrate check` up-to-date; PG parity (`compare_metadata`) still passes (PG cols stay `jsonb`/`timestamp`). NB: app lifespan on sqlite still uses `create_all` (runtime mechanism unchanged — flipping it to Alembic is a separate decision).
- **CRUD** per entity (`crud/{search,page,search_result}.py` + `_upsert.py` dialect insert) — own-session pattern. `services/save.py::save_search_results` (search → page(pending) per url → result → finish done/empty), provider-agnostic.
- **Providers** `providers/` (pattern: `conversations/importers`) — `base.SearchProvider.search(request, **params)` runs the chain (`_fetch` → `save_search_results`); subclass implements `_fetch` (engine call → normalized `[{url,rank?,score?,meta?}]`, ignores foreign params). `registry` (`register`/`get`/`codes`), concrete `tavily.py` + `firecrawl.py` (async httpx, key from `WebContentConfig`). Verified **live** end-to-end (both providers: search=done, pages pending, https-normalized).
- **Pipeline entry points** — `module_settings.SCHEMA` `ChoiceField provider` (tavily|firecrawl, active read via `get_module_store`); `services/searcher.run_search(req)` (active provider → `provider.search`); provider `fetch_page(url)` (Tavily `/extract`, Firecrawl `/v2/scrape`); `services/fetcher.fetch_due_pages` (pending + retry-after-backoff → fetched/retry/fail, `FETCH_MAX_ATTEMPTS`); scheduler task `web_content.fetch_pages` (`CoreTaskBase`, cron `* * * * *`, TTL 300, single-instance via core task-lock) registered in `configure()`. `page_mark_error` → fail after max; `page_list_due_for_fetch` (backoff).
- **Tests** `tests/modules/web_content/` — config + crud + save + providers + searcher + fetcher + tasks (registry). `--module=web_content` → 26 passed.
- **Live full pipeline** verified (temp sqlite): `run_search`(tavily) → 3 pages pending → `fetch_due_pages` → 2 fetched (content + content_hash), 1 retry.

## Verification

- `build_modules` → `[core_setup, web_content]`; models register 3 tables; `create_all` (SQLite) builds the schema; `--module=web_content` → 17 passed (config + crud + save on in-memory SQLite).

## Follow-ups done

- **Seconds-precision timestamps:** `core/utils/date.py::utc_now()` now `.replace(microsecond=0)` — DB storage second-precise on both providers (PG already truncated via `TIMESTAMP(precision=0)`; SQLite ignored the variant). Verified: insert via app → `2026-06-30 23:39:06` (no microseconds). `docs/platform/dates.md` updated (portable `timestamp()` in models+migrations; truncation note).
- **Migration execution verified both providers:** `migrate upgrade` on fresh SQLite (applied + `check` up-to-date) and on ephemeral Postgres (both heads in `alembic_version`). 296 tests pass.

## Next (deferred, per user)

- External trigger for `run_search` (MCP tool / HTTP route) + reading results out; currently programmatic only.
- In dev the `fetch_pages` task runs only with `WORKER_ENABLED=true` (embedded worker) or a worker process.
- `search` reuse/TTL (no dedup → repeated query = new provider call); re-fetch TTL for `fetched` pages.
- Vector layer (recall) over `web_content_page.content`.
