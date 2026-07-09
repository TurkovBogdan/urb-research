---
title: xai web_search provider — agentic strict-output search
date: 2026-07-05
status: completed
description: "Port the bench agentic search pipeline (instructions + web_search tool + strict json_schema links[]) into the production web_search xai provider, filtering model-emitted URLs against real search sources to drop hallucinations."
tags: [web_search, providers, xai]
---

## Task

Перенести логику агентского поиска из бенча `dev/bench/core_gateway/xai/verify_relevant_links.py`
внутрь боевого провайдера `src/modules/web_search/providers/xai/client.py`. Бенч просит Grok
вернуть строгий JSON `links[]` (url/title/reason/relevance) через `json_schema_text` + `instructions`
и server-side `web_search` tool.

## Context

Текущий `client.py` не использует строгий вывод: зовёт `responses()` без `text`/`instructions`
и достаёт URL постобработкой (`url_citation` из annotations, fallback — `web_search_call.action.sources`).
Ранжирования/релевантности от модели нет. Агентский подход даёт ранжирование + обоснование, но URL
печатает сама модель → риск галлюцинации. Бенч это мерил (`grounded N/M`).

Решение пользователя по grounding: **фильтровать по sources** — оставлять только те `links[].url`,
что реально есть в `web_search_call.action.sources` (нормализация url); релевантность/ранжирование
модели сохраняются, галлюцинации отбрасываются.

## What was done

- `providers/xai/client.py`: `search()` теперь строит `XaiResponsesParams` с `instructions=AGENT_INSTRUCTION`,
  `tools=[XaiWebSearchTool(filters=…)]` и `text=json_schema_text("relevant_links", LINKS_SCHEMA)`
  (строгий JSON `links[]` url/title/reason/relevance). Добавлены константы `AGENT_INSTRUCTION`/`LINKS_SCHEMA`.
- Парсинг: `_parsed_links` (строгий JSON финального `message`, пусто при сбое разбора),
  `_searched_urls` (нормализованные `web_search_call.action.sources`), `_grounded_links`
  (оставляет только встреченные поиском — grounding-фильтр от галлюцинаций), `_norm_url`.
  Удалён прежний `_cited_urls` (annotations/url_citation). Маппинг: `relevance→score`, `rank` по порядку,
  `meta={title, reason}`, обрезка до `max_results`.
- Тесты (`tests/modules/web_search/test_providers.py`): `test_xai_search_drops_ungrounded_links`
  (галлюцинированный URL отбрасывается, grounded сохраняют порядок/маппинг), `test_xai_search_survives_unparseable_output`.
- Docs `web_search/INDEX.md` + memory `MEMORY.md` — описание xai-провайдера переписано под strict output + grounding.

`--module=web_search` 41→43 passed.

## Result

- `src/modules/web_search/providers/xai/client.py` — переписан на агентский strict-output поиск + grounding.
- `tests/modules/web_search/test_providers.py` — +2 pure-теста.
- `AGENTS/docs/web_search/INDEX.md`, `AGENTS/memory/MEMORY.md` — обновлены.
- Бенч `dev/bench/core_gateway/xai/verify_relevant_links.py` оставлен как эталон логики (не менялся).
