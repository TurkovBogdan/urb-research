---
title: web_search — DTO в модельные файлы + дедуп Paged/дата в ядро
date: 2026-07-05
status: completed
description: "Moved web_search read-DTOs out of dto.py into the model files next to their ORM (query/page/query_result); deleted dto.py. Deduped the shared pieces into core: Paged[T] → new src/core/api/pagination.py (exported from core.api), and the datetime serializer reuses the pre-existing core DatetimeUTCStr (web_search SqlDateTime was a dupe). Also migrated research_registry off its own Paged/SqlDateTime dupes onto the core types."
tags: [web_search, research_registry, core, dto, refactor]
---

## Task

«`dto.py` перенесём в `models` по файлам моделей?» → да. «Куда общие Paged/SqlDateTime?»
→ сериализатор даты = часть ядра. «Везде поправь» → заодно дедупнуть research_registry.

## Key finding

- Ядро **уже** содержит `DatetimeUTCStr` (`core/utils/date.py`) — тот же SQL-формат
  (`"yyyy-MM-dd HH:mm:ss"`, naive UTC), что и локальные `SqlDateTime`. Значит в `date.py`
  ничего добавлять не надо — переиспользуем существующий тип, локальные дубли удаляем.
- `Paged[T]` в ядре не было — задублирован в web_search и research_registry.

## What was done

Core:
- `src/core/api/pagination.py` — новый `Paged[T]` (общий конверт списка).
- `src/core/api/__init__.py` — экспорт `Paged` (рядом с `ApiError`/`ErrorBody`).

web_search (DTO рядом с ORM, `dto.py` удалён):
- `models/query_result.py` ← `QueryResultView`.
- `models/query.py` ← `QueryRow`, `QueryDetail` (тянет `QueryResultView`).
- `models/page.py` ← `PageRow`, `PageDetail`.
- даты в DTO → ядровый `DatetimeUTCStr`; `api.py` импортит `Paged` из `core.api`,
  DTO — из `models.{query,page,query_result}`.

research_registry (дедуп на ядровые типы, dto.py оставлен):
- `dto.py` — убраны локальные `_to_sql`/`SqlDateTime`/`Paged`/`T`; `SqlDateTime` →
  `DatetimeUTCStr` во всех Row; `__all__` без `Paged`/`SqlDateTime`.
- `api.py` — `Paged` из `core.api`.

Docs/memory обновлены (web_search hub + MEMORY web_search-строка).

## Verification

- `grep` stale `web_search.dto` / `SqlDateTime` → none.
- Smoke-import всех тронутых модулей (вкл. research_registry api/dto/mcp) — OK; datetime
  сериализуется как `"2026-07-05 12:34:56"` (без `T`).
- `uv run pytest` (полный) → **315 passed** (research_registry без тестов — покрыт smoke-импортом).
