---
title: web_search — троттлинг операций по числу in-flight записей (delay, не error)
date: 2026-07-05
status: completed
description: "Несколько агентов через MCP параллельно запускают поиск + фетч контента → падаем по лимитам внешних API (Tavily/Firecrawl/xAI). Нужен throttling в режиме ЗАДЕРЖКИ (не падения): ограничивать число одновременных операций. Ключевая идея (от пользователя): записи со статусом `processing` в наших таблицах — уже распределённый счётчик in-flight; считаем их на уровне модуля и при count > X ставим задержку. Стадия: обсуждение дизайна + исследование реальных лимитов."
tags: [web_search, rate-limit, throttling, design, research]
---

## Проблема

MCP-сервер в backend-процессе. Несколько агентов параллельно зовут поиск → N параллельных
`searcher.search`, затем параллельный фетч страниц. Внешние API (Tavily/Firecrawl/xAI) режут
по лимитам → падаем с ошибкой. Нужно ограничивать **в режиме задержки**, не падения.

## Ключевая идея (пользователь)

БД — общая для всех процессов/агентов. Записи `web_search_query`/`web_search_page` со статусом
`processing` = число операций «в работе» прямо сейчас. Считаем их на уровне модуля;
если `count(processing) > X` — задержка (sleep+recheck), а не ошибка. Никакого Redis/in-proc
семафора — счётчик уже в БД.

## Открытые вопросы (дизайн)

- **Concurrency vs RPM.** count(processing) ограничивает только одновременность. Если лимит —
  requests/min, нужен ещё rate-gate (count строк по `created_at` за окно 60с). Какой лимит
  реально у провайдеров — исследование.
- **Scоpe.** Считать per-role + per-provider: search → `web_search_query WHERE status=processing
  AND search_engine=<p>`; fetch → `web_search_page` теперь несёт колонку `fetch_engine`
  (nullable, добавлена 2026-07-05 — сразу после `status`, миграция `wsm_002_page`), так что фетч
  тоже считается per-provider. Заполнение колонки (page_upsert/searcher) — отдельный шаг.
- **Stale processing (критично).** Крашнутый процесс оставит `processing` навсегда → счётчик течёт,
  лимитер встаёт намертво (а модуль «терминальный, без ретраев»). Нужно считать только
  `processing` с `updated_at >= now - TTL` + reaper протухших → `error`.
- **Гонка/overshoot.** count-then-go — eventually consistent, кратковременный перебор возможен.
  Для «не бить лимиты» держим X с запасом (soft-лимит) — ок. Строгий бонд → атомарный claim с
  порядком (FIFO по created_at).
- **Thundering herd.** Пробуждение ожидающих — с джиттером.
- **Дом лимитера.** Модуль web_search (считает свои строки) vs core_gateway (единый чокпоинт к
  API, но домен-агностичен). Trade-off: модульный проще, но другой потребитель того же API не
  будет учтён.

## Research (нужно)

- Реальные лимиты Tavily / Firecrawl / xAI: concurrency + RPM + поведение 429 (Retry-After).
  Текущий research-лог покрывает только кредиты, не RPM/concurrency.

## Решения

- **Scope сейчас — только concurrency-гейт** (count processing). Rate-гейт (задержки по числу
  выполненных операций за окно / RPM) — **отложен**, добавим позднее если потребуется.
- Гейт — на число одновременных **поисков**; фетч ограничивается транзитивно
  (потолок фетча = max_поисков × fetch_concurrency, оба per-search-семафора остаются как есть).
- Настройка — одна новая, per-provider счёт по search_engine.

## Открыто к подтверждению

- Имя/дефолт настройки: предложено `max_concurrent_searches` = 3 (min 1 / max 50).
- TTL на processing + reaper протухших → делать сразу (без них лимитер клинит на краше).

## Реализовано

- **Настройка** `max_concurrent_searches` (IntField, default 3, min 1 / max 50) + хелпер
  `settings.max_concurrent_searches()`.
- **CRUD** (`crud/query.py`): `query_processing_count(search_engine, *, since)` — свежие
  `processing` по движку; `query_expire_stale(search_engine, *, before)` — reaper залипших
  `processing` → `error="stale"`.
- **Гейт** (`services/searcher.py`): `_acquire_search_slot(engine.code)` между `query_create`
  (pending) и `query_mark_processing` — цикл: expire_stale → count → если `< limit` идём, иначе
  `asyncio.sleep(random.uniform(0.5,1.5))`. Константы `_PROCESSING_STALE_TTL=15мин`,
  `_SLOT_POLL_MIN/MAX`. Reaper inline (планировщика у модуля нет); TTL даёт гарантию прогресса.
- **Индекс** `ix_web_search_query_engine_status` (`search_engine`,`status`) — модель + миграция
  `wsm_001_query`.
- Фетч не трогали (ограничен транзитивно). Rate-гейт (RPM) не делали — отложен.
- Тесты: `test_crud` (count freshness/scoping + expire_stale только старые/свой движок),
  `test_searcher` (гейт: под лимитом без задержки / ждёт до освобождения / игнор чужого
  провайдера), `test_settings` (дефолт 3, границы 1..50).
- Docs (`docs/web_search/INDEX.md`) + MEMORY обновлены.

## Проверка

- `migrate upgrade` на свежей sqlite — индекс на месте.
- `uv run pytest --module=web_search` → 49 passed; полный `uv run pytest` → **321 passed**.

## Осталось (вне scope)

- Заполнение `web_search_page.fetch_engine` (колонка есть, писатель — отдельный шаг; для фетч-
  троттлинга per-provider, когда/если понадобится).
- Rate-гейт (RPM, счёт выполненных за окно) — по требованию.
- dev sqlite: `create_all` не добавит индекс/колонку в существующую таблицу — при желании
  пересобрать (drop+create_all под guard'ом). Функционально гейт работает и без индекса.

## Статус

Готово. Concurrency-гейт по in-flight строкам реализован и покрыт тестами (321 passed).
