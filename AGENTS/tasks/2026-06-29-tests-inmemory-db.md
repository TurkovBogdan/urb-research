---
title: Move tests off the Postgres pool to an in-memory DB
date: 2026-06-29
status: completed
description: "Rewrite the test suite to run against an in-memory (NoSQL-preferred) database and drop the Postgres TEST_DB_NAME pool + TEST_DB_USER/TEST_DB_PASSWORD credentials from the env."
tags: [testing, database, env]
---

## Task

Переписать использование тестов на in-memory базу (желательно NoSQL, работающую в памяти) и убрать из env Postgres-пул:

```
TEST_DB_NAME=core_semaphore_test_u1,...,core_semaphore_test_u8
TEST_DB_USER=core_semaphore_test
TEST_DB_PASSWORD=CHANGE_ME
```

## Context

Сейчас тесты бьют в реальный Postgres: пул физических тест-БД задаётся `TEST_DB_NAME` (одна БД на xdist-воркера), креды — `TEST_DB_USER`/`TEST_DB_PASSWORD`. `tests/conftest.py` выставляет `APP_ENV=test`, `--dbs` выбирает подмножество пула. Это требует поднятого Postgres с заранее созданными БД и тормозит локальный запуск.

Платформа уже умеет `DB_PROVIDER` = `postgres|sqlite` (portable types в `database/types.py`; sqlite → `create_all`, pg → Alembic). Кандидат на in-memory — sqlite `:memory:`; «NoSQL в памяти» в текущей SQLAlchemy/Alembic-архитектуре спорно — уточнить с пользователем перед реализацией.

Открытые вопросы (решить до кода):
- in-memory sqlite vs реальная NoSQL — что именно («NoSQL» против ORM-стека под вопросом);
- `heavy`-тесты гоняют реальный Alembic против Postgres — что с ними при in-memory;
- xdist-параллелизм и `--dbs` без пула физических БД;
- `live`-тесты не трогаем.

## What was done

Выбран in-memory **SQLite** (не NoSQL): проект на SQLAlchemy/Alembic, провайдер уже
поддерживал `postgres|sqlite`, dev-`.env` и так на sqlite. Настоящий NoSQL потребовал бы
переписать весь DB-слой — обсудили, пользователь дал «Вперёд» по sqlite-варианту.

- `src/core/config.py`: новый `Config.sqlite_in_memory` (`DB_PROVIDER=sqlite` + `DB_PATH=:memory:`).
  `database_url` → `sqlite+aiosqlite://`; `engine_kwargs` добавляет `poolclass=StaticPool` +
  `check_same_thread=False` (единый общий коннект держит in-memory базу живой для всех сессий
  engine'а). Импорт `StaticPool`.
- `tests/conftest.py`: полностью переписан. Вместо подмены `DB_*`→`TEST_DB_*` и пула физических
  баз — форс `DB_PROVIDER=sqlite`/`DB_PATH=:memory:` до импорта `src`. Убраны пул/`--dbs`/
  `_TEST_DB_SLOTS`/маршрутизация воркеров; `--dbs` оставлен no-op (старые команды не падают).
  Удалён `_wipe_test_schema` (DROP SCHEMA Postgres) → каждый db-тест строит свежий `:memory:`
  engine сам; новый autouse `_dispose_engine_between_tests` подчищает повисший engine. `-n` по
  умолчанию = `auto`. Опциональный `TEST_PG_DSN` переводит прогон на реальный Postgres для
  heavy-тестов.
- `pytest_collection_modifyitems`: heavy-тесты (Alembic, типы `postgresql.*`) скипаются на
  sqlite — запускаются только при `TEST_PG_DSN`.
- Реклассифицированы 7 lifespan-тестов `heavy → db` (на sqlite схема строится через `create_all`):
  `test_module_lifecycle.py` (2), `test_app_factory.py` (4), `test_main.py::test_health`.
  Остались `heavy` только 3 настоящих Alembic-теста в `test_migrations.py`.
- Тесты добавлены/правлены: `test_db_provider.py` — `test_sqlite_in_memory_url_and_static_pool`,
  `test_sqlite_in_memory_create_all_roundtrip`; `test_config.py` — `test_database_url_format`/
  `test_ssl_requires_cert` сделаны провайдер-явными (раньше зависели от ambient postgres-дефолта);
  `test_sqlite_default_path_in_runtime_root` пинит `db_path=""`.
- Env: убраны `TEST_DB_NAME`/`TEST_DB_USER`/`TEST_DB_PASSWORD` из `.env` и `.env.example.dev`
  (заменены комментарием про in-memory + `TEST_PG_DSN`). `pyproject.toml` — описания маркеров.
- Доки: `tests/README.md`, `AGENTS/docs/workflow/testing.md`, `AGENTS/agent-primary.md`
  (=CLAUDE.md), `AGENTS/docs/platform/architecture.md`, `AGENTS/docs/INDEX.md`,
  `AGENTS/education/test-coverage.md`, memory (`MEMORY.md`, `standalone_script_hits_dev_db.md`,
  `project_test_runtime_dev_leak.md`).

## Problems

3 pure-теста `Config` упали после форса `DB_PROVIDER=sqlite` в env — они опирались на
«дефолтный провайдер = postgres». Исправлены через явный `db_provider="postgres"` (тест
postgres-ветки не должен зависеть от ambient env) и пин `db_path=""` для sqlite-default-теста.

## Result

Тесты гоняются на in-memory SQLite без какого-либо Postgres. Прогоны:
`--core` 259 passed; `--all` 261 passed + 3 skipped (heavy Alembic, скип без `TEST_PG_DSN`);
параллель `-n auto` зелёная (своя `:memory:` у каждого воркера). Postgres-креды из env удалены;
heavy-миграции при необходимости — через `TEST_PG_DSN=postgresql://…`.

Изменённые файлы: `src/core/config.py`, `tests/conftest.py`, `pyproject.toml`,
`tests/core/test_config.py`, `tests/core/test_db_provider.py`,
`tests/core/test_module_lifecycle.py`, `tests/core/test_app_factory.py`,
`tests/apps/test_main.py`, `.env`, `.env.example.dev`, `tests/README.md`,
`AGENTS/docs/workflow/testing.md`, `AGENTS/agent-primary.md`,
`AGENTS/docs/platform/architecture.md`, `AGENTS/docs/INDEX.md`,
`AGENTS/education/test-coverage.md`, `AGENTS/memory/{MEMORY,standalone_script_hits_dev_db,project_test_runtime_dev_leak}.md`.
