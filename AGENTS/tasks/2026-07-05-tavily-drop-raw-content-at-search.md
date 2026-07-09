---
title: Tavily — убрать «тело при поиске», стандартизировать провайдеров на два этапа
date: 2026-07-05
status: completed
description: "Tavily — единственный провайдер, чей /search мог вернуть тело страниц прямо в поиске (include_raw_content). Web_search-провайдер это уже не использовал (двухстадийный флоу введён ранее), но capability жила полем в тонком коннекторе шлюза. Убрал include_raw_content из TavilySearchParams — стандартизируем поведение: поиск = только ссылки у всех провайдеров, тело тянет отдельная стадия (/extract)."
tags: [core_gateway, web_search, tavily, standardization]
---

## Задача

«Tavily может вернуть тело документа сразу при поиске — убери, качество пробивает дно.
Нам важнее стандартизировать поведение провайдеров (поиск всегда двухстадийный).»

## Что найдено

Web_search-провайдер Tavily **уже** двухстадийный: `search()` отдаёт только ссылки
(`url/rank/score/meta{title,snippet}`), тело идёт из `fetch_pages()` → `/extract` →
`raw_content` (единственное использование `raw_content` в модуле). Инлайн-контент из поиска
убран прошлым рефактором. Capability «тело при поиске» жила лишь полем `include_raw_content`
в тонком коннекторе шлюза (`TavilySearchParams`) — в src не используется, тестов нет.

## Что сделано

- `core_gateway/services/tavily/params.py` — удалено поле `include_raw_content` из
  `TavilySearchParams` + класс-докстринг: поле намеренно НЕ проброшено, поиск = только
  ссылки, тело — стадия `/extract` (единый двухстадийный контракт, Tavily не «особый»).
  Приоритет стандартизации над полнотой тонкого коннектора — по решению пользователя.

Провайдер web_search (`providers/tavily/client.py`) не менялся — он уже стандартный
(контент не тянет в поиске). `meta.snippet` (короткий сниппет Tavily) оставлен — это
метаданные, симметричные firecrawl, не тело документа.

## Проверка

- `include_raw_content` больше нет в `TavilySearchParams.model_fields`; payload чистый.
- Полный `uv run pytest` → **321 passed**.

## Не трогал (вне scope)

- Dev-бенч `dev/bench/web_search/tavily/run_search_raw.py` демонстрирует ту самую (теперь
  не используемую) capability, но зовёт Tavily сырым dict мимо `TavilySearchParams` → не
  сломан; оставлен как историческая разведка API. Research-лог tavily — тоже (факт об API).
