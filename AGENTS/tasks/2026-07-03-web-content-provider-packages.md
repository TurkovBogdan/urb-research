---
title: web_content — провайдеры-пакеты с собственным обработчиком очереди + настройка default_pages
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Провайдеры → папки по 3 файла (__init__/client/handlers); обработчик очереди (параллелизм) переезжает из services в провайдер. Настройка default_pages=10 (max_results по умолчанию), рядом с потоками. Задачи без overlap — параллелизм внутри провайдера."
tags: [web_content, providers, scheduler, settings]
---

## Task

1. Провайдеры — папки по провайдерам, каждый = 3 файла; провайдер владеет
   **обработчиком задачи** (логика очереди + параллелизм переезжает из
   `services/search_runner.py`+`fetcher.py` внутрь провайдера).
2. Задачи `run_searches`/`fetch_pages` — без overlap (уже гарантирует task-лок);
   параллелизм — внутри обработчика провайдера (семафор).
3. Настройка `default_pages`=10 рядом с потоками (+ на фронте `/core/settings`).

## Assumptions (ответа на уточнения не было — выбраны рекомендованные)

- 3 файла: `__init__.py` (регистрация) + `client.py` (движок: search/fetch_page) +
  `handlers.py` (обработчик очередей — дефолт в `base.ProviderHandler`, оверрайд на провайдера).
- `default_pages` = `max_results` по умолчанию на поисковый запрос (было хардкод 5).
- Обработчик активного провайдера обрабатывает **всю** очередь своим клиентом;
  `search_claim_pending` переназначает `provider` на активного (без застреваний).
- Настройки схемо-driven → на фронте поле появляется автоматически (IntField по `kind`).

## What was done

- **Провайдеры → пакеты** `providers/tavily/`, `providers/firecrawl/`, каждый = 3 файла:
  `__init__.py` (register инстанса обработчика), `client.py` (`SearchProvider`: search/fetch_page),
  `handlers.py` (`ProviderHandler` подкласс: code + client). Старые `tavily.py`/`firecrawl.py` удалены.
- **`base.py`** — `SearchProvider` (клиент) + новый `ProviderHandler` (обработчик очередей): дефолтные
  `run_search_queue`/`run_fetch_queue` = reclaim→claim→параллельный сетевой вызов (семафор)→последовательная
  запись. Сюда переехала логика из `services/search_runner.py` + `services/fetcher.py` (оба **удалены**).
- **`registry.py`** — хранит инстансы `ProviderHandler` (`register(handler)`, `get(code)->handler`).
- **Задачи** `run_searches`/`fetch_pages` — делегируют `get(active_provider_code()).run_search_queue()`/
  `.run_fetch_queue()`. Overlap исключён (task-лок); параллелизм — внутри обработчика.
- **`searcher.register_search(query, *, max_results=None, …)`** — строит `SearchRequest`, `max_results`
  по умолчанию из настройки `default_pages`.
- **`crud.search.search_claim_pending(limit, provider)`** — при claim перезаписывает `provider` активным.
- **Настройка `default_pages`** (IntField 1..50, default 10) в `module_settings.SCHEMA` + хелпер `default_pages()`.
  На фронте появляется автоматически (settings рендерятся из схемы по `kind`; лейбл — с бэка).
- **Тесты**: `test_searcher` (новая сигнатура + default_pages), новый `test_provider_handler`
  (run_search_queue done/empty/failed + reclaim, run_fetch_queue transitions) вместо удалённых
  `test_search_runner`/`test_fetcher`; `test_providers` без изменений (get→handler).

## Result

- Новые: `providers/{tavily,firecrawl}/{__init__,client,handlers}.py`; `tests/.../test_provider_handler.py`.
- Изменены: `providers/{base,registry,__init__}.py`, `module_settings.py`, `services/searcher.py`,
  `crud/search.py`, `tasks/{run_searches_task,fetch_pages_task}.py`; `tests/.../test_searcher.py`.
- Удалены: `providers/{tavily,firecrawl}.py`, `services/{search_runner,fetcher}.py`,
  `tests/.../{test_search_runner,test_fetcher}.py`.
- Записи: `docs/web_content/INDEX.md`, `memory/MEMORY.md`, tasks INDEX.
- Проверки: `pytest --module=web_content` → 44 passed; `--core` + оба модуля → 313 passed;
  импорт-смоук (оба провайдера регистрируются, схема содержит `default_pages`).

## Verification (реальный кейс + фикс dev-БД)

- **Live e2e** (свежая sqlite + живой Tavily-ключ из dev-настроек): `register_search(max_results=3)`
  → `run_search_queue` `{claimed:1, done:1}`, 3 реальных результата (arxiv/merge.dev/gradientflow),
  провайдер переназначен `tavily` → `run_fetch_queue` `{claimed:3, fetched:3}`, реальный markdown 6.7–18 КБ.
  Весь новый конвейер (обработчик провайдера, параллелизм, claim/reassign, default_pages) работает вживую.
- **Находка**: dev-sqlite `web_content_search`/`_page` созданы до `processing` → старый CHECK; `create_all`
  не альтерит существующие таблицы → задачи падали на claim (`CHECK constraint failed`). Записано в память
  (create_all never alters existing dev tables).
- **Фикс (с согласия пользователя)**: DROP + `create_all` 3 таблиц web_content в `runtime/dev/app.sqlite3`
  (assert sqlite + dev-путь; настройки/ключи/задачи целы). Констрейнты теперь с `processing`; застрявший
  тестовый ряд ушёл при пересоздании.
