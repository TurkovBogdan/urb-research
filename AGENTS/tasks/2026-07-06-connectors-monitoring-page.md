---
title: Connectors monitoring page — registry to module root, /connectors API, cards page
date: 2026-07-06
status: completed
description: "Перенести реестр коннекторов в корень модуля; отдать internal-эндпойнт GET /connectors (паспорт+баланс); фронт-страница карточками коннекторов с балансом в разделе «Мониторинг» первой (перед «Задачи»); баланс — компонент на массиве DTO."
tags: [core_connectors, monitoring, frontend, api, registry]
---

## Task

«registry.py → в корень модуля. Создать страницу со списком включённых сервисов и их балансом (web/src/features). Вывод баланса — компонент, принимающий массив DTO. Оформление карточками коннекторов с описанием, близко к /tasks. Раздел «Мониторинг», первым, перед «Задачи».»

## What was done

**Бэкенд**
- `services/registry.py` → **`registry.py`** (корень модуля): домен «коннекторы» ≠ раскладка файлов `services/`. Внутренние импорты абсолютные — не менялись. `services/__init__` теперь экспортирует только DTO (реестр — из `core_connectors.registry`); правлены импортёры (тест, бенч).
- Новый internal-роутер: `api/connectors.py` (`GET /connectors` → `list[ConnectorView]`, баланс вживую `with_balance=True`) + `api/__init__.py` (агрегатор). `module.py` — `internal_router`/`internal_router_prefix=""` (по образцу core_monitoring).

**Фронт** (`web/src/features/core_connectors`)
- `api.ts` — типы `ConnectorInfo`/`ConnectorBalance`/`ConnectorView` + `fetchConnectors()`.
- `views/ConnectorsView.vue` — страница карточками (эталон TasksView): PageLayout+PageHeader, refresh, KPI включено/всего, грид карточек (имя, описание, badge включён/отключён, блок баланса); загрузка в `onActivated` (KeepAlive-гоча).
- `components/ConnectorBalance.vue` — **принимает массив** balance-DTO; на запись: деньги (`Intl` currency), кредиты (доступно + «из total» + бар, low<15%→warn), либо ошибка. Массив — задел под мультиось (напр. Firecrawl credits+tokens).
- `routes.ts` (`/connectors`) + `locales/ru.json` (namespace `core_connectors`, авто-глоб).
- `router/index.ts` — подключён `coreConnectorsRoutes`. `AppSidebar.vue` — пункт «Сервисы» (`IconPlugConnected`) в разделе «Мониторинг» **первым, перед «Задачи»**.

## Result

- Live `GET /internal/connectors` (ASGI+lifespan): 200, tavily 983/17 credits, firecrawl 898/102, xai $6.02 — полный путь реестр→API работает.
- `--module=core_connectors` 8 / полный дефолт **337 passed**; `vue-tsc` type-check чист; `web/dist` пересобран.
- Docs `core_connectors/INDEX.md` + MEMORY router обновлены.
- Проверено пользователем на фронте — ок.
- Не делалось: авто-refresh по таймеру, вторая ось Firecrawl (tokens) в DTO/компоненте.

## Follow-up (кредиты: «использовано / всего» + %)

По просьбе — кредитный баланс в форме «использовано из всего» (17 / 1000) + процент использования в DTO:
- DTO `ConnectorBalance`: добавлены `credits_total` (=used+available) и `credits_used_percent` (0..100); кредитную математику вынес в фабрику `ConnectorBalance.from_credits(used, available, unit)` (дедуп Tavily/Firecrawl, оба перешли на неё).
- Фронт: `api.ts` +2 поля; `ConnectorBalance.vue` — primary «`used / total unit`», secondary «`{percent}% использовано`», бар = доля использования (warn при >85%, класс `is-high`); локаль `used_percent` вместо `of_total`.
- Тесты дополнены (`credits_total`/`credits_used_percent`: tavily 1000/1.7%, firecrawl 1000/10.2%). Live `GET /internal/connectors`: tavily 17/1000 1.7%, firecrawl 102/1000 10.2%, xai $6.02. `--module=core_connectors` 8 / `vue-tsc` чист; `web/dist` пересобран.

## Follow-up (выравнивание карточек)

Карточки прыгали по высоте (разная длина описания, разный блок баланса). Стандартизировано:
- Описание — фиксировано на **3 строки** (`-webkit-line-clamp: 3` + `min-height: calc(1.5em*3)`): короткие резервируют высоту, длинные обрезаются многоточием.
- Блок баланса — **единая структура** каждой строки: значение (+подпись) + **бар всегда** (`.balance-bar` рендерится всегда; fill `width=(ratio ?? 0)`, т.е. пустой для денег/ошибки/«нет баланса»). Убран `v-if` на баре.
- «Нет баланса» (не умеет/отключён) переехал внутрь компонента: prop `placeholder` → одна строка-заглушка (`kind='na'`, мелкий faint-текст) + пустой бар. Во View убран отдельный `conn-card__balance-na`; `ConnectorBalance` рендерится всегда.
- Значение: деньги/кредиты — крупное mono; ошибка/заглушка — мелкий обычный текст (nowrap+ellipsis, `title`). `vue-tsc` чист; `web/dist` пересобран.
