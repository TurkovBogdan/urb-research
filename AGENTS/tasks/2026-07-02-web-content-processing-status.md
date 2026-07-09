---
title: web_content — статус processing для search и page
date: 2026-07-02
status: completed  # in-work | completed | deferred
description: "Добавить статус `processing` («обрабатывается задачей прямо сейчас») в web_content_search и web_content_page: константы, CheckConstraint, миграции."
tags: [web_content, db, statuses]
---

## Task

Добавить статус, обозначающий «эта запись сейчас обрабатывается в задаче», и для
поиска (`web_content_search`), и для страниц (`web_content_page`). Имя — `processing`.
Обновить миграции.

## Context

Раньше search имел `pending`/`done`/`empty`, page — `pending`/`fetched`/`retry`/`fail`.
Промежуточного состояния «в работе» не было — забор полагался на task-лок ядра.

## What was done

- `constants.py`: `SEARCH_PROCESSING`/`PAGE_PROCESSING` = `"processing"`, добавлены в `SEARCH_STATUSES`/`PAGE_STATUSES` (между pending и done/fetched) и в `__all__`.
- Модели: CheckConstraint строится из `*_STATUSES` через `sql_in` → правок не потребовали, статус подхватился автоматически.
- Миграции `wcm_001_search`, `wcm_002_page`: обновлён литерал `status IN (...)` в CheckConstraint (правка на месте — чейн web_content свежий, dev = sqlite/create_all).
- Фронт: `api.ts` (union-типы `SearchStatus`/`PageStatus`), `labels.ts` (цвет `accent` + списки), `locales/ru.json` (подпись «В обработке» для search и page).

Note: тесты не добавлялись — статус чисто перечислимый, покрыт существующими 38 тестами модуля (проверяют констрейнт/фильтры); `processing` пока никем не выставляется.

## Problems

Миграции отредактированы на месте, а не отдельным ALTER-ом. Это корректно для свежих
БД (heavy-тесты на PG строят с нуля; dev — sqlite через `create_all`). Но если какой-то
**Postgres уже применил `wcm_001/002`**, правка не перезапустится → старый CHECK останется,
и вставка `processing` его нарушит. Тогда нужна отдельная миграция `DROP/ADD CONSTRAINT`.

## Result

- Изменены: `src/modules/web_content/constants.py`, `migrations/versions/wcm_001_search.py`,
  `migrations/versions/wcm_002_page.py`; `web/src/features/web_content/{api.ts,labels.ts,locales/ru.json}`.
- `uv run pytest --module=web_content` → 38 passed; `migrate check` → up to date; `vue-tsc --noEmit` → 0.
- Не сделано (вне запроса): выставление/снятие `processing` в `searcher`/`fetcher`,
  исключение из очереди `page_list_due_for_fetch`, восстановление «зависших» — зависит
  от сценария (защита от повторного забора vs только UI-наблюдаемость).
