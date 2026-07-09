---
title: web_search — searcher как статический класс Searcher + provider→engine по цепочке
date: 2026-07-05
status: completed
description: "searcher.py переведён из модульных функций в статический класс-фасад Searcher: публичные search_engines()/fetch_engines() (коды доступных движков), search(query, *, search_engine=None, fetch_engine=None, …) с опциональными движками, приватные геттеры дефолта _default_search_engine()/_default_fetch_engine(). Термин provider→engine переименован по всей цепочке: настройки (ключи search_provider→search_engine, content_provider→fetch_engine + хелперы), searcher, код ошибки search_provider_disabled→search_engine_disabled."
tags: [web_search, searcher, settings, rename, refactor]
---

## Задача (чеклист, п.1)

Статический класс с методами: получение активных (доступных) движков по ролям + запуск
поиска с опциональным движком (не задан = дефолт). Геттер дефолта — приватный. Поиск
принимает движок для поиска И для получения. «Переименуй по цепочке — это не провайдер, а
engine.»

## Что сделано

**`services/searcher.py` → класс `Searcher`** (статические методы, без состояния):
- публичные `search_engines()` / `fetch_engines()` → `<registry>.available_codes()` (коды
  включённых движков по ролям);
- `search(query, *, search_engine=None, fetch_engine=None, max_results=None, include/exclude_domains, time_range)`
  — движки опциональны, None → приватные `_default_search_engine()`/`_default_fetch_engine()`
  (= настройки);
- реестры импортированы как `search_engine_registry`/`fetch_engine_registry` (не путать с
  одноимёнными публичными методами);
- шаги `_acquire_search_slot`/`_store_results`/`_fetch_pages` остались модульными приватными
  (их зовёт `Searcher.search`; `_store_results` по-прежнему импортит `test_store_results`).

**provider → engine по цепочке:**
- `settings.py`: ключи `search_provider`→`search_engine`, `content_provider`→`fetch_engine`;
  хелперы `search_engine()`/`fetch_engine()`; константы `SEARCH_ENGINE_DEFAULT`/`FETCH_ENGINE_DEFAULT`.
  Лейблы («Поисковый движок» / «Сервис получения контента») не менялись.
- код ошибки `search_provider_disabled` → `search_engine_disabled`.
- Query-колонки `search_engine`/`fetch_engine` и реестры `search_engines`/`fetch_engines`
  уже были engine — теперь вся цепочка согласована.

**Тесты:** `test_settings` (ключи), `test_searcher` (`Searcher._default_*`), `test_search`
(фикстура патчит `Searcher._default_*`, вызовы `Searcher.search`, ошибка `search_engine_disabled`).

**dev-база:** ключи `search_engine`/`fetch_engine` уже были засеяны bootstrap'ом; удалил
устаревшие дубли `search_provider`/`content_provider` + древний `provider` (guarded).

Docs (`docs/web_search/INDEX.md` — settings/searcher/таблица) + MEMORY обновлены.
Фронт не трогал (настройки рендерятся из схемы, ключи в web/src не захардкожены).

## Проверка

- Остаточных `*_provider`-имён в src нет.
- `--module=web_search` 49 / полный `uv run pytest` → **321 passed**.
