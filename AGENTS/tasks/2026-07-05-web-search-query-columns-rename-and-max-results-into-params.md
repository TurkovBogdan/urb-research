---
title: web_search — query-колонки search_engine/fetch_engine/error, max_results в params
date: 2026-07-05
status: completed
description: "Renamed web_search_query columns: search_provider→search_engine, content_provider→fetch_engine, error_code→error; dropped the standalone max_results column (now folded into params JSON via SearchRequest.to_params). Follow-up: web_search_page.error_code→error too (symmetry). Settings keys (search_provider/content_provider) and searcher helpers (active_*) left unchanged — they name the runtime settings, not the columns."
tags: [web_search, models, migrations, dto, frontend, rename]
---

## Task

«`models/query.py`: search_engine, fetch_engine, error_code = error, max_results скрываем в params.»

## What was done

- model `query.py` — `search_provider`→`search_engine`, `content_provider`→`fetch_engine`,
  `error_code`→`error`; убрана колонка `max_results` (+ `Integer` из импортов); докстринг переписан
  (заодно снят устаревший `processing`/`empty`).
- migration `wsm_001_query` — те же переименования колонок + удалена `max_results`.
- `providers/request.py` — `to_params()` теперь кладёт `max_results` в params; `from_stored(query, params)`
  читает `max_results` из params (сигнатура без отдельного аргумента).
- crud `query.py` — `query_create(*, search_engine, fetch_engine, query, params)` (без `max_results`);
  `query_finish`/`query_mark_error` пишут колонку `error`; `query_mark_error(*, error=…)`; фильтр
  `_query_filtered`/`query_list`/`query_count` — параметр `search_engine`.
- dto `QueryRow` — `search_engine`/`fetch_engine`/`error`, убран `max_results`.
- `api.py` — фильтр `GET /queries` параметр `search_provider`→`search_engine`.
- `services/searcher.py` — `query_create(search_engine=…, fetch_engine=…, params=to_params())`;
  `query_mark_error(error=…)` (2 места); докстринг `error="search_provider_disabled"`.
- tests — crud/api/save/search: query_create kwargs, `query.search_engine`/`fetch_engine`/`error`,
  фильтры `search_engine`, `query_mark_error(error=…)`. Page-тесты (`error_code`) не тронуты.
- dev sqlite rebuild (drop+create_all трёх таблиц, guarded) — новые колонки.
- frontend — `api.ts` (`QueryRow`: search_engine/fetch_engine/error, без max_results; `ListQueriesParams.search_engine`),
  `queries.store.ts` (`searchProvider`→`searchEngine`, param `search_engine`), `QueriesView.vue`
  (колонки/фильтр/чип/i18n-ключи), `QueryView.vue` (поля/i18n-ключи), `locales/ru.json`
  (`col`/`field`/`filter`: `search_engine`/`fetch_engine`, лейбл fetch = «Движок контента»).
- docs/memory обновлены.

Не тронуто намеренно: настройки `search_provider`/`content_provider` (`settings.py`) и хелперы
`active_search_provider`/`active_content_provider` — это ключи runtime-настроек, не колонки.

### Follow-up: page.error_code → error (симметрично)
По следующему запросу переименовал и на `web_search_page`: колонка `error_code`→`error`
(model + migration `wsm_002` + `crud.page_set_content`/`page_set_error(*, error=…)` + dto `PageRow`
+ `searcher._fetch_pages` вызовы + тесты + фронт `api.ts`/`PageView.vue`). Теперь `error` — и на
query, и на page. Настройки `*_provider` по-прежнему не тронуты.

## Verification

- `uv run pytest --module=web_search` → 41 passed; full `uv run pytest` → 313 passed.
- `migrate check` → up to date; dev sqlite `web_search_query` = code/search_engine/fetch_engine/status/query/params/error/…;
  `web_search_page` = code/status/domain/url/content_hash/content/error/fetched_at/…
- `vue-tsc --noEmit` → 0.
