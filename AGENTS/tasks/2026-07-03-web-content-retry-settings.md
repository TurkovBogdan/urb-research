---
title: web_content — настройки макс. повторов и паузы перед повтором
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Вынести FETCH_MAX_ATTEMPTS и FETCH_RETRY_BACKOFF_SECONDS в runtime-настройки модуля (fetch_max_attempts, fetch_retry_backoff); CRUD page читает их через хелперы. На фронте появляются авто из схемы."
tags: [web_content, settings]
---

## Task

Добавить в настройки модуля: максимальное кол-во повторов получения и паузу
(секунды) перед повтором.

## What was done

- `module_settings.py` — два `IntField`: `fetch_max_attempts` (default 3, 1..20) и
  `fetch_retry_backoff` (default 300, 0..86400); дефолты берутся из `constants.py`
  (`FETCH_MAX_ATTEMPTS`/`FETCH_RETRY_BACKOFF_SECONDS`). Хелперы `fetch_max_attempts()`,
  `fetch_retry_backoff_seconds()` (fallback на константы, если store не загружен).
- `crud/page.py` — читает хелперы вместо констант: `page_mark_error` → `fetch_max_attempts()`
  в `case(... → fail)`; `_due_predicate` → `fetch_retry_backoff_seconds()` в cutoff.
  Импорты констант заменены на импорт хелперов.
- Фронт — не трогал: настройки рендерятся на `/core/settings` из схемы по `kind`, лейбл с бэка.

## Result

- Изменены: `module_settings.py`, `crud/page.py`; docs `web_content/INDEX.md`, memory.
- Константы `FETCH_MAX_ATTEMPTS`/`FETCH_RETRY_BACKOFF_SECONDS` остались как дефолты/fallback.
- Проверки: `pytest --module=web_content` → 44 passed; импорт-смоук (без циклов; helpers → 3/300;
  схема содержит `fetch_max_attempts`+`fetch_retry_backoff`). Схема/логика — правок БД нет.
