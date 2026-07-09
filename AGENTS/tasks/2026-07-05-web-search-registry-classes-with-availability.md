---
title: web_search — реестры движков как классы + учёт доступности через core_gateway
date: 2026-07-05
status: completed
description: "Replaced the two dict+free-function registries with two registry CLASSES (SearchEngineRegistry/FetchEngineRegistry over a generic EngineRegistry[E]) exposing register/get/codes + availability (available_codes/is_available). Availability comes from core_gateway: a shared base Engine holds enabled_field (= gateway ENABLED_FIELD) and available()=service_enabled(...). Searcher fails fast (error_code=search_provider_disabled) when the chosen search engine's gateway is off."
tags: [web_search, providers, registry, core_gateway, availability]
---

## Task

«Нужно два отдельных класса реестра движков; они должны учитывать доступность самого
провайдера через core_gateway — провайдер может быть отключён.»

## Design

- Общий предок `base.Engine` (ABC): `code` + `enabled_field` (= `ENABLED_FIELD` шлюза) +
  `available()` = `core_gateway.settings.service_enabled(enabled_field)`. `SearchEngine`/
  `FetchEngine` теперь наследуют `Engine`.
- Провайдер задаёт `enabled_field = XxxGateway.ENABLED_FIELD` (без магических строк).
- `registry`: generic `EngineRegistry[E]` (register/get/codes/available_codes/is_available) +
  два класса `SearchEngineRegistry`/`FetchEngineRegistry` + синглтоны `search_engines`/`fetch_engines`.
  Убраны dict `_search`/`_fetch` и free-функции `register_*`/`get_*`/`*_codes`.
- Consumer: `searcher.search` — если `engine.available()` False, запрос сразу `error`
  (`error_code="search_provider_disabled"`, до сети; гейтвей тоже кинул бы RuntimeError, но код яснее).
  `available_codes()`/`is_available()` — публичный API реестра для будущих потребителей (UI/фильтр настроек).

## What was done

- `providers/base.py` — новый `Engine(ABC)` (code/enabled_field/available), `SearchEngine(Engine)`,
  `FetchEngine(Engine)`; импорт `core_gateway.settings.service_enabled`.
- `providers/registry.py` — переписан на классы (`EngineRegistry[E]` + два подкласса + синглтоны).
- clients `tavily`/`firecrawl`/`xai` — `enabled_field = <Gateway>.ENABLED_FIELD`.
- provider `__init__` (tavily/firecrawl/xai) — регистрация через `search_engines.register`/`fetch_engines.register`.
- `providers/__init__.py` — экспорт `Engine`, `search_engines`, `fetch_engines` (вместо free-функций).
- `services/searcher.py` — `search_engines.get`/`fetch_engines.get`; fail-fast на `engine.available()`.
- tests — `test_providers` (методы реестров + `test_registry_reflects_gateway_availability`),
  `test_search` (стаб с `enabled_field`, регистрация через синглтоны, `test_search_disabled_provider_errors_before_network`).
- docs/memory — `docs/web_search/INDEX.md` + MEMORY web_search строка: классы-реестры + доступность.

## Verification

- `grep` for `register_search|register_fetch|get_search|get_fetch|search_codes|fetch_codes` в src/tests → none (кроме `search_engines`/`fetch_engines`).
- `uv run pytest --module=web_search` → 41 passed; full `uv run pytest` → 313 passed.
