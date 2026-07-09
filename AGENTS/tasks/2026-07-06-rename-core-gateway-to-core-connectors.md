---
title: Rename module core_gateway → core_connectors
date: 2026-07-06
status: completed
description: "Переименовать инфра-модуль core_gateway в core_connectors (директория, класс, name, доки, роутинг, фронт) и перенести его runtime-настройки в core_modules_settings по столбцу module. Внутренние классы XxxGateway и ключи *_gateway_enabled оставлены как есть."
tags: [core_connectors, web_search, settings, rename]
---

## Task

«переименовать модуль core_gateway в core_connectors» + «настройки перенеси». Название явное (модуль = тонкие коннекторы к внешним API), опечаток нет.

## Context

`core_gateway` — инфра-модуль-шлюз к внешним API (Tavily/Firecrawl/xAI) + их креды как runtime-настройки. Настройки хранятся в `core_modules_settings` с ключом по имени модуля → смена `Module.name` осиротила бы сохранённые API-ключи. Решено переименовать **идентичность модуля** (буквальный запрос), а внутренние `XxxGateway`/`gateway.py`/`*_gateway_enabled` оставить (глубокий gateway→connector — отдельно, при желании).

## What was done

- **Директория:** `src/modules/core_gateway/` → `core_connectors/` (mv). Класс `CoreGatewayModule` → `CoreConnectorsModule`, `name`/`description`, `settings.MODULE = "core_connectors"`. Все внутренние импорты `src.modules.core_gateway...` → `core_connectors` (module.py, __init__.py, settings.py, services/__init__.py, services/{tavily,firecrawl,xai}/{__init__,gateway}.py) + докстринги (шлюз→коннектор).
- **Потребители:** `src/apps/app/modules.py` (импорт+инстанс+докстринг), web_search `providers/{tavily,firecrawl,xai}/client.py` + `providers/base.py` (импорты `service_enabled`), прозаические ссылки в web_search `module.py`/`settings.py`/`api.py`/`__init__.py`/`providers/registry.py`/`services/searcher.py` и `research/__init__.py`.
- **Тесты:** комментарии в `tests/modules/web_search/test_search.py`, `test_settings.py` (только текст; поле `tavily_gateway_enabled` не трогали).
- **Фронт:** `web/src/features/settings/views/SettingsView.vue` (ключ лейбла `core_connectors: 'Сервисы'`), комментарий в `web/src/features/web_search/api.ts`. Пересобран `web/dist` (`pnpm build`) — старый `core_gateway` из бандла ушёл.
- **Бенчи:** `dev/bench/core_gateway/` → `core_connectors/` (mv) + все импорты `dev.bench.core_gateway...`/`src.modules.core_gateway...` и docstrings; web_search-бенчи (tavily/client.py, xai/run_search.py, README×2, firecrawl/compare_scrape.py — SQL `module='core_connectors'`).
- **Доки/память:** `AGENTS/docs/core_gateway/INDEX.md` → `core_connectors/INDEX.md` (mv+правка), ссылки в `AGENTS/docs/web_search/INDEX.md`, MEMORY.md routing-строка + web_search-строка + doc-линк.
- **Настройки (перенос):** dev-sqlite `runtime/dev/app.sqlite3` — `UPDATE core_modules_settings SET module='core_connectors' WHERE module='core_gateway'` (6 строк: tavily/firecrawl/xai `*_api_key` + `*_gateway_enabled`). Backend был остановлен; UPDATE не деструктивный, ключи сохранены.

## Result

- `grep core_gateway` по `src/tests/web/dev` пусто (кроме намеренно оставленных историч. `AGENTS/tasks`/`AGENTS/research`).
- `build_modules()` → `['core_setup','core_connectors','core_monitoring','core_mcp','web_search','research']`.
- Тесты: `--module=web_search --core` 323 passed; полный дефолт **329 passed**.
- Настройки перенесены в dev-БД, `web/dist` пересобран.
- Не делалось (по решению): глубокий рефактор `XxxGateway`→`XxxConnector`, файлов `gateway.py`, ключей `*_gateway_enabled`, функции бенча `load_gateway_store` — оставлены как внутренние идентификаторы.
