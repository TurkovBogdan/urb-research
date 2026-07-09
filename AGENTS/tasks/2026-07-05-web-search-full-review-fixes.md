---
title: web_search — полная сверка модуля + правки трёх находок
date: 2026-07-05
status: completed
description: "Полный проход по web_search после серии рефакторингов: тесты (51 модуль / 323 полный), схема-паритет, engine-рename сквозь бэк+фронт, sort_by end-to-end — всё актуально. Исправлены три находки: (1) док утверждал, что dev-sqlite строится create_all (уже миграции) — поправлено; (2) классы TavilyProvider/FirecrawlProvider → TavilyEngine/FirecrawlEngine (последний остаток «provider» в идентификаторах); (3) стал докстринг models/page.py per-provider → per-engine."
tags: [web_search, review, rename, docs]
---

## Задача

«Проверь модуль полностью, проверь тесты, что всё актуально» → ревизия + фиксы.

## Итог ревизии (актуально)

- Тесты: модуль 51, полный сьют **323 passed**; `migrate check` up to date (паритет схемы).
- engine-рename прошёл сквозняком: настройки/хелперы/`Searcher`/колонки/реестры/код ошибки
  `search_engine_disabled` **и фронт** (`api.ts`/`stores`/`views`/`locales`) — рассинхрона нет.
- `sort_by` (правка линтера) end-to-end и симметрично: crud `query`+`page` (белые списки
  `QUERY_SORT_COLUMNS`/`PAGE_SORT_COLUMNS`, инъекция → дефолт `created_at`), api, тесты, фронт.
- Троттлинг/ожидание слота, двухстадийность, `save.py` свёрнут, DTO в моделях, grounding xai —
  покрыто тестами.

## Исправлено

1. **Док-факт**: `docs/web_search/INDEX.md` (2 места) утверждал «лайфспан на sqlite строит
   схему `create_all`» — уже неверно (файловая dev-sqlite и PG идут через Alembic; `create_all`
   только in-memory тесты). Приведено в соответствие с `app_factory.py`.
2. **Имена классов**: `TavilyProvider`→`TavilyEngine`, `FirecrawlProvider`→`FirecrawlEngine`
   (по цепочке: `client.py` + пакетные `__init__.py`; docstrings «Провайдер …»→«Движок …»).
   `XaiSearchEngine` (search-only) оставлен — теперь все имена оканчиваются на `Engine`.
   Ссылок по имени класса в тестах нет; реестры регистрируют под кодами tavily/firecrawl.
3. **Докстринг** `models/page.py`: «per-provider учёта фетча» → «per-engine».

## Проверка

- Остатков `*Provider`/`per-provider`/устаревших create_all-утверждений нет.
- Import-smoke: реестры = search{firecrawl,tavily,xai} / fetch{firecrawl,tavily}.
- Полный `uv run pytest` → **323 passed**.
