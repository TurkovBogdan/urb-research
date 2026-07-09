---
title: web_search frontend — click-sort data tables + relative dates
date: 2026-07-05
status: completed
description: "Bring the web_search list views up to the conversations data-table standard: server-side click-to-sort columns and two-line dates (absolute + relative). Adds a sort_by whitelist to the backend list endpoints."
tags: [web_search, frontend, api]
---

## Task

«Фронт веб поиска, нужно его обновить под текущие модели и данные.» Плюс: в таблицах
использовать фронтовую утилиту относительных дат («сколько времени прошло»); таблицы —
data table с пагинацией и **сортировкой по клику** (эталон — `AGENTS/semaphore-core/web/src/features/conversations`).

## Context

Фронтовые типы (`QueryRow`/`PageRow`/`QueryResultView`) уже совпадали с бэкенд-DTO —
рассинхрона моделей не было. Реальные пробелы против эталона conversations: (1) сортировка
была кнопкой-тумблером направления, все заголовки `sortable: false`; (2) даты только
абсолютные (`fmtDateTime`), без относительной строки; (3) бэкенд умел лишь `sort_dir`,
колонка захардкожена в `created_at` (нет `sort_by`). Утилита относительных дат уже есть —
`web/src/shared/utils/date.ts::fmtRelative` («5 минут назад»).

Выбран (моя рекомендация, пользователь не ответил на уточнение) вариант с серверным
`sort_by`, как в conversations.

## What was done

**Бэкенд (без миграций):**
- `crud/query.py` — белый список `QUERY_SORT_COLUMNS` (`created_at`/`finished_at`/`status`/`search_engine`/`fetch_engine`/`query`); `query_list` получил параметр `sort_by` (неизвестный ключ → дефолт `created_at`; dict-lookup = защита от инъекции), `code` — тайбрейк в ту же сторону.
- `crud/page.py` — аналогично `PAGE_SORT_COLUMNS` (`created_at`/`fetched_at`/`status`/`domain`/`url`).
- `api.py` — оба листинга (`GET /queries`, `GET /pages`) получили `sort_by: str = Query("created_at")`, прокинут в CRUD.

**Фронт:**
- `api.ts` — `sort_by?: string` в `ListQueriesParams`/`ListPagesParams`.
- `stores/queries.store.ts`, `stores/pages.store.ts` — новый `sortBy` (default `created_at`), прокинут в `load()`.
- `views/QueriesView.vue`, `views/PagesView.vue` — убрана кнопка-тумблер; заголовки `sortable: true`; `VDataTable` с `:sort-by`, `must-sort`, `@update:sort-by="onUpdateSortBy"` (→ стор + reload); даты в две строки (`fmtDateTime` + `fmtRelative`, класс `.date-rel`); сетка фильтров без колонки под кнопку. В таблицу страниц добавлена колонка «Создана» (`created_at`) — дефолтная сортировка теперь видна.
- `locales/ru.json` — добавлен `page.col.created_at`; удалён неиспользуемый блок `sort` (newest/oldest).

**Тесты:** `tests/modules/web_search/test_api.py` +2 — `test_list_queries_sorts_by_whitelisted_column` (asc/desc по `search_engine`) и `test_list_queries_unknown_sort_by_falls_back` (мусорный `sort_by` → 200, дефолт, без инъекции).

## Result

Таблицы web_search сортируются кликом по заголовку (server-side) и показывают
относительное время — как conversations. `uv run pytest --module=web_search` 51 passed;
`web/node_modules/.bin/vue-tsc --noEmit` EXIT=0. `web/dist` не пересобирался (нет pnpm на PATH).
Изменённые файлы: `src/modules/web_search/{crud/query.py,crud/page.py,api.py}`,
`web/src/features/web_search/{api.ts,stores/queries.store.ts,stores/pages.store.ts,views/QueriesView.vue,views/PagesView.vue,locales/ru.json}`,
`tests/modules/web_search/test_api.py`, doc `AGENTS/docs/web_search/INDEX.md`.
