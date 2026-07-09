---
title: web_search — колонка summary в выдаче + верстак xAI
date: 2026-07-05
status: completed
description: "Краткое содержание страницы в контексте запроса — первоклассная колонка web_search_query_result.summary (Text), общая для всех движков (Tavily content, Firecrawl description, xAI — новое поле строгого вывода). Полноценный верстак dev/bench/web_search/xai (гоняет провайдер-адаптер XaiSearchEngine)."
tags: [web_search, providers, xai, bench, migration]
---

## Задача

1. Изучить провайдеры (`dev/bench/web_search` tavily/firecrawl + `dev/bench/core_gateway/xai`)
   и создать полноценный верстак для xai.
2. Добавить «краткое содержание» в `web_search_query_result` (все движки его отдают); для xAI —
   модифицировать строгий вывод.

## Решения

- Имя поля — **`summary`** (нейтрально для всех движков; ≠ `snippet`, привязанного к поиску).
  Тип `Text`, nullable, колонка **после `score`** (промо-контент выше свободного `meta`).
- `meta` остаётся под остаточные поля провайдера (title/reason/favicon/…); `snippet` из `meta`
  убран у tavily/firecrawl — его роль теперь у `summary`.

## Бэк

- `models/query_result.py` — колонка `summary` + поле в `QueryResultView`; docstring.
- `migrations/wsm_003_result.py` — колонка `summary Text` (правка **in-place**, revision id
  сохранён; dev-sqlite пересобран: бэкап настроек → drop файла → `migrate upgrade` → restore).
- `crud/query_result.py::result_add(..., summary=None)`; `services/searcher.py::_store_results`
  прокидывает `summary=result.get("summary")`.
- Провайдеры кладут `summary` в результат поиска: tavily `content`, firecrawl `description`,
  xai — новое поле строгого вывода (`LINKS_SCHEMA` + `AGENT_INSTRUCTION` просят summary),
  маппинг `summary→summary`, `meta={title, reason}`.
- `api.py::get_query` — `summary` в `QueryResultView`.

## Фронт

- `api.ts` — `QueryResultView.summary: string | null`.
- `QueryView.vue` — `resultSnippet` читает `r.summary` (был `r.meta.snippet`).

## Верстак (`dev/bench/web_search/xai/`)

- `constants.py`/`run_search.py`/`README.md` — гоняет провайдер-адаптер `XaiSearchEngine`
  (у xAI нет raw search — «поиск» = агентский `responses()` + строгий JSON), печатает
  заземлённые ссылки с новым `summary`. Bootstrap переиспользован из `core_gateway/xai`.

## Проверка

- `--module=web_search` 56 / полный `uv run pytest` → **328 passed** (тесты crud/api/store_results
  расширены на `summary`); `migrate check` — up to date; `vue-tsc --noEmit` EXIT=0.
- Dev-sqlite: колонка `summary` на месте (после `score`), 11 настроек восстановлены.

## Не сделано (вне scope)

- Живой прогон верстака xai не гонял (нужен реальный вызов API/кредиты) — код готов к запуску.
- `web/dist` не пересобирал (dev через Vite).
