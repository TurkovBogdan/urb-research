---
title: web_search — web_search_result → web_search_query_result (результаты запроса)
date: 2026-07-05
status: completed
description: "Renamed the join entity from 'result' to 'query_result' end-to-end: table web_search_result→web_search_query_result, model WebSearchResult→WebSearchQueryResult, files models/result.py→query_result.py + crud/result.py→query_result.py, DTO ResultView→QueryResultView, constraint/index names, import alias result_crud→query_result_crud. CRUD function names (result_add/results_for_query/…) kept — read naturally in context."
tags: [web_search, models, dto, migrations, frontend, rename]
---

## Task

«`web_search_result` = `web_search_query_result` — и имя таблицы, и модели/DTO, остальное.
Не просто результаты, а результаты запросов.»

## What was done

- table `web_search_result` → `web_search_query_result`; constraint `uq_web_search_result_query_page`
  → `uq_web_search_query_result_query_page`; index `ix_web_search_result_query_code` →
  `ix_web_search_query_result_query_code`.
- model class `WebSearchResult` → `WebSearchQueryResult`; файл `models/result.py` → `models/query_result.py` (`mv`).
- crud файл `crud/result.py` → `crud/query_result.py` (`mv`); `crud/__init__.py` + `models/__init__.py` обновлены.
- DTO `ResultView` → `QueryResultView` (`dto.py`, `QueryDetail.results`, `__all__`).
- migration `wsm_003_result.py` — table/constraint/index/docstrings обновлены (**revision id и имя файла
  оставлены** `wsm_003_result`, чтобы не рвать цепочку/`alembic_version`).
- import alias `result_crud` → `query_result_crud` (api.py, save.py, tests); CRUD-функции
  `result_add`/`results_for_query`/`results_with_page_for_query` **оставлены** (читаются естественно).
- докстринги `module.py`, `web_search/__init__.py`, `wsm_002_page.py` (FK-упоминание).
- frontend — `api.ts` (`ResultView`→`QueryResultView`, `QueryDetail.results`), `QueryView.vue` (импорт+хелперы).
- dev sqlite rebuild (drop старой `web_search_result` + create_all → `web_search_query_result`).
- docs/memory обновлены.

## Verification

- `grep` старых токенов (`web_search_result`/`WebSearchResult`/`models.result`/`crud import result`) → none.
- dev sqlite таблицы: `web_search_page`, `web_search_query`, `web_search_query_result` (старая удалена).
- `uv run pytest --module=web_search` → 41 passed; full `uv run pytest` → 313 passed.
- `migrate check` → up to date; `vue-tsc --noEmit` → 0.
