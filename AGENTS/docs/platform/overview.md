# urb-research — project overview

`urb-research` (UI brand **Uroboros.Research**) is an MCP server over a research registry: the `research` module (registry + MCP tools) on top of `web_search` (web search + saved pages) and `core_connectors` (Tavily / Firecrawl / xAI / OpenRouter / OpenAI / Anthropic), plus the infra modules `core_setup` / `core_monitoring` / `core_mcp`. The platform core it sits on was ported from a donor project.

Runs **headless from source** — no packaged binary. See [env_prefix_scheme](../../memory/env_prefix_scheme.md).

## Stack

- **Frontend:** Vue3 + Vuetify 4 + Pinia + Vue Router + SCSS + Tabler Icons, built with Vite → `web/dist/` (committed to git; served by the backend itself in prod, by Vite in dev).
- **Backend:** FastAPI + uvicorn, Python ≥3.12; run from source via `src/app.py` (`--backend` / `--worker` / `--mcp-stdio` / `migrate`).
- **Database:** SQLite by default (single file, no server), PostgreSQL optional — `DB_PROVIDER`.
- **JS package manager:** pnpm (workspace — `node_modules` at root).

## Ports

Defined in `.env`: `SERVER_PORT` (dev :12200) | `SERVER_VITE_PORT` (dev :12100) | prod backend :13410, reachable directly. Profile env = `APP_ENV` (`dev` / `test` / `prod`), not the old `APP_PROFILE`.

## Run scenarios

1. **Dev** — Vite (`pnpm --dir web dev` on `SERVER_VITE_PORT`, HMR + proxy `/api`, `/internal` → backend) + `src/app.py --backend --worker --hot-reload` (server + embedded worker). IDE compound `group-server`. `APP_ENV=dev`, `DB_AUTO_MIGRATE=false`.
2. **Prod** — `src/app.py --backend --worker` serves the API and `web/dist/` on `SERVER_PORT`; the worker may also be split into its own `--worker` process. No web server in front. Deploy = `git pull` + `uv sync`.

## How to apply

When adding an API — inside the module (`src/modules/<name>/api.py`); the module exports a `Module` subclass via `__init__.py`, listed in `src/apps/app/modules.py::build_modules()` and assembled by `create_app(build_modules(), config)`. The backend also serves the built SPA: `src/core/router/spa.py::mount_spa` returns `web/dist` files for any GET outside the API prefixes (in dev the SPA comes from Vite instead).
