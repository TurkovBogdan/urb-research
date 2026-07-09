---
title: core_gateway module — external API gateways + credential storage
date: 2026-07-04
status: in-work  # in-work | completed | deferred
description: "New infra module core_gateway: thin connectors to external APIs (Tavily, Firecrawl, …) with their credentials as runtime settings. Step 1 — empty module + env storage for both services; step 2 — Tavily gateway with per-request param models. Incremental; rest later."
tags: [core_gateway, platform, tavily]
---

## Task

Создать модуль core_gateway, дающий коннекторы к внешним API (ключевое — простые
шлюзы) и хранящий их креды. Шаг 1: создать модуль (пока пустой), без реестра,
только хранение env для двух сервисов (Tavily/Firecrawl). Шаг 2: перенести Tavily,
создав модели параметров под каждый запрос; папка services/tavily + вспомогательные
файлы. Остальное — потом, шаг за шагом.

## Context

Провайдеры tavily/firecrawl жили внутри web_content (providers/*), где смешаны два
слоя: тонкий HTTP-клиент (по сути шлюз) и очередная оркестрация (ProviderHandler =
доменная логика). Решено вынести шлюзы в отдельный инфра-модуль core_gateway, а
оркестрацию оставить в web_content. Креды — runtime-настройки (не ENV): в проекте
токены уже специально вынесены ENV→settings; менять решено сохранить.

Дизайн-обсуждение зафиксировано: контракт «шлюз отдаёт нативный ответ сервиса,
маппинг под домен — у потребителя; ключ шлюз берёт сам из настроек; никакой
оркестрации в шлюзе». Имя core_gateway (инфра-префикс core_).

## What was done

Шаг 1 — модуль:
- `src/modules/core_gateway/{__init__,module,settings}.py` + `services/__init__.py`.
- `settings.py`: SCHEMA = `tavily_api_key` + `firecrawl_api_key` (StrField secret=True),
  хелпер `service_api_key(field_key)` через `get_module_store("core_gateway")`.
- `CoreGatewayModule(Module)` — только `settings_schema`; ни таблиц, ни миграций,
  ни роутеров, ни задач, ни реестра (по запросу).
- Зарегистрирован в `apps/app/modules.py::build_modules` (после core_setup).

Шаг 2 — сервис Tavily (services/tavily/):
- `params.py` — модель параметров на запрос: `TavilySearchParams` (полный набор
  полей search по докам), `TavilyExtractParams`, `TavilyMapParams`; общий базовый
  `_TavilyParams.to_payload()` = `model_dump(exclude_none=True)` (шлюз не навязывает
  дефолты).
- `gateway.py` — `TavilyGateway` с `search/extract/map/crawl(params) -> нативный JSON`
  + `usage()` (баланс, `GET /usage`, остаток = `account.plan_limit - plan_usage`);
  ключ из настроек, `Authorization: Bearer`; `BASE_URL`/`API_KEY_FIELD` = константы
  класса, `timeout` — в конструкторе (constants.py убран как файл-ради-файла).
- Все 4 модели заполнены по докам (search/extract/map/crawl); общие поля обхода
  map/crawl вынесены в базу `_TavilyTraversalParams`.

Дополнение — сервис Firecrawl (services/firecrawl/), зеркало Tavily:
- `params.py` — `FirecrawlScrapeParams`/`SearchParams`/`MapParams`/`CrawlParams`;
  Firecrawl принимает camelCase → snake_case-поля + `alias_generator=to_camel`,
  `to_payload()`=`model_dump(by_alias=True, exclude_none=True)`. `FirecrawlScrapeOptions`
  (скрейп без url) переиспользуется как вложенный `scrape_options` в search/crawl.
- `gateway.py` — `FirecrawlGateway.scrape/search/map(params)` (POST `/v2/*`) +
  `crawl` (async → `{id,url}`) + `crawl_status(job_id)` (GET) + `usage()`
  (`GET /v2/team/credit-usage` → `remainingCredits`/`planCredits`).
- Живой usage-чек через оба шлюза: Tavily 14/1000, Firecrawl 945/1000.

Тумблеры включения (по запросу):
- Новый **BoolField** в ядре настроек (`core/_settings/fields.py` + экспорт в
  `core/settings.py`; хранение `"true"/"false"`) + фронт-компонент
  `web/src/components/settings/SettingFieldBool.vue` (VSwitch) + диспетчер
  `SettingField.vue` + тип `BoolFieldDescriptor`/`'bool'` в `features/settings/api.ts`.
- `core_gateway.settings`: пары `tavily_gateway_enabled`/`firecrawl_gateway_enabled`
  (BoolField, default True) перед `*_api_key`; хелпер `service_enabled(field_key)`.
- Шлюзы: `ENABLED_FIELD` на классе + `_ensure_enabled()` в `_request` → `RuntimeError`
  до сети, если выключен.
- Тесты: `test_bool_roundtrip_and_validation` (`tests/core/_settings/test_fields.py`).
  `--core` 266 passed; vue-tsc clean; `web/dist` пересобран.

Проверка: импорт-смоук (схема валидна, секреты маскируются, payload'ы содержат
только заданные поля, modules = [core_setup, core_gateway, core_monitoring,
web_content]); `uv run pytest --core` — 265 passed. Автотестов модуля пока нет
(добавить при вайринге потребителя).

## Result

Создано: `src/modules/core_gateway/` (`__init__.py`, `module.py`, `settings.py`,
`services/__init__.py`, `services/tavily/{__init__,constants,params,gateway}.py`).
Изменено: `src/apps/app/modules.py` (регистрация CoreGatewayModule).

Токены — единственный дом в core_gateway (по запросу «убери из веб-документов»):
- Убраны `tavily_api_key`/`firecrawl_api_key` из web_content `SCHEMA` +
  удалён `provider_api_key`; `providers/{tavily,firecrawl}/client.py` читают ключ
  через `core_gateway.settings.service_api_key`. Тест `test_schema_has_no_api_tokens`.
- Dev-БД: значения ключей уже были в core_gateway (35/58) — миграция не нужна;
  старые web_content-строки токенов осиротели (инертны, store их игнорирует).
- Живой API + скрин: карточка «Веб-документы» больше без полей токенов; core_gateway
  держит тумблеры + ключи. `--module=web_content --core` 314 passed.

Полный вайринг web_content на шлюзы (по запросу):
- `providers/{tavily,firecrawl}/client.py` переписаны из HTTP-движков в **адаптеры
  над core_gateway**: строят модель params, зовут `gateway.search/extract`|`search/scrape`,
  мапят нативный ответ в web_content-форму. Убраны httpx/`_key()`/base-url — HTTP,
  ключ и тумблер целиком в шлюзе. Провайдер держит `self.gateway` (в `__init__`).
- Тумблер `*_gateway_enabled=False` теперь распространяется на конвейер: gateway
  бросает → handler ловит как сбой движка (`search_mark_error`, retry→fail).
- Тесты handler'а используют `_StubProvider` (сеть не трогают) → правок не потребовали.
  `--module=web_content --core` 314 passed. Live-смоук обоих: Tavily search(2)+inline
  content + extract(25K md); Firecrawl search(2)+scrape(28K md).

Открыто:
- Автотесты самого core_gateway (сейчас косвенно: web_content-стабы + live-смоук).
