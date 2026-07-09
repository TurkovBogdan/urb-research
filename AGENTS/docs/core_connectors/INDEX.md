# core_connectors — hub

Инфраструктурный (`core_*`) модуль-коннектор к внешним API: тонкие коннекторы к сервисам
(Tavily, Firecrawl, …) + хранение их кредов как runtime-настроек. Своего домена,
таблиц, миграций, роутеров, задач и реестра **нет** (по мере надобности добавляется).

## Границы и контракт

- **Коннектор = тонкий проброс к API.** Отдаёт **нативный ответ сервиса** (как есть),
  без доменного маппинга — форму под конкретного потребителя строит сам потребитель.
- **Никакой оркестрации в коннекторе** — очереди/статусы/reclaim/семафоры остаются в
  доменном модуле-потребителе (напр. web_search-адаптеры).
- **Ключ коннектор берёт сам** из настроек core_connectors по своему полю; потребитель
  кредов не касается.
- **Креды — runtime-настройки, не ENV** (`StrField(secret=True)`, маскируются на
  чтение, правятся на `/core/settings`). ENV — только bootstrap до БД; внешние API
  сюда не попадают.

## Структура

- `settings.py` — `SCHEMA`: на сервис пара — `*_gateway_enabled` (BoolField, default
  `True`) + `*_api_key` (StrField secret). У xAI ещё второй секрет `xai_management_api_key`
  (биллинг-поверхность, см. services/xai). Хелперы `service_api_key(field_key)` и
  `service_enabled(field_key)` (чтение через `get_module_store("core_connectors")`;
  вне загруженного store — ключ пустой / enabled=True).
- `services/base.py` — **`ServiceGateway`**, общая база всех гейтвеев: HTTP-обвязка
  (`_request`/`_post`, один `httpx.AsyncClient` на вызов; query — через `params`), гейт
  `_ensure_enabled`/`_key`, авторизация — переопределяемый `_auth_headers()` (default
  `Authorization: Bearer`; Anthropic → `x-api-key`+`anthropic-version`). Подкласс объявляет
  ClassVar-ы поверхности — `SERVICE`/`NAME`/`DESCRIPTION`/`BASE_URL`/`API_KEY_FIELD`, опц.
  `TIMEOUT` (default 60) и `ENABLED_FIELD`.
- **Выключение:** если `ENABLED_FIELD` задан и `*_gateway_enabled=False`, коннектор бросает
  `RuntimeError` до сети (`_ensure_enabled` в `_request`). `ENABLED_FIELD=None` → гейт
  только по наличию ключа (`_key` бросает на пустом) — так у management-гейтвея xAI.
- **Один вендор → возможно несколько гейтвеев** (поверхностей): у каждого свои `BASE_URL`
  и `API_KEY_FIELD`. Пример — xAI: инференс (`api.x.ai`) + management/биллинг (`management-api.x.ai`).
- `module.py` — `CoreConnectorsModule(Module)`, только `settings_schema`.
- `services/<service>/` — по папке на сервис.

## Реестр коннекторов + баланс

Домен — **коннекторы** (по одному на вендор), а не «баланс»: `services/` — лишь раскладка
файлов. Реестр отдаёт паспорт каждого коннектора + опционально баланс; баланс — одна из
возможностей, не суть реестра.

- **Паспорт на базе:** `ServiceGateway` держит `SERVICE` (код), `NAME`, `DESCRIPTION` (заменили
  прежний `LABEL`; `NAME` идёт и в тексты ошибок), плюс `HAS_BALANCE`/`available()`.
- **Единый метод баланса:** `async ServiceGateway.balance() -> ConnectorBalance` — общая логика
  (гейт по `HAS_BALANCE` + оркестрация `_fetch_balance` → `_parse_balance`); подкласс задаёт лишь
  запрос и маппинг. `HAS_BALANCE=True` у `TavilyGateway`/`FirecrawlGateway`/`XaiGateway`; инференс
  **`XaiGateway.balance()` делегирует** `XaiManagementGateway` (баланс — на management-поверхности;
  ленивый импорт рвёт цикл, т.к. management тянет inference за `team_id`).
- **DTO (`services/dto.py`, чистый модуль без внутренних импортов):**
  - `ConnectorInfo` — паспорт: `service`, `name`, `description`, `enabled`, `has_balance`.
  - `ConnectorBalance` — `service`/`name` + **список метрик** `metrics: list[BalanceMetric]` +
    `error`. У коннектора может быть несколько независимых показателей (баланс, лимит ключа,
    кредиты — одно другое не отменяет), выводим что доступно.
  - `BalanceMetric` — одна метрика: `label` («Баланс»/«Кредиты»/…) + денежная величина
    (`amount`+`currency`) ИЛИ «использовано из всего» (`used`/`total`/`used_percent`(0..100)+
    `unit`). Фабрики `BalanceMetric.money(label, amount)` и `BalanceMetric.usage(label, used,
    total, unit)` (сама считает %).
  - `ConnectorView` — композиция `info` + опциональный `balance`.
- **Реестр `registry.py::ConnectorsRegistry`** (в **корне модуля**, не в `services/` — домен ≠
  раскладка файлов) + синглтон `connectors_registry` (регистрирует **по коннектору на вендор**:
  Tavily/Firecrawl/`XaiGateway`/`OpenRouterGateway`/`OpenAIGateway`/`AnthropicGateway` — management не отдельный коннектор): `connectors(*,
  with_balance=False) -> list[ConnectorView]` параллельно (`asyncio.gather`); баланс снимается
  только у включённых и умеющих (`with_balance=True`), сбой одного → `error` в его DTO, остальные
  не падают. `all()`/`info(c)` — синхронный паспорт. DTO (`ConnectorInfo`/`ConnectorBalance`/
  `ConnectorView`) экспортируются из `services/__init__` (живут в `services/dto.py`).
- **API + фронт:** internal-роутер модуля (`api/connectors.py`) — `GET /connectors` →
  `list[ConnectorView]` (баланс вживую, `with_balance=True`). Фронт-фича
  `web/src/features/core_connectors` (страница `/connectors` карточками — раздел «Мониторинг»,
  **первой перед «Задачи»**; компонент `ConnectorBalance.vue` рендерит **массив метрик**
  (`metrics`) — на метрику строка: `label` + значение (деньги ИЛИ «использовано / всего» +
  `% использовано`) + бар. `error`/`placeholder` — отдельные строки. **Единая вёрстка карточек:**
  описание фиксировано на 3 строки (line-clamp), блок баланса единый — **бар всегда** (пустой для
  денег/ошибки/«нет баланса») → карточки в ряду выровнены по высоте.
- ⚠ **xAI знак:** `_parse_balance` инвертирует — остаток `amount = −total.val/100` (см. services/xai).
  team_id внутри `XaiManagementGateway._fetch_balance` резолвится из инференс `api_key_info()`.

## services/tavily

Тонкий коннектор Tavily + модели параметров запросов.

- `params.py` — модель на запрос (полный набор полей по докам): `TavilySearchParams`,
  `TavilyExtractParams`, `TavilyMapParams`, `TavilyCrawlParams`; общие поля обхода
  дерева (`max_depth`/`max_breadth`/`limit`/select-exclude paths+domains/`allow_external`/
  `instructions`) вынесены в базу `_TavilyTraversalParams` (наследуют map и crawl).
  `to_payload()` = `model_dump(exclude_none=True)` (незаданные поля опускаются,
  дефолты — на стороне Tavily).
- `gateway.py` — `TavilyGateway.search/extract/map/crawl(params) -> нативный JSON`
  (POST) + `usage() -> JSON` (баланс, `GET /usage`); `BASE_URL` = константа класса,
  `timeout` переопределяется в конструкторе; поле ключа `API_KEY_FIELD`;
  `Authorization: Bearer`, ключ из настроек.
- **Баланс:** `GET /usage` (метод `usage()`) → `{key:{usage,limit,<method>_usage…},
  account:{current_plan, plan_usage, plan_limit, paygo_*, …}}`; остаток кредитов =
  `account.plan_limit - account.plan_usage`.

## services/firecrawl

Тонкий коннектор Firecrawl + модели параметров. Firecrawl принимает **camelCase** — модели
держат snake_case + `alias_generator=to_camel`, `to_payload()` = `model_dump(by_alias=True,
exclude_none=True)`.

- `params.py` — `FirecrawlScrapeParams`/`SearchParams`/`MapParams`/`CrawlParams`;
  `FirecrawlScrapeOptions` = поля скрейпа без `url` (readability `only_main_content`, JS
  `wait_for`/`actions`, анти-бот `proxy`, кэш `max_age`, …), переиспользуются как
  вложенный `scrape_options` в search/crawl (`FirecrawlScrapeParams` = options + url).
- `gateway.py` — `FirecrawlGateway.scrape/search/map(params) -> JSON` (POST `/v2/*`) +
  `crawl(params)` (async → `{id,url}`) + `crawl_status(job_id)` (GET) + `usage()`
  (баланс). `BASE_URL`/`API_KEY_FIELD` = константы класса, `timeout` — в конструкторе.
- **Баланс:** `GET /v2/team/credit-usage` (метод `usage()`) →
  `data.remainingCredits`/`data.planCredits` + границы биллинг-периода.

## services/web_scrapper

Тонкий коннектор к **локальному** демону `daemon-web-scrapper` (браузерный скрейпер,
порт **19020**) — только скрейп
страниц в markdown (поиска нет). Код коннектора = `web_scrapper`, имя = `daemon-web-scrapper`.
`BASE_URL = http://127.0.0.1:19020` (порт фиксирован в реестре демонов, ClassVar-константа).
**Баланса нет** (`HAS_BALANCE=False`) → в `connectors_registry` НЕ регистрируется (нет карточки на `/connectors`).

- `params.py` — `WebScrapperScrapBatchParams` (`urls` + опц. `mode`/`timeout`/`load_timeout`/
  `scroll_timeout`); `to_payload()` = `model_dump(exclude_none=True)`, дефолты применяет демон.
- `gateway.py` — `WebScrapperGateway.scrap_batch(params) -> JSON` (POST `/api/1.0/scrap-batch`
  → `{results: [<scrap>], elapsed_ms}`, каждый `<scrap>` = `{outcome, url, final_url, content, …}`,
  `content` = markdown главного контента страницы). **Auth опциональна:** `_auth_headers()`
  переопределён — Bearer только при заданном `web_scrapper_api_key`, пустой ключ = демон без
  авторизации (`SCRAPER_API_KEY` пуст, локальный dev), а не падение как в базе.
- Настройки: `web_scrapper_gateway_enabled` (BoolField, default True) + `web_scrapper_api_key`
  (StrField secret, опц.). Потребитель — фетч-движок `web_search.providers/web_scrapper`.

## services/xai

Тонкий коннектор xAI (Grok). **Форма отличается от tavily/firecrawl**: у xAI НЕТ отдельных
search-эндпойнтов — «поиск контента» это инференс `POST /v1/responses` с массивом
server-side `tools`; ответ = синтез модели + `citations[]` (**только URL**, без тел/сниппетов;
бакет C, см. `AGENTS/research/xai/INDEX.md`). snake_case (OpenAI-совместимо) — алиасы не нужны.

- `constants.py` — id моделей (`GROK_FLAGSHIP`=grok-4.3, `GROK_MULTI_AGENT`=grok-4.20-multi-agent,
  reasoning/non-reasoning/build) + `MULTI_AGENT_COUNTS=(4,16)`. Pinned-версии ротируются — предпочитать алиасы.
- `params.py` — `XaiResponsesParams` (model/input/tools/tool_choice/max_output_tokens/reasoning/
  `text`/previous_response_id/…) + `XaiTokenizeParams` + хелпер `json_schema_text(name, schema,
  strict=True)`. Инструменты — модели `Xai{WebSearch,XSearch,CodeExecution,CollectionsSearch}Tool`
  (+ `XaiWebSearchFilters`) поверх базы `_XaiTool` (`extra="allow"` — несверённые поля/сырые dict
  проходят насквозь). В `tools` сериализуются через `SerializeAsAny` → в список можно класть и
  типизированные модели, и dict. web_search: домены в `filters.{allowed,excluded}_domains` (≤5,
  взаимоисключающи), `enable_image_*` — на верхнем уровне tool (⚠ `search_context_size` на вход
  НЕ принимается — 400; только в эхо ответа). x_search: `{allowed,excluded}_x_handles` (≤20),
  `from_date`/`to_date` (ISO8601).
- **Строгий вывод (structured output).** `text=json_schema_text(name, schema)` →
  `text.format={type:"json_schema",strict:true,…}`; работает вместе с `web_search` (Grok-4). Схема:
  root=`object`, все поля в `required`, `additionalProperties:false`. Паттерн «релевантные ссылки»:
  web_search + строгий массив → Grok сам ищет/ранжирует/отбирает, URL **заземлены** (сверено 6/6, 8/8).
- **Две поверхности = два гейтвея** (оба поверх `ServiceGateway`):
- `gateway.py` — `XaiGateway` (**инференс**, `api.x.ai`, ключ `xai_api_key`, тумблер
  `xai_gateway_enabled`, `TIMEOUT`=300с): `responses(params)` (ядро, POST `/v1/responses`) +
  `get_response`/`delete_response` (GET/DELETE `/v1/responses/{id}`, хранится 30д) +
  `tokenize` (POST `/v1/tokenize-text`) + `models`/`language_models`/`model(id)` (каталог) +
  `api_key_info()` (GET `/v1/api-key` — статус/права + `team_id`; **баланс сам не отдаёт**).
- `management.py` — `XaiManagementGateway` (**биллинг**, `management-api.x.ai`, отдельный ключ
  `xai_management_api_key`, тумблера нет — гейт по наличию ключа). Все суммы — **USD-центы**;
  `team_id` в пути (берётся из `XaiGateway.api_key_info().team_id`, резолвит потребитель):
  `prepaid_balance(team_id)` (GET `…/prepaid/balance` → `total` + `changes[]`) +
  `spending_limits(team_id)` (GET `…/postpaid/spending-limits` → `effectiveHardSl`/`softSl`/`effectiveSl`) +
  `invoice_preview(team_id)` (GET `…/postpaid/invoice/preview`). Детали → `AGENTS/research/xai/INDEX.md`.
- **Не покрыто (вне задачи поиска):** медиагенерация (`/v1/images|videos`), voice/TTS, files,
  embeddings; legacy `/v1/chat/completions` (снятый Live Search) — только Responses API.

## services/openrouter

Коннектор OpenRouter — **только баланс** (не инференс: полный провайдер из semaphore-core не
тянем). `OpenRouterGateway(ServiceGateway)`: `openrouter.ai/api/v1`, ключ `openrouter_api_key`,
тумблер `openrouter_gateway_enabled`. Настройки — пока runtime-секрет (как у прочих; миграция на
ENV — когда у модуля появится env-хранилище). Баланс = **две метрики** (сверено живьём,
`AGENTS/research/openrouter/INDEX.md`):
- «Лимит ключа» — `GET /api/v1/key` → `data.usage` из `data.limit` (использовано/потолок, USD);
- «Баланс» — `GET /api/v1/credits` → `total_credits − total_usage` (может быть отрицательным).
`_fetch_balance` тянет оба (`/credits` — best-effort: сбой → остаётся метрика лимита); `limit=null`
(безлимитный ключ) → метрика лимита опускается.

## services/openai

Коннектор OpenAI — **только расход** (остатка баланса у OpenAI через API нет — `credit_grants`
только session-токен; `AGENTS/research/openai/INDEX.md`). `OpenAIGateway(ServiceGateway)`:
`api.openai.com/v1`, **Admin-ключ** `openai_admin_api_key` (обычный `sk-…` → 403; тумблер
`openai_gateway_enabled`). Метрика «Расход {N}д» (`SPEND_WINDOW_DAYS=30`): `GET /organization/costs`
(bucket 1d, `start_time`=now−N дней) → `Σ data[].results[].amount.value` (доллары, `BalanceMetric.money`).
Query-параметры идут через `_request(..., params=…)` (добавлено в базу).

## services/anthropic

Коннектор Anthropic (Claude) — **только расход** (остатка баланса нет; `AGENTS/research/anthropic/INDEX.md`).
`AnthropicGateway(ServiceGateway)`: `api.anthropic.com/v1`, **Admin-ключ** `anthropic_admin_api_key`
(`sk-ant-admin…`; тумблер `anthropic_gateway_enabled`). ⚠ **Auth иная** — не `Bearer`, а `x-api-key` +
`anthropic-version: 2023-06-01` (переопределён `_auth_headers`; ради этого база вынесла авторизацию
в `_auth_headers()`). Метрика «Расход {N}д»: `GET /organizations/cost_report` (bucket 1d,
`starting_at`=now−N дней, RFC3339) → **`Σ float(results[].amount) / 100`** — ⚠ `amount` строка в
**ЦЕНТАХ** (в отличие от OpenAI — там доллары-строка).

## Статус / открытое

- Живой контент-бенч Tavily vs Firecrawl: Firecrawl `onlyMainContent` чище и покрывает
  больше (18/19 против 11/19), см. заметку `second-brain/06 - Projects/urb-research/`.
- **web_search провязан на коннекторы**: `providers/{tavily,firecrawl}/client.py` — теперь
  тонкие адаптеры над `core_connectors` (строят params, зовут gateway, мапят нативный ответ
  в web_search-форму). HTTP/ключ/тумблер — целиком в коннекторе; сам провайдер httpx не
  трогает. Тумблер `*_gateway_enabled=False` → коннектор бросает → handler трактует как
  сбой движка (`query_mark_error`, retry→fail). Сквозной live-прогон обоих подтверждён.
- Не сделано: автотесты модуля core_connectors (сейчас покрыт косвенно через web_search
  на стабах + live-смоук).

Задача: [`2026-07-04-core-gateway-module`](../../tasks/2026-07-04-core-gateway-module.md).
