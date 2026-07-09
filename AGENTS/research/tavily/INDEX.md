---
title: Tavily API
date: 2026-06-29
description: "Методы Tavily (search/extract/map/crawl), формат ответов и лимиты. Проверено живыми вызовами через верстак dev/bench/web_content/tavily."
tags: [external-service, ingestion]
---

## Scope

Покрыто живыми вызовами: `POST /search`, `/search`+`include_raw_content`, `/extract`, `/map`.
Не гоняли: `/crawl` (beta). Аутентификация — `Authorization: Bearer <key>`. База `https://api.tavily.com`.
Runnable-артефакты и прогоны — `dev/bench/web_content/tavily/` (`tmp/*.json`).

## Findings

- **`/search`** — топ-уровень ответа: `query`, `results[]`, `answer`, `follow_up_questions`,
  `images`, `response_time`, `request_id`. `answer`/`follow_up_questions`/`images` = `null`, пока не запрошены.
- **Поле результата search:** `title`, `url`, `content` (сниппет ~1 КБ), `score` (0–1), `raw_content`
  (`null` без `include_raw_content`). `published_date` — только при `topic=news`.
- **`include_raw_content="markdown"`** → `raw_content` = полная страница в markdown (~18–20 КБ на результат).
  С `include_answer=true` ответ несёт ещё LLM-`answer`. Один вызов = поиск + тело + ответ (бакет A+B+чуть C).
- **`/extract`** — `urls` + `format`(markdown/text) + `extract_depth`. Ответ: `results[]`
  (`url`, `raw_content`, `title`, `images`), `failed_results[]`. У результата **нет** `content`/`score`.
- **`/map`** (beta) — `url`/`max_depth`/`limit` → `base_url` + `results[]` (плоский список URL, без контента).

## Limits / quirks

- `content` (сниппет) ≠ `raw_content` (полная страница): формы результата у `search` и `extract` разные.
- `map` возвращает и off-domain ссылки (x.com/discord/github) — фильтровать у себя.
- `usage`/кредиты приходят только при `include_usage=true`.
- `search_depth`: `basic`=1 кредит, `advanced`=2; `extract` 1 кр/5URL (basic) / 2 (advanced); `map` 1 кр/10 стр.
  `raw_content` доп. кредитов не добавляет. (Цены — из доков, живьём не мерили.)

## References

- Docs: https://docs.tavily.com/documentation/api-reference (search/extract/crawl/map)
- Верстак: `dev/bench/web_content/tavily/README.md` + `tmp/{search,search_raw,extract,map}.json`
- Каталог движков и классификация A/B/C: `AGENTS/obsidian/sources-engines.md`
