---
title: web_content — retry/fail для поиска (зеркало retry-механики страницы)
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Добавить поиску статусы retry/fail (сбой движка = сервер лёг) + поля повторов error_count/error_code/error_at + настройки search_max_attempts/search_retry_backoff. Полное зеркало механики страницы. Жёсткое пересоздание таблиц."
tags: [web_content, db, statuses, settings]
---

## Task

Добавить к поиску статус ошибки (если сервер/движок лёг) и поля повторов **по аналогии
с документом (страницей)** — т.е. статусы `retry` и `fail`.

## What was done

- **constants** — `SEARCH_RETRY`/`SEARCH_FAIL` в `SEARCH_STATUSES`; `SEARCH_MAX_ATTEMPTS`=3,
  `SEARCH_RETRY_BACKOFF_SECONDS`=300.
- **Модель** `models/search.py` — `error_count`/`error_code`/`error_at` после `params`, до `finished_at`.
- **Миграция** `wcm_001_search.py` — те же 3 колонки (на месте).
- **Настройки** `module_settings.py` — `IntField` `search_max_attempts` (1..20) + `search_retry_backoff`
  (0..86400); хелперы `search_max_attempts()`/`search_retry_backoff_seconds()`.
- **CRUD** `crud/search.py` — `search_claim_pending`→`search_claim_due` (забор `pending`+`retry` после
  бэкоффа, `_due_predicate`); `search_mark_pending`→`search_mark_error` (retry→fail по `search_max_attempts`);
  `search_finish` сбрасывает `error_code`/`error_at`. Читает настройки через хелперы.
- **Обработчик** `providers/base.py` — `run_search_queue` зовёт `search_claim_due` + `search_mark_error`
  (`error_code=type(exc).__name__`) вместо revert-в-pending.
- **DTO** `SearchRow` + фронт `web_content/api.ts` — поля `error_count`/`error_code`/`error_at`; статусы
  `retry`/`fail` (`api.ts SearchStatus`, `labels.ts` цвета accent/error + список, `locales/ru.json` подписи).
- **Dev-БД** — жёстко пересозданы 3 таблицы web_content (assert sqlite+dev-путь).
- **Тесты** `test_provider_handler` — сбой→retry (error_count/error_code), fail после лимита, claim_due
  respects backoff, reclaim (rename claim_due).

## Result

- Изменены: `constants.py`, `models/search.py`, `migrations/versions/wcm_001_search.py`,
  `module_settings.py`, `crud/search.py`, `providers/base.py`, `dto.py`,
  `web/src/features/web_content/{api.ts,labels.ts,locales/ru.json}`, `tests/.../test_provider_handler.py`;
  docs `web_content/INDEX.md`, memory.
- Проверки: `pytest --module=web_content` → 46 passed; `migrate check` → up to date; `vue-tsc` → 0;
  dev DDL: `error_count/error_code/error_at` до `finished_at`, CHECK с `retry`/`fail`.
