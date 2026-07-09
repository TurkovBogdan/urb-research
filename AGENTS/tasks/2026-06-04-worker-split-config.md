---
title: Worker-split — config/scheduler rename + app_backend entry point (Part 1)
date: 2026-06-04
status: in-work  # in-work | completed | deferred
description: "Part 1 of the API↔worker split: rename scheduler env/config (SCHEDULER_ENABLED→BACKEND_SCHEDULER_ENABLED default false; SCHEDULER_TICK_SECONDS/MAX→WORKER_*), rename entry point app_api.py→app_backend.py. Parts 2 (app_worker.py + shared runtime) and 3 (module↔FastAPI decoupling) deferred — Part 3 overlaps the api-zones plan."
tags: [scheduler, tasks, config, deploy]
---

## Task

Implement the agreed config/naming slice of the worker split. Plan:
`~/.claude/plans/snoopy-launching-snowglobe.md` (approved); design decisions in
[`AGENTS/tasks/2026-06-03-server-layout-refactor.md`](2026-06-03-server-layout-refactor.md) (RESOLVED
DECISION) + parent plan [`AGENTS/plans/2026-06-03-tasks-worker-split.md`](../plans/2026-06-03-tasks-worker-split.md).

User-confirmed scope for THIS pass (the rest deferred):
- **Part 1** — config + scheduler rename (no `module.py`/router changes; no overlap with api-zones).
- **+ rename** `app_api.py` → `app_backend.py` (entry-point naming unified: `app_backend` + `app_worker` + `app_migrate`).
- **Deferred Part 2** — `app_worker.py`, `build_runtime`/`run_runtime`, `.run/run-worker`.
- **Deferred Part 3** — FastAPI decoupling (`AppContext`, `Module` hook sig `app`→`ctx` across ~11
  modules, lazy router imports). Overlaps the parallel `2026-06-03-api-zones` plan (router restructuring).

## Naming decisions (final)

- `SCHEDULER_ENABLED` → **`BACKEND_SCHEDULER_ENABLED`** (default **`false`**) — embedded scheduler
  inside the web backend. dev `.env`=true (one process = web+tasks); prod web=false (background in the
  standalone worker). The worker ignores it (will force its own ticker).
- `SCHEDULER_TICK_SECONDS` → **`WORKER_TICK_SECONDS`** (5); `SCHEDULER_MAX_CONCURRENT_RUNS` →
  **`WORKER_MAX_CONCURRENT_RUNS`** (10). Engine knobs, shared by embedded (dev) + worker.
- Config fields: `backend_scheduler_enabled` / `worker_tick_seconds` / `worker_max_concurrent_runs`.

## What was done

- `src/core/config.py` — `scheduler_enabled: bool = True` → `backend_scheduler_enabled: bool = False`
  (+ comment); `scheduler_tick_seconds`→`worker_tick_seconds`, `scheduler_max_concurrent_runs`→
  `worker_max_concurrent_runs`; `server_workers` comment `app_api.py`→`app_backend.py`,
  `SCHEDULER_ENABLED`→`BACKEND_SCHEDULER_ENABLED`.
- `src/core/scheduler/__init__.py` — `start()` reads the three renamed fields.
- `tests/conftest.py` — `SCHEDULER_ENABLED`→`BACKEND_SCHEDULER_ENABLED` (test default `false`).
- **Entry point** `app_api.py` → `app_backend.py` (plain `mv`, was untracked): docstring usage lines +
  `SCHEDULER_ENABLED=false`→`BACKEND_SCHEDULER_ENABLED=false`. `.run/run-dev.run.xml` +
  `.run/watch-dev.run.xml` `scriptOrModule` → `app_backend.py`.
- **Env** — `dev/.env.dev.example` (BACKEND_SCHEDULER_ENABLED=true), `dev/.env.prod.example`
  (=false, background in worker), real `.env` (local dev: =true, kept `WORKER_MAX_CONCURRENT_RUNS=1`).
  Real `.env` edited deliberately: new default is `false`, so dev would lose its embedded scheduler
  without it.
- **Docs/memory** — `dev/docs/ENV.md` table, `src/core/scheduler/README.md` lifecycle+settings,
  `AGENTS/docs/core-architecture.md` entry point, `AGENTS/memory/project_architecture.md` scheduler line.

## Result

- `uv run pytest --core` → **169 passed**; scheduler/apps subset 33 passed.
- Smoke: `Config()` reads `backend_scheduler_enabled`/`worker_tick_seconds`/`worker_max_concurrent_runs`;
  `import app_backend` + app boots → **113 routes** (unchanged).
- No remaining live refs to old field names in `src/`/`tests/` (grep clean; only `backend_scheduler_enabled`
  substring matches).

Pending: Part 2 (`app_worker.py` + `build_runtime`/`run_runtime` + `.run/run-worker`) and Part 3
(module↔FastAPI decoupling) — Part 3 to be sequenced with/after the `2026-06-03-api-zones` work to
avoid conflicting edits across all `module.py`.

---

## Stage 2 (2026-06-04) — env regroup + flags + ticker scope + worker run branch

api-zones landed in parallel and subsumed old Part 3 (declarative routers + `backend_api_enabled`
scheduler-only mode), so the heavy `AppContext`/hook-refactor was dropped. This stage replaces the
Part-1 naming with a clean prefix scheme and adds the worker run path. See [[env_prefix_scheme]].

**Decisions (env regroup, flag > env > default).** Process role = composition of SERVER + WORKER
surfaces via `app_backend.py --backend`/`--worker` (+`--no-*`). Renames:
- `APP_PROFILE`→`APP_ENV`, `LOG_LEVEL`→`APP_LOG_LEVEL`.
- `BACKEND_API_ENABLED`→`SERVER_ENABLED`, `BACKEND_SCHEDULER_ENABLED`→`WORKER_ENABLED`.
- `SERVER_WORKERS`→`SERVER_PROCESSES`; `VITE_PORT`→`SERVER_VITE_PORT` (`int|None`, empty=prod).
- NEW `SERVER_HOT_RELOAD` (replaces `is_dev`, which is **removed**); NEW `WORKER_MODULES` (ticker scope).

**What was done.**
- `config.py` — all field renames; dropped `is_dev`; `cors_origins` → `[]` unless `server_vite_port`
  set; added `server_hot_reload`, `worker_modules` + `worker_modules_set` property.
- `app_path.py` — `os.getenv("APP_PROFILE")`→`APP_ENV`.
- `scheduler/__init__.py` — `start()` reads `worker_enabled`/`worker_modules_set`; added
  `configure_worker(modules, max_concurrent, tick)` + `_WORKER_OVERRIDE` (force-start, cleared in `stop()`).
- `scheduler/ticker.py` — `Ticker(modules=…)` + scope filter in `_tick_once`.
- `app_factory.py` / `server.py` — gate by `server_enabled`; `app_log_level`; comments.
- `app_backend.py` — rewritten: `--backend`/`--worker`/`--hot-reload` (BooleanOptionalAction) +
  `--host/--port/--processes/--worker-module/--worker-tick-seconds/--worker-max-concurrent`; flags→env before `Config()`;
  `server_enabled`→uvicorn (reload vs processes by `server_hot_reload`); pure worker→`configure_worker`
  + `create_app` + direct `lifespan_context` + SIGTERM/SIGINT wait; both off → clean no-op exit (code 0).
- `web/vite.config.ts` — `VITE_PORT`→`SERVER_VITE_PORT` (literal fallback).
- `tests/conftest.py` — `APP_ENV`/`SERVER_ENABLED`/`WORKER_ENABLED` + `SERVER_VITE_PORT=13406`.
- Tests updated/added: `test_config` (renames, cors-by-vite, worker_modules_set), `test_app_path`,
  `test_app_factory` (`server_enabled` + renamed test names), `test_main`, core_users conftest;
  NEW `test_scheduler_ticker` scope + override tests; NEW `tests/apps/test_app_backend.py` (argparse/env).
- Env files: `.env` (dev) + `.env.prod` regrouped APP_/SERVER_/WORKER_ blocks. `.run/*` `APP_PROFILE`→
  `APP_ENV`; NEW `.run/run-worker.run.xml`. Docs: `dev/docs/ENV.md`, `scheduler/README.md`,
  `AGENTS/memory/project_architecture.md` + NEW `env_prefix_scheme.md`.

**Result.** `uv run pytest --core` → **194 passed**; `--module=core_users` → 54 passed; scheduler+
app_backend subset 14 passed. Dev launch unchanged (role from `.env`; reload now via `SERVER_HOT_RELOAD`).

**Stage 2b — unified entry point.** `app_backend.py` + `app_migrate.py` merged into a single
**`app.py`**: default (no subcommand) = run server/worker; `app.py migrate [check|upgrade]` subcommand
ports the old migration runner (`AlembicRunner.status`/`upgrade_head`). Old files deleted. Updated:
`.run/{run-dev,watch-dev,run-worker}` → `app.py`; `.run/tool-migrate` → `app.py migrate upgrade`;
test `tests/apps/test_app_backend.py` → `test_app.py` (+ migrate-subcommand parsing/dispatch tests);
all live docs/comments `app_backend.py`/`app_migrate.py` → `app.py`/`app.py migrate`. `tests/apps`
→ 21 passed; `app.py migrate check` smoke → exit 0, up-to-date.

**Deferred (next stage):** run-request signal API→worker (`core_task_requests`, rewrite `trigger_task`).

---

## Stage 3 (2026-06-04) — role-named run configs

User asked for three one-shot run configs along the role axis. Settled prefix scheme:
under `run-*` the second token is the **process role**. `.run/` is a symlink (git doesn't
track it) → managed with plain `rm`/`Write`, no `git rm`.

- **`.run/run-server-worker.run.xml`** (NEW, replaces `run-dev`) — `app.py --backend --worker`,
  `APP_ENV=dev`, before-launch `build-web`. Server + worker in one process.
- **`.run/run-server.run.xml`** (NEW) — `app.py --backend --no-worker`, `APP_ENV=dev`,
  before-launch `build-web`. HTTP-server only.
- **`.run/run-worker.run.xml`** (unchanged) — `app.py --worker --no-backend`, `APP_ENV=dev`
  + `DB_AUTO_MIGRATE=false`. Worker only.
- Deleted old `.run/run-dev.run.xml`.
- Docs/memory: `dev/docs/DEVELOPMENT.md` table (run-dev row → 3 role rows),
  `AGENTS/memory/run_configs.md` (rows + verb-standard note: `run-*` 2nd token = role).

Then two compound groups along the «where the worker lives» axis (before-launch `tool-stop-all`,
mirroring `group-watch`; no Vite — web served as built static by the server):
- **`.run/group-server.run.xml`** (NEW) — wraps `run-server-worker` → server + embedded worker, 1 process.
- **`.run/group-server-worker.run.xml`** (NEW) — wraps `run-server` + `run-worker` → 2 processes.
- Docs/memory updated again (DEVELOPMENT.md group rows, run_configs.md group rows + reworked the
  stale "No separate backend run config" note into a role-axis summary).

## Stage 4 (2026-06-04) — worker hot-reload + Vite-in-groups, drop watch-dev/group-watch

User reshaped the scheme: **both groups run Vite + hot-reload, server AND worker auto-reload**;
`group-watch` removed. Implications: groups serve the frontend via Vite (`watch-web`), so the backend
no longer needs built static → `run-server*` lose before-launch `build-web` and become watch-style
(`--hot-reload`, `DB_AUTO_MIGRATE=false`); old `watch-dev` is now redundant (its role = `run-server-worker`).

**Worker hot-reload (the only code change).** `--hot-reload` previously hit only the SERVER path
(uvicorn `--reload`); a standalone worker (`asyncio.run(_run_worker)`) had no reload. Wired the *same*
key to the worker:
- `pyproject.toml` — added `watchfiles>=0.24` (main deps; lazy-imported, only on hot-reload). `uv sync`
  → watchfiles 1.2.0.
- `app.py` — new `_run_worker_hot_reload()`: `watchfiles.run_process(src/, target="<py> app.py --worker
  --no-backend --no-hot-reload")` — restarts a fresh worker subprocess on `src/` change (`--no-hot-reload`
  avoids watch-on-watch; scope inherited via env). `main()` pure-worker branch: `server_hot_reload` →
  supervisor, else direct `asyncio.run`. Broadened docstrings + `--hot-reload` help.
- `config.py` — `server_hot_reload` comment now "common key for both surfaces".
- Tests `tests/apps/test_app.py` — NEW `test_main_pure_worker_hot_reload_branch` (dispatch) +
  `test_run_worker_hot_reload_spawns_no_reload_child` (command shape). 23 passed.
- Smoke: `app.py --worker --no-backend --hot-reload` → watchfiles boots worker child, lifespan startup
  over all modules, SIGTERM → clean lifespan shutdown + "stopping watch".

**Run configs (final).**
- `run-server-worker` / `run-server` / `run-worker` — all `app.py … --hot-reload`, `APP_ENV=dev` +
  `DB_AUTO_MIGRATE=false`, no `build-web`.
- `group-server` = `tool-stop-all` → `watch-web` + `run-server-worker` (embedded worker).
- `group-server-worker` = `tool-stop-all` → `watch-web` + `run-server` + `run-worker` (split).
- Deleted `.run/group-watch.run.xml` + `.run/watch-dev.run.xml`. `watch-web` kept (used by both groups).
- Docs/memory: DEVELOPMENT.md table + hot-reload prose (app_run.py→app.py role flags), ENV.md
  `SERVER_HOT_RELOAD` row (both surfaces), `run_configs.md` rebuilt.

## Stage 5 (2026-06-04) — entry points moved into src/ (declutter root)

User asked to move `app.py` + `app_hash_password.py` into `src/` (goal: clean project root).
Feasible; bare `mv` would break because both bootstrap `sys.path` via `Path(__file__).parent`
(= project root when at root). Done:
- `mv app.py src/app.py`, `mv app_hash_password.py src/app_hash_password.py`.
- Both: `sys.path.insert(0, Path(__file__).parent)` → `parents[1]` (root is now src/'s parent),
  so `from src.* import` keeps resolving.
- `src/app.py`: the two `Path(__file__).parent / "src"` joins (`reload_dirs` in `_run_server`,
  `src_dir` in `_run_worker_hot_reload`) → `Path(__file__).parent` (file already lives in src/).
- Run invocation is now `uv run python src/app.py …` (and `src/app_hash_password.py`).
- Run configs (`dev/.run/{run-server,run-server-worker,run-worker,tool-migrate}.run.xml`):
  `scriptOrModule` `$PROJECT_DIR$/app.py` → `$PROJECT_DIR$/src/app.py` (CWD stays project root).
- Doc/comment refs rebased to `src/app.py`/`src/app_hash_password.py`: `dev/docs/{ENV,DEVELOPMENT}.md`,
  `src/core/database/README.md`, `src/core/scheduler/README.md` + `__init__.py` comment,
  `src/core/config.py:63`, `src/modules/core_users/README.md`, `AGENTS/docs/{core-architecture,router}.md`,
  `AGENTS/tools/stop-all.sh` comment, `.env`/`.env.dev`/`.env.prod` comments. Historical memory/plans/
  tasks left as-is.

**Gotcha (verified):** `tests/apps/test_app.py` does a bare `import app`; it keeps working because
pytest `pythonpath = ["src"]` now puts `src/` on the path → `import app` resolves to `src/app.py`.
Running `python src/app.py` also auto-adds `src/` to `sys.path[0]` → `core`/`apps`/`modules` become
importable top-level (the latent [[project_src_pythonpath_shadow]]); no code imports them unprefixed,
so no breakage today. **Result:** `pytest tests/apps/test_app.py` → 23 passed; smokes
`src/app.py --help` (exit 0), `src/app.py migrate check` (DB reachable, up-to-date),
`src/app_hash_password.py` (import chain resolves).
