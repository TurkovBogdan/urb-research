---
title: web_content — статус fetching, инлайн-контент, батч-фетч (pages_per_request × concurrency)
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Редизайн конвейера по канвасу: новый статус поиска fetching (ждём контент), завершение по терминальным страницам (fetched|fail), провайдер-атрибут pages_per_request, инлайн-контент при max_results ≤ cap, батч-фетч chunk=pages_per_request × parallel=fetch_concurrency."
tags: [web_content, providers, scheduler, statuses, refactor]
---

## Task

По исправленному канвасу (`second-brain/.../pipeline-web-content.canvas`):
1. Отдельный статус поиска `fetching` (движок отработал, ждём контент) — reclaim его не трогает.
2. Завершение поиска `done` по **терминальным** страницам (`fetched` ИЛИ `fail`; fail — норма).
3. `pages_per_request` — атрибут провайдера (Tavily 20, Firecrawl 1).
4. Инлайн-контент при `max_results ≤ pages_per_request` (Tavily `include_raw_content`, бесплатно).
5. Батч-фетч: chunk = `pages_per_request`, параллельно `fetch_concurrency` → 5×20.

## What was done

- **constants** — `SEARCH_FETCHING`; убран неиспользуемый `FETCH_BATCH`. Синхронизирован CHECK в
  `wcm_001` (отставал ещё с retry/fail — теперь полный набор + `fetching`).
- **Провайдер** (`base.SearchProvider`) — `pages_per_request` (Tavily 20, Firecrawl 1);
  `search(req, with_content=)` (Tavily `include_raw_content`, Firecrawl игнорирует); `fetch_page`→
  `fetch_pages(urls)->{url:md|None}` (батч). Клиенты tavily/firecrawl переписаны.
- **Обработчик** (`base.ProviderHandler`): `run_search_queue` — инлайн при `max_results ≤ pages_per_request`,
  статус запроса `empty`/`done`(все терминальны)/`fetching`; `run_fetch_queue` — пачка `concurrency × pages_per_request`,
  батчи по `pages_per_request` параллельно, `search_finalize_ready` в конце.
- **`store_results`** — создаёт страницы (инлайн-`content` → `fetched`); статус запроса не финализирует.
- **CRUD** — `search_mark_fetching`, `search_finalize_ready` (fetching со всеми терминальными → done),
  `search_result.nonterminal_page_count`.
- **Задачи** — `fetch_pages` без `limit` (считается внутри); логи со счётчиками (`fetching`/`finalized`).
- **Фронт** — статус `fetching` (`api.ts`/`labels.ts`/`ru.json`).
- **Dev-БД** — жёстко пересозданы 3 таблицы (CHECK с `fetching`).
- **Тесты** — `test_provider_handler` переписан (инлайн→done, no-content→fetching, батч-фетч, финализация);
  `test_providers`/`test_save`/`test_crud` под новый API.

## Result

- Проверки: `pytest --module=web_content` → 48 passed; `migrate check` → up to date; `vue-tsc` → 0.
- **Live e2e** (Tavily, инлайн): `register(max_results=4)` → `run_search_queue` `{done:1, fetching:0}`,
  4 страницы `fetched` с реальным контентом (80/39/9 КБ) за **один** прогон поиска, без задачи контента.
- Канвас `second-brain/.../pipeline-web-content.canvas` обновлён под исправленную логику.
- Провайдер `wcm_001` правлена на месте (dev пересоздан, heavy на PG строят с нуля).
