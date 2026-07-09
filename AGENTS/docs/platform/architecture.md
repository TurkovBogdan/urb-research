# Architecture — платформа из модулей

Кодовая база — конструктор. На её основе могут собираться разные приложения, у каждой — свой набор модулей. Сейчас собрана одна — `apps/app` (headless web-сервер). Qt-оболочка и по-модульные MCP-приложения удалены в рефакторе на web-сервер.

## Слои

```
src/
  core/                   # ядро: знает про Settings, БД, фабрику, типы
    config.py             # Settings (pydantic-settings) + get_settings (lru_cache)
    app_path.py           # AppPath.from_root, ensure_dirs
    app_factory.py        # create_app(modules, settings) -> FastAPI
    module.py             # Module (ABC, контракт модуля)
    loggers/              # каналы логирования — см. src/core/loggers/README.md
    database/             # init_database, close_database, get_session, AlembicRunner
  modules/                # самодостаточные модули (в bare-core пуст: build_modules() → [])
    my_module/            # name="my_module" — типовая раскладка модуля
      __init__.py         # экспортирует MyModule
      module.py           # Module subclass: configure + on_settings_change + on_startup + shutdown
      api.py              # APIRouter
      module_settings.py  # settings_schema
      schemas.py          # Pydantic DTO
      models/             # ORM, один файл на тип
      crud/               # CRUD, один файл на таблицу
      tasks/              # scheduler tasks
      migrations/versions/
  apps/                   # точки сборки
    app/                  # headless FastAPI-приложение (web API, без раздачи SPA)
      server.py           # Config → bootstrap логгера → create_app → CORS → /api/health
```

Точка входа — `src/app.py`. Роль процесса — композиция поверхностей SERVER (`SERVER_ENABLED`, HTTP через uvicorn) + WORKER (`WORKER_ENABLED`, планировщик + задачи); флаги `--backend`/`--worker` перекрывают env (флаг > env > дефолт). Чистый worker (без SERVER) — без uvicorn/порта, lifespan напрямую. `SERVER_HOT_RELOAD=true` → uvicorn `--reload` (dev). См. [`dev/docs/ENV.md`](../../../dev/docs/ENV.md).

## Контракт модуля — `Module`

```python
class Module(ABC):
    name: ClassVar[str]                              # префикс /api/<name>/, OpenAPI-тег
    migrations_dir: ClassVar[Path | None] = None    # alembic подхватит через AlembicRunner(modules=...)
    config_cls: ClassVar[type[BaseSettings] | None] = None  # env_prefix=<NAME>_; инстанс в app.state.module_configs[name]
    settings_schema: ClassVar[ModuleSchema | None] = None   # user-tunable runtime settings

    def configure(self, app: FastAPI, config: Config) -> None: ...   # sync, build phase
    def on_settings_change(self, store: Any) -> None: ...            # sync, первичный install + каждый PUT
    async def on_startup(self, app: FastAPI) -> None: ...            # async, DB уже готова
    async def shutdown(self, app: FastAPI) -> None: ...              # async, teardown ресурсов
```

## Жизненный цикл (lifespan)

```
create_app(modules, config):
  1. app.state.config = config
  2. app.state.module_configs[name] = Module.config_cls()  # для каждого модуля с config_cls
  3. get_registry().clear() + register_core_tasks()
  4. register_settings_schemas(modules)
  5. for m in modules: m.configure(app, config)
  6. app.include_router(core_router, prefix="/api/core")
  7. return app

  lifespan startup:
     a. init_database(config)               → module-global engine (не в app.state)
     b. AlembicRunner(modules).upgrade_head(engine)
     c. load_initial_stores(modules)        → on_settings_change для каждого модуля
     d. for m in modules: await m.on_startup(app)
     e. scheduler.start(config)

  lifespan shutdown:
     f. scheduler.stop()
     g. for m in reversed(modules): await m.shutdown(app)
     h. close_database()
```

## Принципы

1. **Модули статичны.** Список модулей фиксирован на старте процесса. Установка нового = перезагрузка. Никакого hot-reload, plugin-discovery, entry_points.
2. **`configure()` — sync, одноразовый.** Async-ресурсы — через FastAPI `Depends` (async-generator) или `on_startup`.
3. **Engine/session — модуль-глобальные.** `init_database(config)` создаёт один engine на процесс, `session_scope()` доступен напрямую. Не через `app.state`.
4. **Каналы логирования по конвенции.** Один канал → один файл `logs/<channel>.log`. Подробнее — [`src/core/loggers/README.md`](../../../src/core/loggers/README.md).
5. **Конфигурация в два слоя:** `Config` (ядро) + `<Module>Config(BaseSettings, env_prefix=<NAME>_)` для каждого модуля.
6. **Префикс роутера и OpenAPI-тег = `Module.name`.** Это инвариант: `app.include_router(router, prefix=f"/api/{_NAME}", tags=[_NAME])`.
7. **Ядро не знает о модулях.** Только `Config`, БД, фабрика, типы.

## API-конвенции

### Datetime → фронт

Все `datetime`-поля в **response**-схемах (Pydantic `BaseModel`, которые возвращаются клиенту) должны использовать тип `DatetimeUTCStr` из `src.core.utils.date`:

```python
from src.core.utils.date import DatetimeUTCStr

class SomeOut(BaseModel):
    created_at: DatetimeUTCStr
    updated_at: DatetimeUTCStr
    finished_at: DatetimeUTCStr | None
```

`DatetimeUTCStr` — это `Annotated[datetime, PlainSerializer(...)]`: принимает наивный (или aware) `datetime`, отдаёт строку `"YYYY-MM-DD HH:MM:SS"` наивного UTC **без** timezone-суффикса (например `2026-05-06 15:01:18`). Фронт читает все такие строки как UTC через `DateTime.fromSQL(s, { zone: 'utc' })` и рендерит в выбранной пользователем зоне.

**Нельзя** использовать голый `datetime`, `str` + `.isoformat()`, или любую другую форму — иначе формат строки разойдётся с тем, что ожидает парсер на фронте.

Правило касается только response-схем. В request-схемах (`Create`, `Update`) и внутренних DTO тип остаётся `datetime`. Полная конвенция дат (хранение `TIMESTAMP(precision=0)`, `synced_at`/`processed_at`/`ingested_at`, форматтеры фронта) — в [`dates.md`](dates.md).

## Scheduler

Module-global: `TaskRegistry` via `get_registry()`, a `Ticker` held in a module-global inside `src/core/scheduler/__init__.py`.

- API (no `app` argument): `scheduler.register(module=..., code=..., schedule=..., handler=..., ttl=...)`, `scheduler.start(config)` / `scheduler.stop()`, plus `scheduler.configure_worker(modules, max_concurrent, tick)` — worker-override that forces ticker start regardless of `worker_enabled`.
- `schedule` — standard 5-field cron (minimum 1 minute). `ttl` (int seconds) is **both** the `wait_for` timeout and the task-lock TTL.
- `Config.worker_enabled` (default False) gates the embedded ticker: dev=true (one process = web + tasks); prod-web=false → tasks run in a dedicated worker (same binary `--worker`, no uvicorn/port, lifespan run directly). `Config.worker_modules` (CSV → `worker_modules_set` frozenset|None) scopes the ticker by `entry.module`; `Config.worker_tick_seconds` (default 5) tick granularity; `Config.worker_max_concurrent_runs` (default 10) run cap.
- **Handler convention:** `tasks.py` next to the code, with a no-arg `register()` that calls `scheduler.register(...)`. `src/core/tasks.py` is registered from `app_factory.create_app`; `src/modules/<name>/tasks.py` from the module's registration.

## Runtime settings vs env config

- Runtime user-tunable settings: declare `settings_schema: ModuleSchema` on the `Module`; read via `get_module_store("<name>")` (immutable frozen dataclass, hot-reloadable); UI/API at `/api/core/settings/*`. `on_settings_change` fires only for modules that declare a settings_schema (unlike `on_startup`, which is universal).
- **Secrets stay in env** (`Config` / `<Module>Config`), never in runtime settings.

## Что сознательно НЕ делаем

- plugin-discovery / hot-reload / `entry_points`
- реестры моделей и миграций как глобалы
- user-editable runtime-конфиг (TOML на модуль)
- `app_boot.py` / `bootstrap.py` (роль уехала в фабрику + `apps/<name>/server.py`)
- per-module sub-логгеры с префиксами

## Отложенные траектории

- **Зависимости между модулями.** Сейчас порядок = порядок в списке `apps/<name>/server.py`. Когда понадобится — `depends: list[str]` в `Module` + топ-сорт.
- **Cross-module вызовы.** Допустимы прямые импорты `from src.modules.X.service import ...`. Event-bus — когда понадобится.
- **Скаффолд нового модуля** (`python -m src.tools.new_module <name>`) — создание шаблонного модуля.
- **MCP-сервер, CLI-утилиты** — новые `src/apps/<name>/server.py` со своим набором модулей.

## Тесты

```
tests/
  conftest.py                     # сброс CoreLoggerStore + кэша Settings между тестами
  core/                           # юнит-тесты ядра
  modules/<name>/                 # юнит-тесты модулей
  apps/<app>/                     # интеграционные тесты сборки
```

Запуск: `uv run --group test pytest`. БД не нужна — тесты на in-memory SQLite.

Каждый тест несёт одну метку: `pure` / `db` / `heavy` / `live`. По умолчанию
(`addopts = "-m 'not heavy and not live'"`) гоняются `pure` + `db`; `heavy`/`live`
— по флагам `--heavy` / `--live`, всё разом — `--all`. Параллель (`pytest-xdist`):
у каждого воркера своя in-memory база (отдельный процесс), пула баз нет. `heavy`
(реальные Alembic-миграции) — только Postgres через `TEST_PG_DSN`, иначе скип.
Полное описание и флаги: [testing.md](../workflow/testing.md) и `tests/README.md`.
