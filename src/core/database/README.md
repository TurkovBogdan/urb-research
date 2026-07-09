# core/database

Async SQLAlchemy 2.0 + asyncpg + Alembic.

## Жизненный цикл

Engine и session-factory лежат на уровне модуля `runtime.py` — один процесс, один движок. `init_database(settings)` создаёт их, `close_database()` сбрасывает. Создаются внутри lifespan фабрики (`src/core/app_factory.py`).

```python
# Внутри create_app() lifespan:
engine = await init_database(settings)
await AlembicRunner(modules=modules).upgrade_head(engine)
# ... yield ...
await close_database()
```

Текущий engine — `get_engine()` (или `None`, если ещё не инициализирован).

## Доступ к сессии

Сессией владеет **CRUD**, а не вызывающий код. Каждая CRUD-функция сама открывает `session_scope()` и коммитит на выходе; HTTP-обработчики, сервисы и задачи вызывают CRUD напрямую без `session`-аргумента (см. `AGENTS/conventions/code-layout.md`, раздел CRUD).

`session_scope()` напрямую — только внутри CRUD и в редких местах, где нужен ad-hoc запрос вне CRUD-слоя:

```python
from src.core.database import session_scope

async with session_scope() as session:
    await session.execute(...)
    # commit на успехе, rollback на исключении
```

## Как добавить миграцию для модуля

Каждый модуль в `src/modules/<name>/` хранит свои модели и свою папку ревизий. Ядро ничего не знает о моделях модуля — они регистрируются в `Base.metadata` через импорт `models` в `__init__.py` модуля.

**1. Модель.** `src/modules/<name>/models.py`:

```python
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base

class Vacancy(Base):
    __tablename__ = "vacancies"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
```

**2. Регистрация в SPEC.** `src/modules/<name>/__init__.py`:

```python
from pathlib import Path
from src.core.module_spec import ModuleSpec
from src.modules.<name> import models  # noqa: F401 — регистрация в Base.metadata
from src.modules.<name>.api import router

_NAME = "<short-name>"
_HERE = Path(__file__).resolve().parent

def _register(app, settings):
    app.include_router(router, prefix=f"/api/{_NAME}", tags=[_NAME])

SPEC = ModuleSpec(
    name=_NAME,
    register=_register,
    migrations_dir=_HERE / "migrations" / "versions",
    settings_cls=...,
)
```

**3. Подключение к сборке.** `src/apps/app/server.py`:

```python
from src.modules import <name>
app = create_app(modules=[headhunter.SPEC, <name>.SPEC], settings=settings)
```

**4. Создание ревизии.** Сейчас вручную через alembic CLI с явным `script_location` и `version_locations`; обёртка-скрипт `scripts/db_revision.py` пока не написана (TODO).

**5. Применение.** Автоматически при старте приложения — `AlembicRunner(modules=modules).upgrade_head(engine)` собирает `version_locations` из `m.migrations_dir` всех модулей.

### Флаг `DB_AUTO_MIGRATE`

Авто-применение миграций при старте управляется env-флагом `DB_AUTO_MIGRATE` (конфиг `Config.db_auto_migrate`, по умолчанию `true`). При `false` lifespan пропускает `upgrade_head` и пишет warning — миграции нужно накатить вручную.

**Зачем:** dev-конфиги (`.run/run-server*`, `run-worker`) запускают `src/app.py --hot-reload`. Без флага каждый перезапуск по сохранению файла гонит `upgrade heads` и может накатить **недописанную** миграцию на dev-базу (реальный инцидент: reload применил `ci01_init` с `depends_on` на чужую head и заклинил Alembic). Поэтому dev-конфиги выставляют `DB_AUTO_MIGRATE=false`.

**Как тогда накатывать миграции в dev:** явной командой `uv run python src/app.py migrate upgrade` — она применяет миграции до head тем же `AlembicRunner` и сразу выходит (без подъёма сервера, `DB_AUTO_MIGRATE` игнорируется). Сначала можно свериться `src/app.py migrate check` (dry-run: список pending, БД не трогает, exit 1 при drift). Запускать осознанно, когда миграция дописана. Для prod/test флаг не задаётся → миграции накатываются на старте как обычно.

## Файлы

- `runtime.py` — `Base`, `init_database`, `close_database`, `get_engine`, `session_scope`.
- `migrations.py` — `AlembicRunner(modules)`: программный API Alembic, `path_separator=os`, `version_locations` склеиваются из ModuleSpec'ов.
- `alembic/env.py` — стандартный env, импортирует `Base.metadata`. Вызывается изнутри `AlembicRunner`.
- `alembic/script.py.mako` — шаблон ревизии.

## TODO

- `scripts/db_revision.py` — обёртка над `alembic revision --autogenerate`, которая знает про путь до `versions/` указанного модуля.
