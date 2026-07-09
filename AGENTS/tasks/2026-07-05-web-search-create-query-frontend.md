---
title: web_search — создание запроса с фронта (fire-and-forget) + выбор движков и страниц
date: 2026-07-05
status: completed
description: "Форма создания поискового запроса на странице /web-search/queries: текст + выбор движка поиска и движка контента + число страниц. Бэк: POST /queries (fire-and-forget через Searcher.submit — 202 + pending сразу, прогон в фоне asyncio.create_task) + GET /engines (доступные движки по ролям + дефолты). Фронт: кнопка «Создать запрос» → VDialog с формой, стор.create → обновление списка."
tags: [web_search, frontend, api, searcher]
---

## Задача

«Список запросов + возможность создать запрос на фронте, с указанием кол-ва страниц и
выбором движков (поиска и получения).» Режим — **fire-and-forget** (клиент не ждёт, сразу в фон).

## Бэк

- `services/searcher.py` — `Searcher.submit(query, *, search_engine=None, fetch_engine=None,
  max_results=None, …)`: `_prepare` (резолв движков → `KeyError` до создания строки → `query_create`
  `pending`) → `_schedule(_run(...))` (фон `asyncio.create_task`, ссылки в `_BACKGROUND_TASKS`
  чтобы task не собрался GC) → возвращает `pending`-строку **сразу**. Общие `_prepare`/`_run`
  вынесены из `search` (блокирующий остаётся для MCP/тестов).
- `api.py` — `POST /queries` (`CreateQueryBody`: query непустой ≤2000, движки/`max_results` 1..50
  опциональны) → `Searcher.submit` → **202** + `QueryRow` (неизвестный движок → `KeyError`→**400**).
  `GET /engines` → `EnginesInfo` (`search`/`fetch` = `Searcher.*_engines()` доступные + дефолты
  `settings.*_engine()`).

## Фронт (`web/src/features/web_search`)

- `api.ts` — `createQuery`/`listEngines` + типы `CreateQueryBody`/`EnginesInfo`.
- `stores/queries.store.ts` — `engines` (грузятся раз), `creating`, `loadEngines()`, `create()`
  (POST → resetPage → load).
- `views/QueriesView.vue` — кнопка «Создать запрос» в шапке → `VDialog`: `VTextarea` (запрос,
  autofocus, Enter=submit) + два `VSelect` (движки из `/engines`, преселект дефолта) + `VTextField`
  число страниц 1..50 (дефолт 10); submit `:loading=creating`, `:disabled` если пусто; ошибка в
  алерте диалога. `onActivated` грузит и список, и движки.
- i18n `ru.json` — `action.create` + блок `query.create.*`.

## Проверка

- `--module=web_search` 56 / полный `uv run pytest` → **328 passed** (+5: submit, POST happy/validation/unknown-engine, GET engines).
- `vue-tsc --noEmit` EXIT=0.
- Docs + MEMORY обновлены.

## Не сделано (вне scope)

- `web/dist` не пересобран — dev идёт через Vite (:12100); прод-сборка при наличии pnpm отдельно.
- Автополлинг статуса pending→done не делали — прогресс по кнопке «Обновить» (можно добавить позже).
