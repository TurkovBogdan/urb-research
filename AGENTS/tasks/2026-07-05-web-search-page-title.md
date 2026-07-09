---
title: web_search — заголовок документа как колонка web_search_page.title
date: 2026-07-05
status: completed
description: "Заголовок страницы — свойство самого документа (не запроса), поэтому первоклассная колонка web_search_page.title (String(512), nullable), а не поле в query_result.meta. Заполняется из выдачи поиска при создании страницы (дедуп не перетирает — первый нашедший движок задаёт). title повышен до верхнего ключа контракта провайдера (как summary), из meta убран; в meta остаётся только контекстное (у xAI — reason). QueryResultView отдаёт page_title из джойна."
tags: [web_search, providers, page, migration]
---

## Задача

Появилась возможность сохранять заголовок страницы. Развилка: `summary` контекстно-зависим
(разный под разные запросы → живёт на `query_result`), а заголовок — атрибут документа, один
для страницы независимо от запроса → его дом `web_search_page`, и из `meta` его надо убрать,
а не дублировать.

## Решения

- Колонка **`web_search_page.title`** (`String(512)`, nullable). Источник — выдача **поиска**
  (`meta.title`), не фетч: Tavily `extract` заголовок надёжно не отдаёт. Проставляется при
  создании страницы; дедуп `on_conflict_do_nothing` не перетирает (первый движок задаёт).
- `title` — **верхний ключ** контракта провайдера `{url, rank?, score?, summary?, title?, meta?}`
  (как `summary`); из `meta` убран. `meta` теперь = только контекстное (у xAI — `reason`).
- Фронт — минимум: `QueryView` берёт заголовок из `page_title`, `PageView` показывает `title`
  в шапке. Списки не трогали.

## Бэк

- `models/page.py` — колонка `title` (после `url`) + поле в `PageRow`; docstring.
- `migrations/wsm_002_page.py` — `sa.Column("title", sa.String(512), nullable=True)` **in-place**
  (revision id сохранён).
- `crud/page.py::page_upsert(url, *, title=None)` — `title` в insert values.
- Провайдеры: `title` верхним ключом, из `meta` убран — tavily `item.title`, firecrawl
  `item.title`, xai `link.title` (`meta={reason}`). `base.py` контракт в докстроках.
- `services/searcher.py::_store_results` — `page_upsert(url, title=result.get("title"))`.
- `models/query_result.py::QueryResultView` + `api.py::get_query` — поле `page_title`
  (из `page.title`); docstring meta переписан.

## Фронт

- `api.ts` — `QueryResultView.page_title`, `WebSearchPageRow.title`.
- `QueryView.vue::resultTitle` → `r.page_title` (был `r.meta?.title`).
- `PageView.vue` — заголовок `.page-title` в шапке карточки.

## Верстак

- `dev/bench/web_search/xai` (`run_search.py` + README) — печать/описание под `title` верхним
  ключом (был `meta.title`).

## Проверка

- `--module=web_search` → **57 passed** (тесты crud/api/store_results/providers перенесены с
  `meta.title` на `page.title`/`page_title`; добавлен `test_page_upsert_sets_title_once_and_keeps_first`).
- `vue-tsc --noEmit` EXIT=0.

## Пересборка dev-sqlite — сделано

Backend + Database-инструмент PyCharm остановлены; бэкап `core_modules_settings` (11) → assert
(sqlite + путь) → drop файла (+ мусорный `app.sqlite3 (deleted)`) → `migrate upgrade` → restore.
`web_search_page.title` на месте, `integrity_check` ok, `migrate check` up-to-date.

## Не сделано / остаётся

- Живой прогон xai-бенча — не гонял (нужны кредиты).
