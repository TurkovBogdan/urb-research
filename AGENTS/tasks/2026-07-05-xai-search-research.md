---
title: xAI (Grok) content-search research
date: 2026-07-05
status: completed
description: "Research xAI's content-search functionality as a candidate engine (bucket C) for the research/web_content layer. Doc-based, no live calls."
tags: [research, ingestion, xai]
---

## Task

«Нужно провести ресёч xai функционала по поиску контента» — исследовать возможности xAI (Grok)
по поиску контента и оформить артефакт в `AGENTS/research/`.

## Context

`AGENTS/obsidian/sources-engines.md` уже классифицирует xAI как движок **бакета C** (синтез агента +
цитаты, тела источников не отдаёт), но полноценного research-артефакта по xAI (как у Tavily) не было.
Нужен разбор актуальной поверхности поиска для выбора движков слоя исходных данных.

## What was done

- Собрал по `docs.x.ai` (WebFetch/WebSearch, живьём не гоняли — нет ключа):
  Agent Tools API на `POST /v1/responses`, инструменты `web_search`/`x_search`/`code_execution`/
  `collections_search`, их конфиг-параметры и лимиты; формат `citations[]`/`annotations[]`
  (только URL, без тел/сниппетов); multi-agent deep research (`grok-4.20-multi-agent`, agent_count 4/16);
  каталог моделей и цен; тарификация built-in-инструментов; снятие legacy Live Search (410 Gone c 12.01.2026).
- Создал `AGENTS/research/xai/INDEX.md` из TEMPLATE, добавил строку в `AGENTS/research/INDEX.md`.

## Result

- `AGENTS/research/xai/INDEX.md` — новый артефакт (Scope / Findings / Limits / References).
- `AGENTS/research/INDEX.md` — строка инвентаря по xai.
- Ключевой вывод для дизайна: xAI = бакет C, цитаты = **только URL** (нужен доскрейп через движок A);
  Live Search снят — только Agent Tools на `/v1/responses`; биллинг = токены + $5/1000 вызовов на инструмент.
- Открытый хвост: живьём не проверено (точная схема `output[]`, поля `usage`) — при появлении ключа
  сделать верстак по образцу `dev/bench/web_content/tavily`.
