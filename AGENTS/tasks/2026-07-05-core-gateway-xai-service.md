---
title: core_gateway xAI service
date: 2026-07-05
status: completed
description: "Add an xAI (Grok) gateway to core_gateway: Responses API (agentic web_search/x_search) + auxiliary read methods, with typed param/tool models and model-id constants. Following the tavily/firecrawl service pattern."
tags: [core_gateway, xai, ingestion]
---

## Task

«Создать шлюз, в котором есть полный набор их методов и все нужные модели» — коннектор к xAI
внутри `core_gateway`, для методов поиска контента.

## Context

Токен xAI уже добавлен в `settings.py` (`xai_gateway_enabled` + `xai_api_key`, задача от 2026-07-05).
Ресёрч xAI (`AGENTS/research/xai/INDEX.md`) показал: у xAI нет отдельных search-эндпойнтов — поиск
это `POST /v1/responses` с `tools:[{"type":"web_search"}|{"type":"x_search"}|…]`, ответ = синтез
модели + `citations[]` (только URL). Форма шлюза отличается от tavily/firecrawl (там REST-search).

## What was done

- `services/xai/` по паттерну tavily/firecrawl: `constants.py` (id моделей + agent-counts),
  `params.py` (XaiResponsesParams/XaiTokenizeParams + модели инструментов web_search/x_search/
  code_execution/collections_search поверх базы `_XaiTool` c `extra="allow"`; tools через
  `SerializeAsAny`), `gateway.py` (`XaiGateway`: responses/get_response/delete_response/tokenize/
  models/language_models/model/api_key_info), `__init__.py` (реэкспорт).
- Смоук-скрипт: сериализация вложенных tools + сырого dict-passthrough корректна (exclude_none
  пробрасывается). `--core` 266 passed.
- Доку модуля `docs/core_gateway/INDEX.md` дополнил секцией `services/xai` + memory-роутер.

## Problems

xAI не ложится в форму `SearchProvider.search()` как Tavily/Firecrawl: нет search-эндпойнта,
поиск = инференс `/v1/responses` с tools, ответ = синтез + `citations[]` (только URL). Шлюз
построен вокруг Responses API, метод — `responses()`, а не `search()`. Медиа/voice/files/
embeddings/legacy chat-completions намеренно не покрыты.

## Result

Новые файлы: `src/modules/core_gateway/services/xai/{__init__,constants,params,gateway}.py`.
Изменены: `src/modules/core_gateway/settings.py` (токен, предыдущий шаг),
`AGENTS/docs/core_gateway/INDEX.md`, `AGENTS/memory/MEMORY.md`.
Открыто: автотестов у core_gateway нет; `x_search`/`collections_search`/multi-agent живьём не гоняли.

## Живой прогон (ключ в dev-настройках)

Верстак `dev/bench/core_gateway/xai/` (bootstrap поднимает dev-sqlite + module store, затем
`XaiGateway().responses()`). `run_search.py` (grok-4.3 + web_search) отработал: `status=completed`,
4 web_search-вызова, осмысленный ответ + 6 url_citation.

Уточнения против доки (внесены в research + докстринги):
- В сыром REST **нет** топ-уровневых `citations`/`output_text` (это SDK-удобства). Реально:
  `output[]` = `reasoning` + `web_search_call`(`action.sources[].url`) + финальный `message`
  (`content[].text` + `content[].annotations[]` = `url_citation`). Все посещённые URL — в
  `web_search_call.action.sources[]`.
- `usage` несёт `num_server_side_tools_used`, `server_side_tool_usage_details.web_search_calls`,
  `cost_in_usd_ticks` (USD·10¹⁰; 375440000 ≈ $0.0375 за прогон).
- Добавил `search_context_size` (low|medium|high) в `XaiWebSearchTool` — xAI дефолтит `medium`.

## Полировка + полная верификация поверхности (2026-07-05, тот же ключ)

Верстак: `verify_surface.py` (read-методы + tokenize + responses store→get→delete) и
`verify_variants.py` (multi-agent + x_search). Все методы шлюза отработали живьём:
- `api_key_info`/`models`/`language_models`/`model(id)`/`tokenize` — пути верны, формы сняты.
  Каталог моделей совпал с константами; `model()` даёт `context_length`/`aliases`/цены.
- `responses` store→get→delete — полный цикл ок (`delete`→`{deleted:true}`).
- **`agent_count=4`** у `grok-4.20-multi-agent` — работает как топ-уровневое поле REST (снял
  пометку «не сверено»); алиас резолвится в `-0309`.
- **`x_search`** — работает; в `output[]` = блок `custom_tool_call`, счётчик `x_search_calls`
  (задокументировал в докстринге модели).

Причёсано в коде: убрал `stream` из `XaiResponsesParams` (тонкий шлюз читает `response.json()`,
SSE не тянет — footgun); уточнил комментарии `agent_count`/x_search; поправил модуль-докстринг
`gateway.py` (нет топ-уровневого `citations`) и `constants.py` (пометка «сверено»). `--core` 266 passed.
Осталось несверённым только `collections_search` (нет коллекций) и `enable_image_*`.

## Строгий вывод (structured output) + паттерн «релевантные ссылки»

Сверено вживую: `text.format={type:"json_schema",name,strict:true,schema}` на `/v1/responses`
работает **вместе с web_search** (Grok-4). Ключевой баг пойман: `search_context_size` на вход НЕ
принимается (`400 Argument not supported`; лишь в эхо ответа) → **убран** из `XaiWebSearchTool`.

В шлюз добавлено: поле `text: dict|None` в `XaiResponsesParams` + хелпер `json_schema_text(name,
schema, strict=True)` → собирает конверт `{"format":{…}}` (обходит конфликт имени `schema` с
pydantic без alias). Экспортированы из пакета.

Пайплайн проверен end-to-end через типизированную модель (`verify_relevant_links.py`, запрос
«очереди на Python», схема `{links:[{url,title,relevance,reason}]}`): Grok сам ищет →
отбирает/ранжирует → возвращает строгий JSON; **URL заземлены 6/6 и 8/8** (не выдуманы), мусор
(youtube/reddit) отсеян. `instructions` = агентская инструкция, `input` = запрос пользователя.
Схема ссылки по решению юзера: url+title+relevance+reason. Логика «релевантных ссылок» пока живёт
в верстаке-рецепте (не в модуле — шлюз общий). `--core` 266 passed.
