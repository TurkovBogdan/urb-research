---
title: xAI (Grok) — поиск контента
date: 2026-07-05
description: "Поверхности xAI для поиска контента: Agent Tools API (web_search / x_search / code_execution / collections_search) на /v1/responses, multi-agent deep research, формат цитат. По докам docs.x.ai; живьём НЕ гоняли (нет ключа/кредитов)."
tags: [external-service, ingestion]
---

## Scope

По официальным докам `docs.x.ai` + **живые прогоны** (ключ в dev-настройках; верстак
`dev/bench/core_connectors/xai/`): `web_search` (`tmp/search.json`), `x_search`, multi-agent
(`agent_count=4`), read-методы (`models`/`language_models`/`model`/`api_key_info`), `tokenize`,
`responses` store→get→delete.
База `https://api.x.ai`, аутентификация `Authorization: Bearer <XAI_API_KEY>`.
Актуальная поверхность поиска — **Agent Tools API** на эндпойнте `POST /v1/responses`
(server-side инструменты, автономный агент-луп). Разобраны: `web_search`, `x_search`,
`code_execution`/`code_interpreter`, `collections_search`, multi-agent deep research, реальная
форма `output[]`/`annotations[]`/`usage`, каталог моделей, снятие legacy Live Search.
**Живьём не гоняли:** `collections_search` (нет коллекций), `enable_image_*`.

## Findings

- **Эндпойнт — `POST /v1/responses`** (Responses API, OpenAI-совместимый). Инструменты
  включаются массивом `tools: [{"type": "web_search"}, …]`; сервер сам гоняет **агентский цикл**
  (анализ запроса → tool call → парс результатов → доп. запросы → финальный ответ). Клиент только
  конфигурирует инструменты, исполнение — на стороне xAI. `/v1/chat/completions` — **legacy**.
- **Инструменты (server-side, built-in):** `web_search` (поиск + браузинг страниц в реальном
  времени), `x_search` (поиск по X/Twitter), `code_execution` (в Python-SDK `code_interpreter` —
  запуск Python), `collections_search` (RAG по загруженным коллекциям/файлам). Плюс обычный
  function calling (пользовательские функции) — тарифицируется как токены, не как built-in-вызов.
- **`web_search` — конфиг:** `filters.allowed_domains` (**≤5** доменов) **или**
  `filters.excluded_domains` (≤5) — **вместе нельзя**; `enable_image_search` (Grok ищет картинки и
  вставляет `![alt](url)` в текст), `enable_image_understanding` (включает `view_image` — анализ
  найденных картинок). Параметров max-results / страна / safe-search в доках нет.
  Форма запроса: `{"type": "web_search", "filters": {"allowed_domains": [...]}}`.
- **`x_search` — конфиг:** `allowed_x_handles` / `excluded_x_handles` (**≤20**),
  `from_date` / `to_date` (**ISO8601 `YYYY-MM-DD`**, ограничение диапазона),
  `enable_image_understanding`, `enable_video_understanding`. Режимы: keyword / semantic / user
  search / thread fetch (управляются моделью автономно, отдельных флагов режима нет).
- **Реальная форма ответа (сверено вживую, grok-4.3 + web_search).** Топ-уровня `citations` /
  `output_text` в сыром REST **НЕТ** — это удобства SDK. Есть `output[]` — гетерогенный список
  типизированных блоков: `reasoning` (сводки размышлений), по блоку `web_search_call` на каждый
  поиск (`{id, status, action:{type:"search", query, sources:[{type:"url", url}]}}`) и финальный
  `message` (`role:"assistant"`), чей `content[]` несёт блок `output_text` с полями `text` +
  `annotations[]`. Плюс `usage`, `status`, эхо `tools`/`model`.
- **Цитаты — только URL (ключевой факт для дизайна хранилища).** Два источника URL в ответе:
  (1) финальные цитаты = `output[-1].content[].annotations[]`, объект
  `{type:"url_citation", url, start_index, end_index, title}` (`title` = метка-номер «1»/«2»,
  индексы = Python-slice в `text`); (2) все посещённые агентом URL = объединение
  `web_search_call.action.sources[].url` (из них SDK и собирает свой `.citations`). **Ни тела,
  ни сниппета, ни даты** источника нет — бакет C: нужен доскрейп URL через движок A
  (Firecrawl/Tavily extract). См. `AGENTS/obsidian/sources-engines.md`.
- **`usage` (живой пример).** `input_tokens`/`output_tokens` (+`_details`, вкл. `reasoning_tokens`,
  `cached_tokens`), `num_server_side_tools_used`, `server_side_tool_usage_details`
  (`web_search_calls`/`x_search_calls`/`code_interpreter_calls`/…), `cost_in_usd_ticks`
  (USD·10¹⁰ — 375440000 ≈ $0.0375 за прогон с 4 web_search). `num_sources_used` может быть 0 при
  непустых annotations.
- ⚠ **`search_context_size` НА ВХОД НЕ ПРИНИМАЕТСЯ** (сверено): передача в tool → `400
  {"error":"Argument not supported: search_context_size"}`. Оно лишь в *эхо* ответа как дефолт
  xAI (`medium`) — читать можно, задавать нельзя.
- **Structured output + web_search (сверено, ключевой паттерн).** `text.format` =
  `{type:"json_schema", name, strict:true, schema}` вместе с `tools:[{"type":"web_search"}]` →
  `200`. Grok ищет, **сам отбирает/ранжирует** и возвращает строгий JSON. Проверка заземления
  (схема `{links:[{url,title,reason,relevance}]}`, запрос «очереди на Python»): из 30 найденных
  вернул 8, **8/8 URL — из реального поиска** (не выдуманы), отсортированы по relevance, мусор
  (youtube/reddit) отсеян. Root схемы должен быть `object`; в strict все поля — в `required`,
  `additionalProperties:false`.
- **`x_search` (сверено).** Работает через тот же `/v1/responses`; в `output[]` вызов всплывает
  блоком **`custom_tool_call`** (не `x_search_call`), надёжный счётчик —
  `usage.server_side_tool_usage_details.x_search_calls`.
- **Multi-agent deep research** — отдельная **модель**, не инструмент:
  `model="grok-4.20-multi-agent"` (алиас → `grok-4.20-multi-agent-0309`). Запускает несколько
  агентов (leader синтезирует финал), `agent_count` = **4** или **16** — **сверено вживую как
  топ-уровневое поле `/v1/responses`** (не только SDK): ответ `status=completed`, echo
  `model=grok-4.20-multi-agent`. Контекст **2M**. Инструменты (`web_search`/`x_search`/…)
  опциональны — работает и на одних знаниях.
- **Каталог моделей (сверено `models()`/`model()`).** Канонические id: `grok-4.3` (алиасы
  `grok-4.3-latest`/`grok-latest`, 1M), `grok-4.20-0309-reasoning`, `grok-4.20-0309-non-reasoning`,
  `grok-4.20-multi-agent-0309`, `grok-build-0.1`. `model()` даёт `context_length`, `aliases[]` и
  цены в мини-единицах (`prompt_text_token_price`=12500 / `completion_text_token_price`=25000 для
  grok-4.3 → $1.25 / $2.50 за 1M). `tokenize` → `token_ids[{token_id,string_token,token_bytes}]`.

## Billing / баланс — отдельный Management API (сверено ЖИВЬЁМ 2026-07-06)

- **Inference-API (`api.x.ai`) баланс НЕ отдаёт.** `GET /v1/api-key` — только права (`acls`) и
  статусные флаги; `GET /v1/models` — пер-модельные цены; фактический расход — пост-фактум в
  `usage.cost_in_usd_ticks` каждого ответа. Остатка/предоплаты тут нет принципиально.
- **Баланс живёт в Management API** — **другой базовый URL** `https://management-api.x.ai` и
  **отдельный Management Key** (Console → Settings → Management Keys; право *Management Keys Read* /
  billing). Аутентификация та же — `Authorization: Bearer <management_key>`. Ключ ≠ `xai_api_key`.
- **team_id** — берём из inference `api_key_info().team_id` (у нас `a838c37e-…`), доп. конфига не надо.
- **Эндпойнты биллинга (всё в USD-центах, суммы — строки в `amount.val`/`total.val`):**
  - Остаток предоплаты — `GET /v1/billing/teams/{team_id}/prepaid/balance` → `total.val` + `changes[]`.
  - Лимиты трат — `GET /v1/billing/teams/{team_id}/postpaid/spending-limits` → `spendingLimits.{effectiveHardSl,effectiveSl,hardSlAuto}.val`.
  - Превью текущего счёта — `GET /v1/billing/teams/{team_id}/postpaid/invoice/preview` → `coreInvoice` + `billingCycle`.
  - Историческое потребление — `POST /v1/billing/teams/{team_id}/usage` → `timeSeries[]` + `limitReached`.
- ⚠ **ЗНАК ИНВЕРТИРОВАН (ключевая гоча, сверено живьём).** В `changes[]`: пополнения
  `changeOrigin:"PURCHASE"` идут с **отрицательным** `amount.val`, списания `changeOrigin:"SPEND"` — с
  **положительным**. Неуспешные топапы (`topupStatus:"FAILED_TO_CHARGE"`) в `total` **не** входят.
  `total.val` = сумма успешных изменений → **остаток кредитов = −`total.val`** (пример: `total.val="-602"`
  → на балансе $6.02). PURCHASE несёт `topupStatus`/`invoice_number`/`paymentProcessor`; SPEND —
  `spendBpKeyYear`/`spendBpKeyMonth` (период), `createTime:null` но `createTs` заполнен.
- **Лимиты (сверено):** у prepaid-only команды `spending_limits` все нули (`effectiveHardSl/effectiveSl/hardSlAuto = 0`)
  — постоплата не настроена. Значит «сколько ещё можно потратить» = только prepaid-остаток.
- **Проверено гейтвеем** `XaiManagementGateway` (`prepaid_balance`/`spending_limits`), бенч
  `dev/bench/core_connectors/run_balances.py` (сырьё `tmp/balance_xai.json`). Docs:
  https://docs.x.ai/developers/management-api-guide · https://docs.x.ai/developers/rest-api-reference/management/billing

## Limits / quirks

- ☠ **Legacy Live Search снят.** `search_parameters` в `POST /v1/chat/completions` → **HTTP 410 Gone**
  `{"error":"Live search is deprecated. Please switch to the Agent Tools API"}` с 12.01.2026. Массово
  поломал интеграции (LangChain `langchain-xai`, Make.com, Dify, Cherry Studio). Не закладываться —
  использовать только Agent Tools на `/v1/responses`.
- **Биллинг = токены + вызовы инструментов.** Built-in-инструменты тарифицируются **за вызов сверх
  токенов**: web_search / x_search / code_execution — **$5 / 1000 вызовов**, file/attachments search —
  $10/1000, collections_search (RAG) — $2.50/1000. В агентском режиме **число вызовов решает модель**
  (один запрос может дать 5 поисков + 2 code-exec) → стоимость масштабируется сложностью, не числом
  реквестов. Плюс найденный контент возвращается в модель как **платные input-токены**.
- **Модели (актуально середина-2026, докам):** флагман `grok-4.3` — 1M контекст, **$1.25/1M in,
  $2.50/1M out**; `grok-4.20-0309-reasoning`/`-non-reasoning` (1M, та же цена); `grok-4.20-multi-agent`
  (2M); `grok-build-0.1` (256k, $1.00/$2.00). **Knowledge cutoff — ноябрь 2024** → без search-инструментов
  свежих данных нет.
- `allowed_domains` и `excluded_domains` **взаимоисключающие** в одном запросе (лимит 5 доменов).
- Цены/доступность моделей плавают и зависят от региона — сверять по `docs.x.ai` и консоли перед
  прод-интеграцией; здесь не мерено живьём.

## References

- Docs: https://docs.x.ai/developers/tools/overview · /web-search · /x-search · /citations
- Multi-agent: https://docs.x.ai/developers/model-capabilities/text/multi-agent ·
  модель https://docs.x.ai/developers/models/grok-4.20-multi-agent-beta-0309
- Модели/цены: https://docs.x.ai/developers/models
- Снятие Live Search (410): https://community.make.com/t/x-ai-node-integration-error-410-live-search-deprecated-switch-to-agent-tools-api/102097 · анонс grok-4.1-fast/Agent Tools https://x.ai/news/grok-4-1-fast
- Python SDK: https://github.com/xai-org/xai-sdk-python
- Живой верстак: `dev/bench/core_connectors/xai/` (`run_search.py` + `tmp/search.json`)
- Каталог движков и классификация A/B/C (xAI = бакет C): `AGENTS/obsidian/sources-engines.md`
