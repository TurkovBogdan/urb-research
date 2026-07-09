---
title: dev-схема через миграции, а не create_all (+ миграции research_registry)
date: 2026-07-05
status: completed
description: "Dev (файловая sqlite) строила схему через create_all в lifespan, минуя Alembic — из-за этого правки моделей молча не доезжали в dev. Флипнул lifespan: create_all остаётся ТОЛЬКО для in-memory тестов (sqlite_in_memory), файловая dev-sqlite и PG идут через Alembic. Предпосылка: research_registry не имел миграций вообще (create_all-only) — завёл ему полноценные rrm_001..004. Пересобрал dev-базу через миграции (drop файла + migrate upgrade, настройки/ключи сохранены)."
tags: [core, migrations, research_registry, web_search, database]
---

## Проблема (претензия пользователя)

«Какого хуя в dev базе create_all? Нужны нормальные полноценные миграции. Разрешаю вручную
дропать базу чтобы обновить миграции (не плодя новых), но всё только через миграции.»

Причина: `app_factory.py` lifespan для `db_provider=="sqlite"` строил схему через `create_all`
(«SQLite-тир без истории миграций»). Побочка: `create_all` не ALTER'ит существующие таблицы →
правки моделей (напр. `fetch_engine`, индекс) молча не доезжали в dev. Плюс **research_registry
не имел миграций вообще** — только create_all.

## Что сделано

**Ядро — lifespan флип** (`app_factory.py`): `create_all` только при `config.sqlite_in_memory`
(тест-харнес, StaticPool, один прогон); файловая dev-sqlite и PG — через `AlembicRunner`
(`db_auto_migrate` → `upgrade_head`, иначе warn+ручной `migrate upgrade`). Тесты, грузящие
lifespan, работают на `:memory:` → ветка не изменилась.

**research_registry — полноценные миграции** (портируемые типы, идут на sqlite и PG):
- `rrm_001_research` → `rrm_002_research_query` → `rrm_003_research_document` → `rrm_004_research_report`
  (одна таблица на миграцию; column order зеркалит модели; FK внутримодульные CASCADE;
  cross-module ссылки `search_code`/`page_code` — мягкие, без FK/`depends_on`).
- `module.py`: `migrations_dir = _HERE/"migrations"/"versions"` (иначе runner не найдёт).

**Докстринги/доки** очищены от «create_all в dev»: `core/database/types.py`, `runtime.py`,
`web_search/module.py`, `research_registry/{module,constants,models/research}.py`,
`docs/platform/database.md` (sqlite schema = Alembic; create_all = только in-memory; migrate CLI
работает на обоих бэкендах). MEMORY: перевёрнут гоча «create_all never alters dev» → «dev строится
миграциями».

**Пересборка dev-базы** (пользователь разрешил дропать): бэкап 12 строк `core_modules_settings`
(вкл. API-ключи tavily/firecrawl/xai) → удаление `runtime/dev/app.sqlite3` (guard: sqlite + путь) →
`migrate upgrade` (свежая схема, `alembic_version` на 3 head'а) → восстановление настроек.

## Проверка

- Паритет модель↔миграция на sqlite: схема, собранная `migrate upgrade`, **структурно идентична**
  собранной `create_all` (0 diffs по колонкам/типам/индексам всех таблиц, вкл. research_*).
- `migrate check` (dev) → up to date (heads: `rrm_004`, `wsm_003`, `com_005`).
- Dev-база: все таблицы (core/web_search/research) + `alembic_version`; 12 настроек восстановлены;
  `web_search_page.fetch_engine` и `ix_web_search_query_engine_status` на месте.
- Полный `uv run pytest` → **321 passed**.

## Заметки на будущее

- dev `db_auto_migrate=True` (в `.env` не переопределён) → boot делает `upgrade heads` (no-op на head).
  Правка миграции **in-place** (revision id сохраняем, новых файлов не плодим) уже применённой ревизии
  на boot НЕ переcatается → нужно дропнуть dev-файл + `migrate upgrade` (тот самый разрешённый флоу).
- Каждый новый модуль с таблицами обязан иметь `migrations_dir` + миграции (не полагаться на create_all).
- `heavy` compare_metadata-тест (PG-only) теперь покрывает и research_registry (миграции vs модели).
