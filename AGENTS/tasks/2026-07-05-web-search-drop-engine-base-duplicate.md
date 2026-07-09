---
title: web_search — убрать base.Engine, продублировать в SearchEngine/FetchEngine
date: 2026-07-05
status: completed
description: "Removed the shared base.Engine ABC (inheritance for its own sake) — duplicated code/enabled_field/available() into SearchEngine and FetchEngine, each now a standalone ABC. Registry TypeVar bound=Engine → constrained TypeVar('E', SearchEngine, FetchEngine)."
tags: [web_search, providers, refactor]
---

## Task

«`providers/base.py`: убери `Engine`, просто продублируй — тут наследование ради наследования.»

## What was done

- `providers/base.py` — удалён `Engine(ABC)`; `SearchEngine`/`FetchEngine` теперь оба `ABC` и
  каждый сам объявляет `code`/`enabled_field` + метод `available()` (= `service_enabled(enabled_field)`);
  дубль `available()` (2 строки) в каждом. `__all__` без `Engine`.
- `providers/registry.py` — импорт без `Engine`; `E = TypeVar("E", bound=Engine)` →
  `E = TypeVar("E", SearchEngine, FetchEngine)` (constrained), докстринг подправлен.
- `providers/__init__.py` — `Engine` убран из импорта и `__all__`.
- docs/memory — убрано упоминание общего предка `base.Engine`.

Провайдеры (`client.py`) не менялись — они реализуют `SearchEngine`/`FetchEngine` и задают
`enabled_field` как прежде.

## Verification

- `grep` bare `Engine` (кроме Search/Fetch/EngineRegistry) в src/tests → none.
- `uv run pytest --module=web_search` → 43 passed; full `uv run pytest` → 315 passed.
