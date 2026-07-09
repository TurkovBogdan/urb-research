---
title: daemon-web-scrapper as a content-fetch provider
date: 2026-07-08
status: completed
description: "Add the local browser daemon (daemon-web-scrapper, port 19020) as a fetch-only content engine (code web_scrapper) in web_search, wired through a new core_connectors connector."
tags: [web_search, core_connectors, providers]
---

## Task

Добавить в `web_search` ещё одного провайдера получения контента страниц (скрапинг, не поиск) —
локальный сервер `daemon-web-scrapper`.
Имя провайдера — `daemon-web-scrapper` (код-идентификатор `web_scrapper`).

## Context

`web_search` различает две роли: движок поиска (`SearchEngine`) и движок контента (`FetchEngine`).
Провайдеры — адаптеры над коннекторами `core_connectors` (HTTP/ключ/тумблер живут в коннекторе).
Демон умеет только скрейп страниц в markdown (поиска нет) → одна роль `FetchEngine`.
Демон: `POST /api/1.0/scrap-batch {urls, mode?, timeout?, …}` → `{results: [{outcome, url, content, …}]}`,
`content` = markdown. Конфиг демона (`.env`): `127.0.0.1:19020`, `SCRAPER_API_KEY` пуст (auth off),
`SCRAPE_BATCH_CONCURRENCY=10`. Решения пользователя: BASE_URL — по конфигу проекта (хардкод),
на страницу мониторинга `/connectors` НЕ выводить (баланса нет); имя = `daemon-web-scrapper`.

## What was done

- **core_connectors** — новый коннектор `services/web_scrapper/` (код `web_scrapper`, имя `daemon-web-scrapper`):
  - `params.py` — `WebScrapperScrapBatchParams` (`urls` + опц. `mode`/`timeout`/`load_timeout`/`scroll_timeout`).
  - `gateway.py` — `WebScrapperGateway(ServiceGateway)`: `BASE_URL=http://127.0.0.1:19020`,
    `API_KEY_FIELD=web_scrapper_api_key`, `ENABLED_FIELD=web_scrapper_gateway_enabled`, `TIMEOUT=180`;
    метод `scrap_batch(params)`; переопределён `_auth_headers()` — Bearer только при заданном ключе,
    пустой ключ = без авторизации (иначе база падает на `_key()`). `HAS_BALANCE=False`, в реестр не регистрируется.
  - `__init__.py` — экспорт. Настройки: `web_scrapper_gateway_enabled` (BoolField default True) +
    `web_scrapper_api_key` (StrField secret) в `settings.py::SCHEMA`.
- **web_search** — новый фетч-движок `providers/web_scrapper/`:
  - `client.py` — `WebScrapperEngine(FetchEngine)`, `code=web_scrapper`, `pages_per_request=10`;
    `fetch_pages(urls)` → `scrap_batch`, маппит `results[].url → content` (None при неуспехе/отсутствии).
  - `__init__.py` — регистрация в `fetch_engines` (только фетч).
  - `providers/__init__.py` — импорт пакета; `settings.py` — опция `web_scrapper` в `fetch_engine` + docstring.
- **Тесты:** `tests/modules/web_search/test_providers.py` — `test_web_scrapper_is_fetch_only`,
  `test_web_scrapper_maps_batch_content_by_url` (фейк-gateway, маппинг url→content, None-кейсы).
  Правлен `test_settings.py::test_schema_has_search_and_fetch_engines` (fetch-опции += web_scrapper).
- **Доки:** `docs/core_connectors/INDEX.md` (секция `services/web_scrapper`), `docs/web_search/INDEX.md`
  (фетч-движок web_scrapper: base/registry/__init__/настройки), `providers/base.py` docstring.

## Problems

Изначально провайдер назвали обобщённо `local_scraper`; по правке пользователя переименован в
`web_scrapper` / `daemon-web-scrapper` (пакеты, классы, коды, ключи настроек, опция, тесты, доки).

Демон на момент работы был **остановлен** (`run.sh status` → `resident: stopped`), хотя ожидался поднятым —
живой e2e-прогон не делался. Логика фетча покрыта юнит-тестом с фейк-gateway; форма ответа сверена
с исходником демона `src/schemas.py`. Живую проверку нужно прогнать после старта демона.

## Result

Новые файлы: `src/modules/core_connectors/services/web_scrapper/{__init__,gateway,params}.py`,
`src/modules/web_search/providers/web_scrapper/{__init__,client}.py`.
Изменены: `core_connectors/settings.py`, `web_search/providers/__init__.py`, `web_search/settings.py`,
`web_search/providers/base.py`, `tests/modules/web_search/{test_providers,test_settings}.py`,
`docs/core_connectors/INDEX.md`, `docs/web_search/INDEX.md`.
Проверка: `uv run pytest --module=web_search --module=core_connectors` → **74 passed**.
