---
title: ConnectorsRegistry + connector passport (name/description) + two DTOs
date: 2026-07-06
status: completed
description: "Переосмысление реестра как реестра КОННЕКТОРОВ (домен), а не баланса: BalanceRegistry→ConnectorsRegistry, паспорт (NAME/DESCRIPTION) на базовой модели, метод connectors(with_balance=…) с двумя DTO (ConnectorInfo + ConnectorBalance→ConnectorView). Баланс — одна из возможностей реестра."
tags: [core_connectors, registry, dto, refactor]
---

## Task

«BalanceRegistry → ServicesRegistry, а лучше ConnectorsRegistry — чтобы не смешивать домен и правила для папок сервисов. Баланс — просто один метод реестра. Добавить коннекторам название и описание на уровне базовой модели; в реестре — метод получения всех коннекторов, в нём опционально баланс. Получим два DTO: один под сервис, другой под цену.»

## Context

Предыдущая итерация (`2026-07-06-connector-balance-dto-and-registry`) дала `BalanceRegistry`/`ServiceBalance`, но термин «баланс» узкий: реестр про коннекторы, баланс — лишь одна их грань. Плюс папка `services/` — раскладка файлов, домен = «коннекторы».

## What was done

- **Паспорт на базе** `ServiceGateway`: `LABEL`→`NAME` (идёт и в тексты ошибок) + новый `DESCRIPTION`; `SERVICE` (код) остался. Заданы у Tavily/Firecrawl/xAI (name+описание).
- **Два DTO** (`services/balance.py` → **`services/dto.py`**, mv; чистый модуль без внутренних импортов):
  - `ConnectorInfo` — паспорт: `service`, `name`, `description`, `enabled`, `has_balance`.
  - `ConnectorBalance` (переим. из `ServiceBalance`, `label`→`name`) — остаток: деньги `amount`/`currency` ИЛИ кредиты `credits_used`/`credits_available`+`credits_unit`, `error`.
  - `ConnectorView` — композиция `info` + опц. `balance`.
- **Реестр** `services/registry.py`: `BalanceRegistry`→**`ConnectorsRegistry`** (+ синглтон `balance_registry`→`connectors_registry`). Регистрирует **по коннектору на вендор**: Tavily/Firecrawl/`XaiGateway` (management больше не отдельная запись). Метод `connectors(*, with_balance=False) -> list[ConnectorView]` (параллельно `asyncio.gather`; баланс только у включённых+умеющих; сбой→`error` в DTO). Плюс `all()`/`info(c)`.
- **xAI как один коннектор:** `XaiGateway.HAS_BALANCE=True`, `balance()` **делегирует** `XaiManagementGateway().balance()` (ленивый импорт рвёт цикл inference↔management). Инференс — «лицо» коннектора xAI, management — внутренняя биллинг-поверхность.
- **Экспорт** из `services/__init__`: `ConnectorInfo`/`ConnectorBalance`/`ConnectorView`/`ConnectorsRegistry`/`connectors_registry`.
- **Тесты** `tests/modules/core_connectors/test_balance.py` переписаны под новые имена/API (8, pure): маппинги, паспорт `info()`, `connectors(with_balance=False)` — голые паспорта, `with_balance=True` — композиция + изоляция ошибок + пропуск отключённых/не-баланс. Стаб-коннекторы.
- **Бенч** `run_balances.py` — секция `connectors_registry.connectors(with_balance=True)` (паспорт+баланс).

## Result

- `services/dto.py` (3 DTO), `services/registry.py` (`ConnectorsRegistry`), правки базы/гейтвеев/`__init__`/тестов/бенча.
- **Живьём:** `tavily Tavily — Веб-поиск… 983/17 credits`; `firecrawl … 898/102 credits`; `xai (Grok) … 6.02 USD` (через делегацию в management).
- `--module=core_connectors` 8 / полный дефолт **337 passed**. Импорт без циклов.
- Docs `core_connectors/INDEX.md` (раздел «Реестр коннекторов + баланс») + MEMORY router обновлены.
- Не делалось: вторая ось Firecrawl (tokens), выставление реестра наружу (API/фронт), `spending_limits` в DTO.
