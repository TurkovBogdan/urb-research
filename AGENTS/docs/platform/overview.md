# core_semaphore — project overview

`core_semaphore` is the platform core being extracted from `hh-support-agent` as the foundation for new projects.

Runs **headless from source** — no packaged binary. The Qt GUI (`src/gui/`) and the MCP apps were removed in the web-server refactor (commit "refactor for web server"). See [env_prefix_scheme](../../memory/env_prefix_scheme.md).

## Stack

- **Frontend:** Vue3 + Vuetify 4 + Pinia + Vue Router + SCSS + Tabler Icons, built with Vite → `static/` (committed to git, served by nginx in prod / Vite in dev).
- **Backend:** FastAPI + uvicorn, Python ≥3.12; run from source via `src/app.py` (`--backend` / `--worker` / `migrate`).
- **JS package manager:** pnpm (workspace — `node_modules` at root).

## Ports

Defined in `.env`: `SERVER_PORT` (dev :12200) | `SERVER_VITE_PORT` (dev :12100) | prod backend :13410 behind nginx. Profile env = `APP_ENV` (`dev` / `test` / `prod`), not the old `APP_PROFILE`.

## Run scenarios

1. **Dev** — Vite (`pnpm --dir web dev` on `SERVER_VITE_PORT`, HMR + proxy `/api`, `/internal` → backend) + `src/app.py --backend --worker --hot-reload` (server + embedded worker). IDE compound `group-server`. `APP_ENV=dev`, `DB_AUTO_MIGRATE=false`.
2. **Prod** — nginx serves `static/` + proxies to `src/app.py --backend`; `src/app.py --worker` runs as a separate process. Deploy = `git pull` + `uv sync`.

## How to apply

When adding an API — inside the module (`src/modules/<name>/api.py`); the module exports a `Module` subclass via `__init__.py`, listed in `src/apps/app/modules.py::build_modules()` and assembled by `create_app(build_modules(), config)`. The backend is API-only — the SPA is served by nginx (prod) / Vite (dev), never by the backend.
