---
title: Rename module web_content → web_search (+ entity renames)
date: 2026-07-05
status: completed  # in-work | completed | deferred
description: "Rename domain module web_content → web_search — sharpened responsibility = web search + saving fetched pages. Entities renamed: search→query, search_result→result. Backend + frontend + tests + bench + docs."
tags: [web_search, web_content, rename, refactor]
---

## Task

«web_search, давай теперь подумаем про названия моделей и таблиц … Вперёд, проводи рефактор» —
зона ответственности модуля уточнена: **поиск в вебе + сохранение найденных страниц**.
Переименовать `web_content` → `web_search` целиком, консистентно по коду/фронту/тестам/докам.

## Naming map (confirmed with user)

Module `web_content` → **`web_search`**; router prefix `/web-content` → `/web-search`;
module-store key `web_content` → `web_search`.

| Table (old → new) | ORM (old → new) |
|---|---|
| `web_content_search` → `web_search_query` | `WebContentSearch` → `WebSearchQuery` |
| `web_content_page` → `web_search_page` | `WebContentPage` → `WebSearchPage` |
| `web_content_search_result` → `web_search_result` | `WebContentSearchResult` → `WebSearchResult` |

Columns: `web_search_query.request` → **`query`**; `web_search_result.search_id` → **`query_id`**.
Constraints/idx: `ck_web_search_query_status`, `ix_web_search_page_status`,
`uq_web_search_result_query_page`, `ix_web_search_result_query_id`.

Files: `models/search.py`→`query.py`, `models/search_result.py`→`result.py`;
`crud/search.py`→`query.py` (funcs `search_*`→`query_*`), `crud/search_result.py`→`result.py`;
migrations `wcm_00N_*`→`wsm_00N_*` (query/page/result). CRUD `results_with_page_for_search`→
`_for_query`. Service `searcher.register_search` → `enqueue`. Task codes `web_content.*`→`web_search.*`.

## What was done

- **Backend module** `src/modules/web_content` → `src/modules/web_search` (dir + inner files
  `models/search.py`→`query.py`, `models/search_result.py`→`result.py`, `crud/search.py`→
  `query.py`, `crud/search_result.py`→`result.py`, migrations `wcm_*`→`wsm_*`). All ORM/table/
  column/constraint/CRUD-func/DTO/endpoint/service/task-code/store-key renames applied by hand.
  `searcher.register_search`→`enqueue`; task `MODULE="web_search"`; router prefix `/web-search`.
  Registered as `WebSearchModule` in `apps/app/modules.py`. research_registry soft-ref docstrings updated.
- **Tests** `tests/modules/web_content`→`web_search`, all 8 files rewritten to new symbols.
- **Bench** `dev/bench/web_content`→`web_search` (subagent; also repointed the dead `WebContentConfig`
  token source to `core_gateway` runtime settings — key had already moved there).
- **Docs/memory** (subagent): `AGENTS/docs/web_content`→`web_search` INDEX rewritten; `MEMORY.md`
  routing bullet + gotchas; `core_gateway`/`core_setup` cross-refs; `dev-query.sh`; `.env.example.*`.
  Historical `AGENTS/tasks/` + `AGENTS/research/` logs left as-is.
- **Frontend** `web/src/features/web_content`→`web_search` (subagent): views `SearchesView`→
  `QueriesView`, `SearchView`→`QueryView`; stores/types/routes/labels renamed; api base `/web-search`,
  endpoints `/queries`; i18n namespace auto-derives from dir name; nav + settings label = «Веб-поиск».
  `router/index.ts`, `AppSidebar.vue`, `SettingsView.vue` updated. `pnpm build` (vue-tsc + vite) → PASS.
- **env** `.env.example.dev`/`.prod` comment → `web_search`.

## Verification

- `grep web_content` in `src/` → clean; import smoke OK; tables = `web_search_{query,page,result}`.
- `uv run pytest --core --module=web_search` → **314 passed**.
- `migrate check` → heads match (`wsm_003_result`); fresh-sqlite AlembicRunner applies all migrations,
  `web_search_query` has `query` col, `web_search_result` has `query_id`.
- Dev sqlite fixed: dropped orphan `web_content_*` tables + restamped `alembic_version` `wcm_003`→`wsm_003`
  (guarded: assert sqlite + dev path). Gateway API keys preserved.

## Result

Done end-to-end. Module `web_content` → `web_search` across backend / tests / bench / frontend /
docs / memory / env. Full suite `uv run pytest` → **320 passed**; `pnpm build` PASS; `migrate check`
heads match; fresh-sqlite migration apply verified. No `web_content` refs remain outside historical
`AGENTS/tasks/` + `AGENTS/research/` logs (left intact by design). Dev sqlite reconciled (orphan tables
dropped, revision restamped, gateway keys preserved).
