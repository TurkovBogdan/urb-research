---
title: web_search — четыре статуса на роль (SEARCH_STATUS_* / FETCH_STATUS_*)
date: 2026-07-05
status: completed
description: "Reworked table statuses to one 4-state machine (pending → processing → done | error), split into two role-prefixed sets: SEARCH_STATUS_* (web_search_query) and FETCH_STATUS_* (web_search_page). Dropped `empty` (query: no results = done) and `fetched` (page done = done). Added pending→processing transition to both entities (query_mark_processing, pages_mark_processing)."
tags: [web_search, statuses, refactor, migrations, frontend]
---

## Task

«Подумать над статусами (flow сильно поменялся), нужно четыре: ожидание, обрабатывается,
выполнено, ошибка. Константы переделать под роли SEARCH_STATUS_ / FETCH_STATUS_.»

## Design

- Одна машина состояний для обеих таблиц: `pending → processing → done | error`
  (терминально, без повторов — очереди/ретраев нет).
- Два набора констант по ролям модуля (search vs fetch): `SEARCH_STATUS_*` для прогона
  поиска (`web_search_query`), `FETCH_STATUS_*` для получения контента (`web_search_page`).
- Убраны `empty` (пустая выдача = `done`, «нашлось 0» видно по числу результатов) и
  `fetched` (контент получен = `done`).
- Добавлен реальный переход `pending → processing`: `query` создаётся в `pending`, searcher
  зовёт `query_mark_processing`; страницы батча помечаются `pages_mark_processing` перед фетчем.

## What was done

- `constants.py` — переписан: `SEARCH_STATUS_{PENDING,PROCESSING,DONE,ERROR}` + `SEARCH_STATUSES`,
  `FETCH_STATUS_{…}` + `FETCH_STATUSES`, `sql_in`. Старые `SEARCH_*`/`PAGE_*` удалены.
- models `query.py`/`page.py` — default `*_STATUS_PENDING`, CHECK over `SEARCH_STATUSES`/`FETCH_STATUSES`.
- crud `query.py` — create → `pending`; новый `query_mark_processing`; `query_finish(code)` без
  параметра `status` (всегда `done`, ветка `empty` убрана); `query_mark_error` → `SEARCH_STATUS_ERROR`.
- crud `page.py` — новый `pages_mark_processing(codes)` (батч-UPDATE `IN`); `page_set_content` → `done`;
  `page_set_error` → `FETCH_STATUS_ERROR`.
- `services/searcher.py` — после create зовёт `query_mark_processing`; `_fetch_pages` метит батч
  `pages_mark_processing` перед фетчем; финал `query_finish(row.code)` (без empty). `error_code="empty"`
  на странице оставлен — это диагностический код «контент не пришёл», не статус.
- `services/save.py` — `FETCH_STATUS_PENDING`.
- migrations `wsm_001_query` (server_default `pending`, CHECK `pending/processing/done/error`) и
  `wsm_002_page` (CHECK `pending/processing/done/error`) — правки на месте (модуль до прода).
- dev sqlite: DROP+create_all трёх `web_search_*` таблиц (guarded: sqlite + `app.sqlite3`), т.к.
  create_all не ALTERит существующие CHECK. Проверено: обе таблицы теперь с новым CHECK.
- tests — `test_crud` (mark_processing вместо empty/reject-тестов, `*_STATUS_*`), `test_save`,
  `test_search` (`test_search_no_results_marks_done`), `test_api` (`FETCH_STATUS_DONE`).
- frontend — `api.ts` типы `QueryStatus`/`PageStatus` = pending|processing|done|error; `labels.ts`
  цвета + списки (pending=muted, processing=accent, done=success, error); `locales/ru.json` (query:
  Ожидает/Выполняется/Готово/Ошибка; page: Ожидает/Получение/Получено/Ошибка).
- docs/memory — `docs/web_search/INDEX.md` + MEMORY web_search строка: новая машина статусов,
  два набора, `query_mark_processing`/`pages_mark_processing`, `query_finish` без empty.

## Verification

- `uv run pytest --module=web_search` → 39 passed; full `uv run pytest` → 311 passed.
- `migrate check` → up to date (heads unchanged — правки контента миграций, не ревизий).
- `vue-tsc --noEmit` → 0 ошибок.
- dev sqlite: `ck_web_search_query_status` и `ck_web_search_page_status` = `('pending','processing','done','error')`.
