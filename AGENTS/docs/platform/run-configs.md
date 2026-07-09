# IDE run configurations

All configs in `dev/.run/`, used in PyCharm/IntelliJ. Filenames are `<category>-<name>.run.xml`, following a verb standard: **run** (one-shot run), **watch** (continuous dev rebuild), **build** (prod dist), **test** (test runs), **sync** (deps), **tool** (utilities), **group** (compounds). For `run-*` the second token is the **process role** — `server-worker` / `server` / `worker` (`app.py --backend`/`--worker` composition).

| File | Type | What it does |
|------|------|-------------|
| `run-server-worker.run.xml` | UvRunConfigurationType | **server + worker** in one process: `app.py --backend --worker --hot-reload`, `APP_ENV=dev` + `DB_AUTO_MIGRATE=false`. Embedded worker reloads with uvicorn `--reload`. Replaced the old `run-dev`/`watch-dev` |
| `run-server.run.xml` | UvRunConfigurationType | **HTTP-server only**: `app.py --backend --no-worker --hot-reload`, `APP_ENV=dev` + `DB_AUTO_MIGRATE=false` |
| `run-worker.run.xml` | UvRunConfigurationType | **worker only** (scheduler + tasks, no HTTP): `app.py --worker --no-backend --hot-reload`, `APP_ENV=dev` + `DB_AUTO_MIGRATE=false`. Standalone worker reloads via `watchfiles` (see Role axis) |
| `group-server.run.xml` | Compound | **Main dev (embedded worker)**: before-launch `tool-stop-all` → `watch-web` (Vite HMR) + `run-server-worker` |
| `group-server-worker.run.xml` | Compound | **Main dev (split)**: before-launch `tool-stop-all` → `watch-web` (Vite HMR) + `run-server` + `run-worker` |
| `watch-web.run.xml` | js.build_tools.npm | `pnpm dev` in `web/`, Vite HMR on `SERVER_VITE_PORT` (currently :12100); serves the frontend **source** for both groups |
| `build-web.run.xml` | js.build_tools.npm | `pnpm build` in `web/` → `web/dist/` (committed); one-shot prod web build (groups use Vite, not this). No `build-app` config — there's no binary build anymore (headless from source) |
| `preview-web.run.xml` | js.build_tools.npm | `pnpm preview` in `web/`, `vite preview` serving the **built** `web/dist/` on `SERVER_PREVIEW_PORT` (default `SERVER_VITE_PORT`+1 → :12101); proxies `/api`+`/internal` to the backend. Use it to view the committed SPA artifact (run `build-web` first to refresh); backend is API-only and never serves the SPA |
| `test.run.xml` | pytest | Default run with coverage. `addopts = -m 'not heavy and not live'` → pure+db |
| `test-all.run.xml` | pytest | `--all` — everything incl. heavy + live |
| `test-heavy.run.xml` | pytest | `--heavy` — real Alembic migration tests |
| `test-live.run.xml` | pytest | `--live` — real external services + creds |
| `test-lost.run.xml` | pytest | `--unmarked` audit — finds tests missing a type marker |
| `sync-app.run.xml` | ShConfigurationType | `uv sync --all-groups` — all deps incl. test/build groups |
| `sync-web.run.xml` | js.build_tools.npm | `pnpm install` in `web/` |
| `tool-migrate.run.xml` | UvRunConfigurationType | `src/app.py migrate upgrade` with `APP_ENV=dev` — standalone migration apply (`migrate check` = dry-run) |
| `tool-stop-all.run.xml` | ShConfigurationType | `AGENTS/tools/stop-all.sh` — kills `SERVER_PORT`/`SERVER_VITE_PORT`/:13410 |

## Role axis

`app.py` composes SERVER + WORKER surfaces (`--backend`/`--worker`). Run configs: `run-server-worker` (both, one process), `run-server` (HTTP only), `run-worker` (worker only) — all `--hot-reload`, `DB_AUTO_MIGRATE=false`, no web build (Vite serves the frontend). Compounds add Vite: `group-server` = `watch-web` + `run-server-worker` (embedded worker), `group-server-worker` = `watch-web` + `run-server` + `run-worker` (split). `group-watch`/`watch-dev` removed (2026-06-04).

## Hot-reload covers both surfaces

Same `--hot-reload` / `SERVER_HOT_RELOAD` key. SERVER → uvicorn `--reload`. A *standalone* worker has no uvicorn, so `app.py._run_worker_hot_reload` supervises it with `watchfiles.run_process`: on `src/` change it restarts a fresh `app.py --worker --no-backend --no-hot-reload` subprocess (the `--no-hot-reload` avoids watch-on-watch recursion; worker scope inherited via env). `watchfiles` is a main dependency. The embedded worker (with SERVER) reloads together with uvicorn.

## History

Renamed 2026-05-30 to the verb standard, then to `<category>-<name>`; role-named run configs + worker hot-reload + Vite-in-groups 2026-06-04.
