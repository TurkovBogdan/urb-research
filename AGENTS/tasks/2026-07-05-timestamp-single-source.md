---
title: Единый источник времени — utc_now() вместо func.now() во всех таймстемп-колонках
date: 2026-07-05
status: completed
description: "Пользователь увидел в dev-sqlite смешанные форматы дат (часть строк с .000000, часть без) — следствие двух источников времени: часть колонок писалась app-side utc_now(), created_at/updated_at — DB-side server_default=func.now()/onupdate=func.now(). Свели к одному источнику utc_now() (Python-side default/onupdate), func.now() убран из моделей и миграций. Причина выбора utc_now: на PG func.now() в наивный TIMESTAMP пишется в таймзоне сессии БД (не гарантированно UTC), а utc_now() всегда истинный UTC + один формат."
tags: [dates, database, migrations, web_search, research_database, convention]
---

## Задача

В базе видно `2026-07-05 07:01:06.000000`. Вопрос: UTC в базе — норма? Да, норма (проект хранит
наивный UTC везде, фронт переводит в локаль). Но всплыл реальный дефект: **два источника времени**
— app-side `utc_now()` (даёт `.000000` на sqlite) и DB-side `server_default=func.now()`
(без дробной части). Требование: **один источник**.

## Решение

Единый источник — **`utc_now()`** (Python-side), как и объявлено в `date.py`/`docs/platform/dates.md`.
Почему не `func.now()`: (1) на Postgres `now()` в наивный `TIMESTAMP` пишется в таймзоне сессии
БД — не гарантированно UTC; `utc_now()` всегда истинный UTC; (2) второй источник = второй формат
(на sqlite `func.now()` без дробной, `utc_now()` — `.000000`).

- Модели: `server_default=func.now()` → `default=utc_now`; `onupdate=func.now()` → `onupdate=utc_now`.
- Миграции: убран `server_default=sa.func.now()` у `created_at`/`updated_at` (Python-side `default`
  не создаёт DDL-дефолт → модель и миграция в паритете).
- CRUD не трогал — он и так стамповал `utc_now()`; пути, что полагались на `server_default`
  (`query_result`, `research_*`), теперь берут `default=utc_now`.
- Бонус: Python-side `onupdate=utc_now` вычисляется клиентом → отпадает `s.refresh(row)`, который
  требовался для SQL-side `onupdate` (заметка в `backend.md` уточнена).

## Файлы

**web_search** (фактический охват) — модели `query.py`/`page.py`/`query_result.py`; миграции
`wsm_001`/`wsm_002`/`wsm_003`.

**research** — уже был чист: параллельно с этой задачей модуль `research_database` **переименован в
`research`** (rem_* миграции), и там уже стоял `default=utc_now`/`onupdate=utc_now`, `func.now()`
нет ни в моделях, ни в миграциях. Мои правки, сделанные в старом `research_database/`, осиротели
при переименовании (каталог удалён) — на активный `research` не влияют и не нужны.

**Доки:** `docs/platform/dates.md` — новая секция «created_at/updated_at column defaults — single
source is utc_now()»; `docs/conventions/backend.md` — заметка про `onupdate` уточнена.

## Проверка

- `grep func.now()` по `src/` — пусто (и в `research`, и в `web_search`).
- `--module=web_search --core` → **323 passed**.
- Dev-sqlite пересобран (drop + `migrate upgrade`): `web_search_page`/`query_result` и `research.*`
  имеют `created_at`/`updated_at` **без DDL-дефолта**; `integrity_check` ok; `migrate check` up-to-date;
  11 настроек восстановлены.

## Осталось

- `heavy` compare_metadata паритет (PG) — не гонял (нет `TEST_PG_DSN`); правки симметричны
  (server_default убран и из модели, и из миграции), дрейфа быть не должно.
