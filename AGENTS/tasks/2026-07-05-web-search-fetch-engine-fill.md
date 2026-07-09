---
title: web_search — заполнять web_search_page.fetch_engine при получении контента
date: 2026-07-05
status: completed
description: "Колонка web_search_page.fetch_engine существовала (nullable, под per-engine учёт фетча), но никто её не заполнял. Теперь движок контента снимается на попытке фетча — в pages_mark_processing(codes, *, fetch_engine): запись сохраняется и при done, и при error (движок известен до сети). Схема не менялась (колонка была) — пересборка dev не нужна из-за этой правки."
tags: [web_search, page, fetch]
---

## Задача

При получении контента страницы заполнять `web_search_page.fetch_engine` (колонка была, но
оставалась пустой).

## Решения

- Движок контента снимаем **на попытке фетча** — в `pages_mark_processing`, а не в
  `page_set_content`: так запись сохраняется и при `done`, и при `error` (страница, у которой
  фетч упал, тоже несёт движок, которым пытались).

## Правки

- `crud/page.py::pages_mark_processing(codes, *, fetch_engine: str)` — `fetch_engine` в
  `.values(...)`; docstring.
- `services/searcher.py::_fetch_pages` — `pages_mark_processing(..., fetch_engine=fetcher.code)`.

## Проверка

- `test_search.py`: `test_search_fetches_content_for_links` ассертит `page.fetch_engine == "stub"`;
  `test_search_page_fetch_empty_and_error` — что движок снят и при ошибке страницы.
- `--module=web_search` → **57 passed**.

## Схема

- Колонка `fetch_engine` уже была в `wsm_002_page` — миграция не менялась, отдельная пересборка
  dev из-за этой правки не нужна (общая пересборка нужна только для колонки `title` из соседней
  задачи [2026-07-05-web-search-page-title](2026-07-05-web-search-page-title.md)).
