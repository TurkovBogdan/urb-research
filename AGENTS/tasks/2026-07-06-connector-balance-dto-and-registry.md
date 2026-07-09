---
title: Unified balance — HAS_BALANCE flag, balance() method, ServiceBalance DTO, BalanceRegistry
date: 2026-07-06
status: completed
description: "Единый слой баланса в core_connectors: флаг HAS_BALANCE на базовом гейтвее, общий метод balance(), нормализованный DTO ServiceBalance (сумма USD + кредиты used/available) и реестр BalanceRegistry, собирающий DTO по всем не отключённым сервисам."
tags: [core_connectors, balance, dto, registry]
---

## Task

«На уровне базового класса: (1) константа наличия баланса; (2) один метод с общим названием и логикой для получения баланса; (3) DTO баланса — сумма (доллары) + кредиты (использовано, доступно); (4) реестр, отдающий DTO по всем не отключённым сервисам.»

## Context

Из предыдущих задач: баланс Tavily = кредиты (`plan_limit−plan_usage`), Firecrawl = кредиты (`remainingCredits`/`planCredits`), xAI = деньги через management-API (остаток `−total.val` центов). Формы несовместимы → нужен нормализующий слой поверх гейтвеев (все они уже на общей базе `ServiceGateway`, см. `2026-07-06-services-base-gateway-and-xai-management`).

## What was done

- **Флаг наличия баланса** — `ServiceGateway.HAS_BALANCE: ClassVar[bool] = False`. True у `TavilyGateway`/`FirecrawlGateway`/`XaiManagementGateway`; инференс-`XaiGateway` — False. Плюс `SERVICE: ClassVar[str]` (код сервиса для DTO/реестра — вернул как используемый, не мёртвый) и `available()` (не отключён ли тумблером; `ENABLED_FIELD=None` → всегда).
- **Единый метод** — `async ServiceGateway.balance() -> ServiceBalance` (общая логика: гейт по `HAS_BALANCE` + оркестрация `_fetch_balance` → `_parse_balance`). Подкласс задаёт только запрос и маппинг:
  - Tavily/Firecrawl: `_fetch_balance` = `usage()`; `_parse_balance` — кредиты used/available.
  - xAI: `XaiManagementGateway._fetch_balance` резолвит `team_id` из инференс `api_key_info()` → `prepaid_balance`; `_parse_balance` — **инверсия знака** `amount=−total.val/100` USD.
- **DTO `services/balance.py::ServiceBalance`** (pydantic): `service`/`label`, `amount`+`currency` (деньги), `credits_used`/`credits_available`+`credits_unit` (кредиты), `error`. Каждый сервис заполняет что умеет.
- **Реестр `services/registry.py::BalanceRegistry`** + синглтон `balance_registry` (Tavily/Firecrawl/XaiManagementGateway): `collect()` параллельно (`asyncio.gather`) снимает баланс со всех не отключённых (`available()`); сбой одного → `error` в его DTO, сбор не падает. `register()` отвергает гейтвей без `HAS_BALANCE`. Экспорт `ServiceBalance`/`BalanceRegistry`/`balance_registry` из `services/__init__`.
- **Тесты** (новый `tests/modules/core_connectors/test_balance.py`, 7 шт., `pure`): маппинги Tavily/Firecrawl/xAI (в т.ч. инверсия знака и пустые поля→None), `balance()` без `HAS_BALANCE` → `NotImplementedError`, реестр (отвергает не-баланс гейтвей, фильтрует отключённые, ловит ошибку в DTO). Стаб-гейтвеи — без сети.
- **Бенч** `run_balances.py` расширен секцией `BalanceRegistry.collect()`.

## Result

- Новые: `services/balance.py`, `services/registry.py`, `tests/modules/core_connectors/test_balance.py`. Правки: `services/base.py` (флаг/`SERVICE`/`available`/`balance`+хуки), `tavily`/`firecrawl`/`xai/gateway.py`, `xai/management.py`, `services/__init__.py`, бенч.
- **Живая сверка (реестр end-to-end):** `tavily 983/17 credits`, `firecrawl 898/102 credits`, `xai $6.02 USD`.
- `--module=core_connectors` 7 passed; полный дефолт **336 passed**. Импорт-цепочка без циклов (DTO `balance.py` без внутренних импортов → base/гейтвеи/реестр над ним).
- Docs `core_connectors/INDEX.md` (раздел «Баланс») + MEMORY router обновлены.
- Возможные расширения (не в этой задаче): вторая ось Firecrawl (tokens) и concurrency; денежная нормализация кредитов (курс кредит→USD у Tavily/Firecrawl отсутствует); выставление баланса наружу (API/фронт).
