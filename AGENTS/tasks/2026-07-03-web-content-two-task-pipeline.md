---
title: web_content — конвейер «регистрация + две задачи» (паттерн mail_sync)
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "searcher только регистрирует запрос; исполнение вынесено в две scheduler-задачи (run_searches, fetch_pages) с ограничением параллелизма через семафор."
tags: [web_content, scheduler, tasks, refactor]
---

## Task

Перевести модуль на паттерн `mail_sync`: `searcher` только **регистрирует** задачу
поиска, а обработка идёт двумя scheduler-задачами — поиск и получение контента, — с
ограничением параллелизма (`search_concurrency`/`fetch_concurrency`).

## Context

Раньше `searcher.run_search` выполнял поиск **синхронно** (провайдер + сохранение);
задача была одна (`fetch_pages`, последовательная); настройки concurrency не
использовались. Статус `processing` уже был заведён, но никем не выставлялся.

## What was done

- **Провайдеры:** `SearchProvider._fetch` → публичный `search(req) -> list[dict]`
  (только вызов движка + нормализация). Убрана оркестрация `SearchProvider.search`
  (создание/сохранение). tavily/firecrawl переименованы. `SearchRequest.from_stored`
  восстанавливает запрос из строки БД.
- **searcher:** `run_search` → `register_search(req)` — снимок активного провайдера +
  `search_create` (строка `pending`), провайдер не вызывается.
- **save:** `save_search_results` → `store_results(search_id, results)` — привязка
  выдачи к существующему запросу + finish (строку не создаёт).
- **Новый `services/search_runner.py`:** `run_pending_searches(limit, concurrency,
  stuck_after_seconds)` — reclaim → claim → `provider.search` с `asyncio.Semaphore` →
  `store_results`; сбой провайдера → `search_mark_pending`.
- **fetcher:** `fetch_due_pages(provider, limit, concurrency, stuck_after_seconds)` —
  reclaim → claim due → фетч с семафором. Счётчики `{reclaimed, claimed, fetched, failed}`.
- **CRUD:** `search`: `search_claim_pending`/`search_reclaim_stuck`/`search_mark_pending`.
  `page`: `page_claim_due`/`page_reclaim_stuck` (due-предикат вынесен в `_due_predicate`);
  `page_list_due_for_fetch` удалён.
- **constants:** `SEARCH_BATCH = 5`.
- **tasks:** новая `RunSearchesTask` (`web_content.run_searches`); `FetchPagesTask`
  переведён на claim/reclaim/семафор. Обе cron `* * * * *`, TTL 300, `USER_REQUEST`.
- **Тесты (обновлены/добавлены):** `test_searcher` (register вместо run), новый
  `test_search_runner` (исполнение done/empty/failed + reclaim), `test_providers`
  (search → нормализованный список, стал pure), `test_save` (store_results),
  `test_fetcher` (новая сигнатура/stats), `test_crud` (page_claim_due, store_results),
  `test_tasks` (обе задачи).

## Result

- Изменены: `constants.py`, `providers/{base,tavily,firecrawl,request}.py`,
  `services/{searcher,save,fetcher}.py` (+ новый `services/search_runner.py`),
  `crud/{search,page}.py`, `tasks/{__init__,fetch_pages_task}.py` (+ новый
  `tasks/run_searches_task.py`); тесты `tests/modules/web_content/*`.
- Обновлены записи: `docs/web_content/INDEX.md`, `memory/MEMORY.md` (строка web_content).
- `uv run pytest --module=web_content` → 41 passed.
- Не сделано (вне запроса): write-триггер `register_search` (MCP/HTTP); search без
  статуса ошибки (сбой → бесконечный ретрай в `pending`, ограничен cron).
