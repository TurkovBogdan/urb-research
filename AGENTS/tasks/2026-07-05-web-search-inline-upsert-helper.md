---
title: web_search — убрать crud/_upsert.py, инлайнить диалект-выбор по месту
date: 2026-07-05
status: completed
description: "Deleted crud/_upsert.py (insert_for helper) and inlined the dialect-specific insert selection at both use sites (crud/page.py page_upsert, crud/query_result.py result_add) as two local lines: `dialect = s.bind.dialect.name if s.bind else 'postgresql'; insert = sqlite_insert if dialect=='sqlite' else pg_insert`."
tags: [web_search, crud, refactor]
---

## Task

«Убрать `crud/_upsert.py`, добавить по месту использования.»

## What was done

- Удалён `src/modules/web_search/crud/_upsert.py` (`insert_for`).
- В `crud/page.py` (`page_upsert`) и `crud/query_result.py` (`result_add`) добавлены импорты
  `pg_insert`/`sqlite_insert` и инлайн две строки на месте вызова:
  `dialect = s.bind.dialect.name if s.bind else "postgresql"` +
  `insert = sqlite_insert if dialect == "sqlite" else pg_insert` (поведение то же, включая None-fallback).
- doc `docs/web_search/INDEX.md` — убрано упоминание `_upsert.py` из списка crud-файлов.

## Verification

- `grep _upsert|insert_for` в src/tests → только `page_upsert` (функция), реальных ссылок нет.
- `uv run pytest --module=web_search` → 41 passed; full `uv run pytest` → 313 passed.
