---
title: web_content — max_results явной колонкой в web_content_search (до params)
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Вынести требуемое кол-во страниц (max_results) из params в отдельную NOT NULL колонку web_content_search, до params. Жёсткое пересоздание таблиц в dev."
tags: [web_content, db, schema]
---

## Task

Вынести требуемое кол-во страниц явным полем `max_results` в таблицу
`web_content_search`, **до `params`**. `params` больше его не дублирует. Таблицу
пересоздать жёстко (drop + create_all в dev).

## What was done

- **Модель** `models/search.py` — колонка `max_results: Mapped[int]` (Integer, server_default "10")
  между `request` и `params`.
- **Миграция** `wcm_001_search.py` — та же колонка `sa.Integer() NOT NULL server_default 10` до `params`
  (правка на месте — чейн свежий).
- **`crud.search.search_create`** — параметр `max_results: int = 10` (дефолт сохраняет существующие вызовы).
- **`providers/request.py`** — `to_params()` больше **не** кладёт `max_results` (только domains/time_range);
  `from_stored(query, max_results, params)` берёт его аргументом.
- **`providers/base._search_one`** — `SearchRequest.from_stored(row.request, row.max_results, row.params)`.
- **`services/searcher.register_search`** — пишет `max_results` в колонку; `params = to_params() or None`.
- **`dto.SearchRow`** + фронт `web_content/api.ts SearchRow` — поле `max_results` до `params`.
- **Dev-БД** — жёстко пересозданы 3 таблицы web_content (drop + create_all, assert sqlite+dev-путь).
- **Тесты** — `test_searcher` обновлён (max_results = колонка, params без него); прочие вызовы `search_create`
  работают на дефолте 10.

## Result

- Изменены: `models/search.py`, `migrations/versions/wcm_001_search.py`, `crud/search.py`,
  `providers/{request,base}.py`, `services/searcher.py`, `dto.py`, `web/src/features/web_content/api.ts`,
  `tests/modules/web_content/test_searcher.py`.
- Проверки: `pytest --module=web_content` → 44 passed; `migrate check` → up to date; `vue-tsc` → 0;
  dev DDL: `max_results INTEGER DEFAULT '10' NOT NULL` сразу после `request`.
