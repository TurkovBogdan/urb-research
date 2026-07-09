# core-loggers — logging channels

One channel = one file `logs/<channel>.log`. No hierarchy, no propagation to `logging.root`.

Slash in channel name → subdirectory: `agents/dispatch` → `logs/agents/dispatch.log`. Subdirectories are created automatically.

## Public API

```python
from src.core.loggers import get_logger, set_logger_factory, LoggerStore
```

| Name | Purpose |
|------|---------|
| `get_logger(*channels)` | proxy for one or more channels; no args → `core`; ≥2 channels → tee (fan-out) |
| `set_logger_factory(factory)` | bootstrap: set `(channel) -> CoreLoggerProtocol` factory |
| `LoggerStore` | channel registry; `set/reset` for tests |

## Core channels

| Channel | Where | File |
|---------|-------|------|
| `core` | default `get_logger()` | `logs/core.log` |
| `tasks` | `core/scheduler/{runner,ticker,context}.py` | `logs/tasks.log` |
| `tasks/{code}` | scheduler runner + `TaskContext` per task | `logs/tasks/<code>.log` |

Modules define their own channels freely — channels are created on first use.

### Channel convention

- Core: flat (`core`, `tasks`).
- Modules: `modules/<name>` (e.g. `modules/my_module`).
- Agents: `agents/<name>` (`agents/dispatch`).
- Subtasks tee into the parent — e.g. the scheduler runner uses `get_logger("tasks", f"tasks/{code}")`.
- A module may expose its channel via a `LOG_CHANNEL` const.

## Global stdout/stderr tee

`src/core/loggers/global_log.py::install()` redirects `sys.stdout`/`sys.stderr` to a `_TeeStream` (original stream + `logs/app.log`). Call it as early as possible at process start — it works for any entry point (server/worker) and is independent of the channel system.

## Usage

```python
_LOG = get_logger("page_scraper")             # single channel
_LOG = get_logger()                           # default → "core"
_LOG = get_logger("tasks", "tasks/my_task")  # tee: both files get the message
```

`set_level` on a tee applies to all channels.

## How the proxy works

`get_logger(...)` returns a **proxy**, not a logger instance. Each log call resolves through `LoggerStore` at call time:

```python
_LOG = get_logger("tasks")   # _LoggerProxy("tasks") — created at import time, before bootstrap
# ...later, bootstrap calls set_logger_factory(...)
_LOG.info("started")         # resolves through the new factory now
```

Without the proxy, module-level `_LOG = get_logger(...)` would capture the pre-bootstrap default instance and ignore configuration.

## Bootstrap

Called in `src/apps/app/server.py` at import (module-level), before `create_app` — not in lifespan:

```python
def _bootstrap_logger(config: Config) -> None:
    paths = AppPath.from_root()
    ensure_dirs(paths)

    def factory(channel: str) -> CoreLogger:
        return CoreLogger(logs_dir=paths.logs, file_name=channel, level=config.log_level)

    set_logger_factory(factory)
```

`set_logger_factory` clears all cached channel instances so early imports don't stick with the default factory.

## Tests

```python
@pytest.fixture(autouse=True)
def _reset_store():
    LoggerStore.reset()
    yield
    LoggerStore.reset()
```

Pin a specific instance to a channel:
```python
LoggerStore.set(my_logger, "tasks")   # fix instance
LoggerStore.set(None, "tasks")        # remove override; next get() recreates via factory
```
