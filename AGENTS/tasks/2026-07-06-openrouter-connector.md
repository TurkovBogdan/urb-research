---
title: OpenRouter connector (balance-only) in core_connectors
date: 2026-07-06
status: completed
description: "Добавить OpenRouter как коннектор в core_connectors — только баланс (не инференс). Подкласс ServiceGateway, две метрики (лимит ключа + баланс аккаунта), регистрация в реестре. Креды — runtime-настройка (ENV — отложено)."
tags: [core_connectors, openrouter, balance]
---

## Task

«Добавляем в core_connectors коннектор openrouter.» Предыстория: полный `OpenRouterProvider` из semaphore-core слишком функциональный, нужен только баланс; проверен на верстаке (`2026-07-06-connector-balance-metrics-and-openrouter-bench`).

## What was done

- **`services/openrouter/gateway.py::OpenRouterGateway(ServiceGateway)`** — только баланс, без инференса. `openrouter.ai/api/v1`, `TIMEOUT=30`, ключ `openrouter_api_key`, тумблер `openrouter_gateway_enabled`, `HAS_BALANCE=True`. Методы `key_info()` (`GET /api/v1/key`) + `credits()` (`GET /api/v1/credits`).
- `_fetch_balance` тянет **оба** эндпойнта (`/credits` — best-effort: `httpx.HTTPError` → `None`, остаётся метрика лимита). `_parse_balance` строит **две метрики**: «Лимит ключа» (`usage`/`limit`, USD, с %) + «Баланс» (`total_credits − total_usage`, может быть минус). `limit=null` → метрика лимита опускается.
- `services/openrouter/__init__.py` — экспорт `OpenRouterGateway`.
- **Настройки** (`settings.py`): `openrouter_gateway_enabled` (BoolField default True) + `openrouter_api_key` (StrField secret) — по паттерну прочих коннекторов. **ENV-хранилище отложено** (у модуля пока нет env-инфры; когда появится — мигрировать ключ туда).
- **Реестр** (`registry.py`): `connectors_registry.register(OpenRouterGateway())`.
- **Тесты** (`test_balance.py`, +2 → 10): две метрики (лимит 5.16/10 51.6% + баланс −0.16), лимит-only когда `/credits` нет, пустой ответ → `metrics=[]`.

## Result

- **Фронт/dist НЕ менялись** — страница `/connectors` и настройки data-driven: OpenRouter появляется 4-й карточкой сам, поля ключа — в Настройки → Сервисы.
- Live через сам коннектор (ключ из ENV, без записи в настройки): «Лимит ключа 5.16 / 10 USD (51.6%)» + «Баланс −0.16 USD». Endpoint `GET /internal/connectors` возвращает 4 коннектора; OpenRouter без ключа в настройках → `error` DTO (ожидаемо).
- `--module=core_connectors` 10 / полный дефолт **339 passed**. Docs `core_connectors/INDEX.md` (services/openrouter) + MEMORY router обновлены; research `openrouter/INDEX.md` уже был.
- **Чтобы увидеть баланс на странице:** задать `openrouter_api_key` в Настройки → Сервисы (хот-релоад настроек). Ключ намеренно не сидировал в dev-БД.
