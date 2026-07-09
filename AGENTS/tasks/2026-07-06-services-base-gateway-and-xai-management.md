---
title: ServiceGateway base + xAI two gateways (inference + management)
date: 2026-07-06
status: completed
description: "Вынести общую HTTP-обвязку гейтвеев в services/base.py::ServiceGateway; у xAI сделать два гейтвея под две поверхности — XaiGateway (инференс api.x.ai) и XaiManagementGateway (биллинг management-api.x.ai) с отдельным ключом xai_management_api_key."
tags: [core_connectors, refactor, xai, balance, gateway]
---

## Task

«В корне services сделай файл base.py, вынеси туда базовые классы шлюзов. Для xAI — ManagementGateway и Gateway (два разных шлюза, два разных ключа). Продумай архитектуру.»

## Context

Три гейтвея (Tavily/Firecrawl/xAI) побайтово дублировали HTTP-обвязку (`__init__`/`_ensure_enabled`/`_key`/`_request`/`_post` + ClassVar-ы), различаясь только константами. Плюс выяснилось: баланс xAI отдаётся **не** inference-API, а отдельным Management API (другая база `management-api.x.ai` + отдельный ключ) — см. задачу `2026-07-06-connector-balance-and-limits`. Значит xAI ломает инвариант «сервис = один BASE_URL + один ключ» → нужны два гейтвея.

## What was done

- **`services/base.py::ServiceGateway`** — общая база всех гейтвеев: `_request`/`_post` (один `httpx.AsyncClient` на вызов, `Authorization: Bearer`), гейт `_ensure_enabled`/`_key`, `__init__(timeout)`. Подкласс объявляет только ClassVar-ы поверхности: `LABEL`, `BASE_URL`, `API_KEY_FIELD`, опц. `TIMEOUT` (default 60), `ENABLED_FIELD` (**`None` → гейт только по наличию ключа**). Тексты ошибок берут `LABEL`. Мёртвый ClassVar `code` (нигде не читался) удалён — не переносился.
- **Мигрированы на базу** все существующие гейтвеи (убрана дублирующая обвязка, остались ClassVar-ы + доменные методы): `TavilyGateway`, `FirecrawlGateway`, `XaiGateway`. Имена классов и сигнатуры методов не менялись → web_search-клиенты (`XxxGateway.ENABLED_FIELD` + методы) не тронуты.
- **xAI — две поверхности, два гейтвея:**
  - `services/xai/gateway.py::XaiGateway` — инференс (`api.x.ai`, `xai_api_key`, `xai_gateway_enabled`, `TIMEOUT`=300). `api_key_info()` теперь помечен как источник `team_id` для биллинга.
  - `services/xai/management.py::XaiManagementGateway` (новый) — биллинг (`management-api.x.ai`, отдельный ключ `xai_management_api_key`, `ENABLED_FIELD=None`). Методы (суммы USD-центы, `team_id` в пути): `prepaid_balance(team_id)`, `spending_limits(team_id)`, `invoice_preview(team_id)`. Гейтвей чистый — `team_id` резолвит потребитель (из inference `api_key_info()`), взаимных вызовов внутри нет.
- **Настройки:** добавлен секрет `xai_management_api_key` (`StrField secret`) в `settings.py` рядом с `xai_api_key`. Тумблера management нет (гейт по наличию ключа).
- **Экспорт:** `services/xai/__init__.py` отдаёт `XaiManagementGateway`.
- **Бенч:** `dev/bench/core_connectors/run_balances.py` расширен — для xAI резолвит `team_id` из inference и дёргает management `prepaid_balance`/`spending_limits`; без ключа мягко печатает «ключ не задан».

## Problems

Изначально management-эндпойнты нельзя было проверить без ключа (бенч падал контролируемо на `_key()`). После того как пользователь завёл management-ключ — **сверено живьём (2026-07-06)**: `prepaid_balance` → `total.val`+`changes[]`, `spending_limits` → нули (prepaid-only). Всплыла гоча: **знак инвертирован** (PURCHASE отрицательные, SPEND положительные, `FAILED_TO_CHARGE` не в сумме) → остаток = −`total.val`. Записано в `research/xai/INDEX.md`.

## Result

- Новый `src/modules/core_connectors/services/base.py` (`ServiceGateway`); `tavily/gateway.py`, `firecrawl/gateway.py`, `xai/gateway.py` ужаты до ClassVar-ов + методов; новый `xai/management.py`; `xai/__init__.py` + `settings.py` обновлены. Бенч `run_balances.py` расширен.
- Импорт-смоук: все 4 гейтвея наследуют `ServiceGateway`, базы/ключи верные (management `ENABLED_FIELD=None`). `--module=web_search --core` 323 passed; полный дефолт **329 passed**.
- Docs `core_connectors/INDEX.md` + `research/xai/INDEX.md` + MEMORY router обновлены.
- **Осталось (blocker — ключ пользователя):** живая сверка баланса xAI; дизайн нормализованного интерфейса баланса (задача `2026-07-06-connector-balance-and-limits`); опц. методы FirecrawlGateway `token_usage()`/`queue_status()`.
