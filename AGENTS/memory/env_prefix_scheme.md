---
name: env_prefix_scheme
description: Core (non-module) env vars regrouped under APP_/SERVER_/WORKER_ prefixes; process role = SERVER+WORKER surfaces via --backend/--worker flags
metadata: 
  node_type: memory
  type: project
  originSessionId: 896ff2ea-d8e1-471a-929a-cb3d4d0ce448
---

Core (non-module) env was renamed into clean umbrella prefixes (2026-06-04, worker-split work). Process role is a **composition of two surfaces** — SERVER (HTTP transport: internal/external/webhook) + WORKER (scheduler + tasks) — set by `app.py --backend`/`--worker` (and `--no-*`), priority **flag > env > default**. dev = both on; prod-web = SERVER only; prod-worker = WORKER only. Pure worker (no SERVER) runs WITHOUT uvicorn/port: lifespan driven directly via `app.router.lifespan_context`, ticker forced through `scheduler.configure_worker`.

Renames (env → `Config` field):
- `APP_PROFILE`→`APP_ENV` (`app_env`); also raw `os.getenv("APP_ENV")` in `app_path.py`. After dropping `is_dev`, APP_ENV's ONLY effect is selecting `runtime/<env>/`.
- `LOG_LEVEL`→`APP_LOG_LEVEL` (`app_log_level`)
- `BACKEND_API_ENABLED`→`SERVER_ENABLED` (`server_enabled`)
- `BACKEND_SCHEDULER_ENABLED`→`WORKER_ENABLED` (`worker_enabled`)
- `SERVER_WORKERS`→`SERVER_PROCESSES` (`server_processes`) — uvicorn process count, renamed to avoid confusion with the background WORKER
- `VITE_PORT`→`SERVER_VITE_PORT` (`server_vite_port: int|None=None`, empty=prod) — dev-CORS + Vite proxy target; `cors_origins` is `[]` when unset; `web/vite.config.ts` reads it with literal fallback `'13406'`
- NEW `SERVER_HOT_RELOAD` (`server_hot_reload: bool=False`) — replaces `is_dev` as the reload-vs-processes gate in `app.py`; hot-reload of the server on `src/` changes (uvicorn `--reload`), dev-only, incompatible with `SERVER_PROCESSES>1`. **`is_dev` removed** (no consumers left).
- NEW `WORKER_MODULES` (`worker_modules` CSV → `worker_modules_set: frozenset|None`) — ticker scope by `entry.module`; empty=all
- `WORKER_TICK_SECONDS`/`WORKER_MAX_CONCURRENT_RUNS` unchanged

Untouched: `DB_*`/`TEST_DB_*`/`DB_AUTO_MIGRATE`/module prefixes (`LLM_PROVIDERS_*`/`INTERCOM_*`/`TWENTY_*`/`CORE_USERS_*`).

**Why:** make the process role explicit (flags) and env self-grouping; `SERVER_`=transport (shared by all HTTP surfaces), `WORKER_`=background, `APP_`=identity. Files touched: `config.py`, `app_path.py`, `app_factory.py`, `server.py`, `app.py`, `web/vite.config.ts`, `tests/conftest.py`, `.env`, `.env.prod`, `dev/docs/ENV.md`, `scheduler/README.md`. See [[run_configs]] (run-config flags may need updating next). Related: [[project_architecture]].
