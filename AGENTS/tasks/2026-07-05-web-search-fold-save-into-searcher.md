---
title: web_search — свернуть services/save.py в searcher (это не сервис)
date: 2026-07-05
status: completed
description: "services/save.py держал одну функцию store_results, вызываемую только из searcher.search — фейковый «сервис». Свёрнута приватным _store_results в searcher.py рядом с _fetch_pages; save.py удалён. Аргумент: возврат list[WebSearchPage] (страницы под до-фетч) — оркестрационный сигнал для _fetch_pages, а не данные сущности → дом = оркестратор, не отдельный сервис и не crud."
tags: [web_search, refactor, services]
---

## Задача

«`services/save.py` — куда вынести? Это не сервис.» → свернуть в searcher.

## Что сделано

- `services/searcher.py` — добавлен приватный `_store_results(query_code, results) -> list[WebSearchPage]`
  (тело из бывшего `store_results`), рядом с `_fetch_pages`; вызов `search()` → `_store_results`.
  Импорты подтянуты (`Mapping`/`Sequence`/`Any`, `FETCH_STATUS_PENDING`, `query_result` crud).
- `services/save.py` — **удалён**.
- Тест `tests/modules/web_search/test_save.py` → `mv` в `test_store_results.py`; импорт
  `services.save.store_results` → `services.searcher._store_results`, докстринг обновлён.
- Docs (`docs/web_search/INDEX.md`) + MEMORY: убран bullet `services/save.py`, поток → `_store_results`.

## Почему не crud

`_store_results` возвращает подмножество страниц (`pending`) под следующий шаг (`_fetch_pages`) —
это оркестрационный сигнал, а не данные сущности. Чистые записи (`page_upsert`, `result_add`)
уже в crud; композиция + возврat pending = оркестрация → дом оркестратора (searcher), не crud
(иначе crud звал бы crud и возвращал page-сущности из results-crud).

## Проверка

- Висячих ссылок `services.save`/`store_results` нет.
- `--module=web_search` 49 / full `uv run pytest` → **321 passed**.
