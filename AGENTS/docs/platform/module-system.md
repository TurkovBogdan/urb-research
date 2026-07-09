# module-system — module registration and lifecycle

How domain modules are declared, composed into a FastAPI app, and driven through their lifecycle.

## Module ABC

Every module is a class inheriting `src.core.module.Module`. Declarative class attributes:

| Attribute | Type | Purpose |
|-----------|------|---------|
| `name` | `str` (required) | Unique key. Used as DB migration label, settings namespace, log prefix. |
| `migrations_dir` | `Path \| None` | Path to Alembic `versions/` folder. `None` = no migrations. |
| `config_cls` | `type[BaseSettings] \| None` | Build-time config class (pydantic-settings, reads env). Instantiated once in `create_app`, stored in `app.state.module_configs[name]`. |
| `settings_schema` | `ModuleSchema \| None` | Runtime-tunable settings schema. Registered in settings registry at build time. |
| `internal_router` | `APIRouter \| None` | Sub-router mounted into the `internal` zone by `create_app` (do **not** `app.include_router` in `configure`). `None` = no HTTP. |
| `internal_router_prefix` | `str` | Sub-prefix inside the zone (e.g. `/my-module`); set explicitly — not derived from `name` (kebab vs underscore). |
| `guards` | `dict[str, GuardFn]` | Guard kinds the module contributes (`kind → guard`); core merges them into one shared registry before mounting zones. Empty for most; a future auth module would supply `auth`/`ability`/etc. |
| `mcp_servers` | `dict[str, McpServerBuilder]` | MCP servers exposed as `/mcp/<code>`; value is a constructor fn `(ctx) -> FastMCP` (a function, so declaring it does **not** import `fastmcp` → worker stays clean). |

## Four lifecycle hooks

1. **`configure(app, config)`** — sync, build phase, no DB
2. **`on_settings_change(store)`** — sync, lifespan startup + each settings PUT, DB ready
3. **`on_startup(app)`** — async, all modules ready, DB ready, before scheduler start
4. **`shutdown(app)`** — async, reverse module order, before DB close

### 1. `configure(app, config)` — sync, build phase

Called once during `create_app`. No database, no settings store yet.

Responsibilities:
- `register_tasks()` — register scheduler tasks in the task registry
- Init sync resources with safe no-op defaults (they must work before `on_settings_change` fires)

Routes are **not** registered here — declare the `internal_router`/`internal_router_prefix` class attributes and `create_app` mounts them into the `internal` zone (see [router.md](router.md)).

```python
class MyModule(Module):
    name = "my_module"
    internal_router = internal_router        # from src.modules.my_module.api
    internal_router_prefix = "/my-module"

    def configure(self, app: FastAPI, config: Config) -> None:
        register_tasks()
```

### 2. `on_settings_change(store)` — sync, runtime

Called twice: first time during lifespan startup (after DB + migrations), then on every `PUT /core/settings/{module}` or reset via API (zone-relative; the `internal` zone prepends `/internal`).

Constraints:
- **Sync only.** For async reactions: `asyncio.get_running_loop().create_task(...)` with a `RuntimeError` guard for tests.
- `store` is an immutable pydantic model with the module's settings values.
- Modules that have no runtime-tunable resources can leave this as a no-op.

```python
def on_settings_change(self, store: Any) -> None:
    try:
        client = state.get_client()
    except RuntimeError:
        return  # not yet initialized (test environment)
    client.set_max_concurrent(int(store.max_concurrent))
```

Async reaction pattern (bootstrap that needs DB):
```python
try:
    loop = asyncio.get_running_loop()
    loop.create_task(self._async_bootstrap())
except RuntimeError:
    pass  # no loop in tests
```

### 3. `on_startup(app)` — async, after all modules ready

Called once in lifespan, after all `configure()` calls, DB init, migrations, and initial settings load. Before `scheduler.start()`.

Use for:
- Stale-record cleanup (`session_crud.close_stale_active()`)
- Agent registration (`ScoringAgent.register()`)
- Async seed operations

```python
async def on_startup(self, app: FastAPI) -> None:
    closed = await session_crud.close_stale_active()
    if closed:
        get_logger("my_module").warning("closed %d stale sessions", closed)
    await MyAgent.register()
```

### 4. `shutdown(app)` — async, teardown

Called in **reverse module order** during lifespan `finally`, before `close_database()`.

Use for: closing httpx clients, MCP connections, thread pools, flushing buffers.

```python
async def shutdown(self, app: FastAPI) -> None:
    try:
        mgr = state.get_mcp_manager()
    except RuntimeError:
        return
    await mgr.shutdown()
    state.reset_state()
```

## create_app build sequence

`src/core/app_factory.py`:

```
1. clear task registry + settings registry
2. register_core_tasks()
3. register_settings_schemas(modules)   ← iterates modules, collects settings_schema
4. for m in modules: m.configure(app, config)
5. include core routers (settings API)
6. return app
```

`app.state.module_configs[name]` is populated from `config_cls()` during step 4. Access in `configure`:
```python
cfg = app.state.module_configs[_NAME]  # type: MyModuleConfig
```

## Lifespan sequence

Startup:
1. `init_database(config)`
2. `AlembicRunner(modules).upgrade_head(engine)` — runs all modules' migrations
3. `load_initial_stores(modules)` — fires `on_settings_change` once per module
4. `m.on_startup(app)` for each module in order
5. `scheduler.start(config)`
6. → app serves requests

Shutdown:
1. `scheduler.stop()`
2. `m.shutdown(app)` for each module in **reverse** order
3. `close_database()`

## Config vs Settings

Two separate concepts, both per-module:

| | `Config` (build-time) | `Settings` (runtime) |
|-|----------------------|---------------------|
| Source | Environment variables | Database table `core_modules_settings` |
| Access | `app.state.module_configs[name]` in `configure()` | `get_module_store(name)` anywhere |
| Mutability | Immutable, set before process start | Tunable via `PUT /core/settings/{module}` |
| Hook | `configure(app, config)` | `on_settings_change(store)` |
| Class | `BaseSettings` subclass | `ModuleSchema` with `Field` declarations |
| Example | API keys, base URLs, DB connection | LLM concurrency limit, default provider, cron toggles |

Field types for `ModuleSchema`: `StrField`, `IntField`, `FloatField`, `BoolField`, `ChoiceField`, `ListField`, `MultiChoiceField`, `DateField`, `DateTimeField`.

## Registering a new module

1. Create `src/modules/<name>/module.py` with a class inheriting `Module`.
2. Export from `src/modules/<name>/__init__.py`.
3. Add an instance to the list returned by `build_modules()` in `src/apps/app/modules.py` (the single source of the module list, shared by `server.py` and `app.py migrate`):
   ```python
   def build_modules() -> list[Module]:
       return [..., MyNewModule()]
   ```
4. If the module has migrations, set `migrations_dir = _HERE / "migrations" / "versions"`.
5. Alembic picks up the new folder automatically on next `upgrade_head`.

## Current modules (apps/app)

Pure core registers **no modules** — `build_modules()` (`src/apps/app/modules.py`) returns `[]`. Domain modules are added by appending instances to that list (see *Registering a new module* above).


## AppPath

`AppPath` fields: `root`, `logs`, `cache`, `user`, `import_`, `tmp` (dev: `runtime/dev/...`). `import_` is the root for file-based import sources. `tmp` (`runtime/<profile>/tmp/`) is per-run scratch, created by `ensure_dirs`.
