---
title: Server / Docker migration
date: 2026-06-02
status: in-work
description: "Migrate the main app from a PyInstaller desktop binary (Qt GUI + embedded FastAPI) to a headless server running inside a Docker container. PyInstaller stays for the MCP build on the same codebase — MCP delivery model TBD."
tags: [deploy, docker, build, mcp]
---

## Task

Deploy the application to a server, running inside a Docker container. Drop the PyInstaller
scenario for the main app. PyInstaller stays for the MCP build (same codebase) — but how MCP
is delivered/run in the server world is an open question.

## Context

Current packaging (see `app_build.py`, `app_run.py`, `src/apps/app/gui.py`):
- Main app = single PyInstaller `--onefile` binary `urb-research`: Qt status window + embedded
  FastAPI (`ServerThread` runs uvicorn in a thread); serves its own SPA static on `:13410`.
- MCP = separate PyInstaller binary `urb-research-mcp` (`app_run_mcp.py <server>`), 5 stdio servers.

Key architecture findings for headless migration:
- `src/apps/app/server.py` `app` is ALREADY a complete headless server: its `lifespan` runs
  init_database → Alembic upgrade_head → module on_startup → scheduler.start. Qt is purely a
  desktop browser shell. ⇒ headless run = `uvicorn src.apps.app.server:app`.
- No hard Qt dependency in the backend (only a qasync *comment* in `llm_providers/api.py`).
- `mount_spa` (`src/apps/app/web.py`) already serves from `dist/build/web` in non-frozen mode.
- `Config`: `server_host` default `127.0.0.1` → set `0.0.0.0` via env in container; DB TLS certs
  resolve relative to app root → mount + set `DB_CERT`. `db_auto_migrate=True` ⇒ migrations on boot.

## Open decisions (to resolve with user)

- Target DB: external/remote PG (current hardening) vs PG sidecar/compose vs managed.
- SPA serving: keep FastAPI serving static (single container) vs nginx/Caddy in front + TLS term.
- MCP delivery: keep PyInstaller binary for local laptop use vs run MCP in-container over
  streamable-HTTP vs both. ← the user-flagged unknown.
- Scheduler with >1 replica (CoreLock makes it safe-ish) — likely single replica.
- Build base image / uv-in-image / multi-stage (node web build + python runtime).

## What was done

- Confirmed backend is headless-ready (FastAPI lifespan owns DB/migrations/modules/scheduler; Qt is
  only a desktop shell). No hard Qt dep in backend.
- Created **`app_api.py`** — headless uvicorn launcher (reads `Config`, runs `src.apps.app.server:app`,
  host/port/workers/log from `.env`). No Qt, no SPA mount (nginx serves static).
- Added **`Config.server_workers`** (env `SERVER_WORKERS`, default 1).
- Decided deploy topology: docker-compose, edge nginx → project nginx; project nginx serves `static/`
  (built SPA, git-tracked) + proxies `/api` → python (`app_api.py`). Deploy = `git pull` inside the
  app container; migrations run on the spot via `app_migrate.py`.
- Decided web container runs nothing built for backend (Python interpreted; runs from `src/`). Only the
  frontend is built (`pnpm build` → `static/`, Vite `outDir`).
- File-storage security model laid in under **`storage/`**: **`storage/public`** (nginx direct,
  `location /media/`) and **`storage/protected`** (nginx `internal` + backend `X-Accel-Redirect`
  after `core_auth` permission check). Created `storage/public/.gitkeep` + `storage/protected/.gitkeep`;
  `.gitignore` keeps folders, ignores contents. Endpoint + `AppPath` wiring deferred until `core_auth`
  exists (nothing to gate on yet).
- Established the app is near-stateless on disk: state in Postgres; only filesystem touch is
  `runtime/<profile>/import/gmail-mbox/` (manual mbox drop) + logs/cache/tmp. Email attachments are
  NOT stored (only `has_attachments` flag); bodies live in DB.

## Open / next

- Web container: 1 uvicorn process to start; `SCHEDULER_ENABLED=false`, `DB_AUTO_MIGRATE=false`.
- Worker container (scheduler) + optional `core_jobs` Postgres queue (`FOR UPDATE SKIP LOCKED`) — TBD.
- `core_auth` module (server-side session cookie + Argon2id) + generic middleware (request-id, error
  envelope, security headers) — TBD; gates `protected/` file serving.
- Move `PySide6`/`qasync` out of core `dependencies` into an optional `gui` group (server image skips them).
- Dockerfile (backend) + nginx conf + `docker-compose.yml` + Vite `outDir=../static` — TBD.

## new_structure — standalone layout boilerplate (verified)

Built `new_structure/` as a self-contained, copyable mock of the on-server layout (no parent
dependency). Verified live: `app_api.py` boots; `/api/health`→200, `/api/db`→503 w/o DB_* (SELECT 1
once set), `/api/files/{name}`→streams from storage/protected (200) / 404. Relative symlinks
(`static/storage/public→../../storage/public`, `runtime/prod/{storage,web}`). Own minimal
`pyproject.toml`+`uv.lock` (fastapi/uvicorn/sqlalchemy/asyncpg/pydantic-settings), own `.gitignore`
(check-ignore verified), Vue+Vuetify 4-button smoke page built into `static/` (Vite `emptyOutDir:false`
+ clean-only-`static/assets` so `static/storage` survives). Open cosmetics: favicon 404 (no web/public).
NB: this is a mock/boilerplate — real-app changes so far are only `app_api.py` + `Config.server_workers`
(the experimental `/api/db` was reverted out of `src/apps/app/server.py`).

## Result

- `app_api.py` (new), `src/core/config.py` (+`server_workers`), `public/.gitkeep`,
  `protected/.gitkeep`, `.gitignore` (file-storage block). Planning logged; migration in progress.

## Stage (2026-06-04) — prod `.env.prod` assembled (SERVER role)

User asked to build the boevoy `.env.prod`. Framing: this file = the SERVER role's config;
the worker is a separate process running the same `app.py --worker --no-backend`, overriding
its knobs via CLI (`--worker-module`/`--worker-tick-seconds`/`--worker-max-concurrent`, flag > env).

Decisions: nginx in a separate container → `SERVER_HOST=0.0.0.0`; worker = separate process →
`WORKER_ENABLED=false`; **DB without TLS** (`DB_SSL=false`) — trusted app↔DB network on the server.
All secrets/credentials stay `CHANGE_ME` (DB password, all LLM/Intercom/Twenty tokens, admin
email+hash) — user wants no secrets committed; non-secret config (hosts, ports, pool/session
knobs) is filled.

**Follow-up (same day) — turned into committed templates.** The files were renamed root
`.env.prod`/`.env.dev` → `.env.example.prod`/`.env.example.dev` (both real ones deleted) so they
go INTO the repo as no-secret templates. Gotcha: `.gitignore` had `.env` + `.env.*` + `!.env.example`
— the `.example.{prod,dev}` names still matched `.env.*` and were IGNORED. Fixed by adding
`!.env.example*` (covers `.env.example`, `.env.example.dev`, `.env.example.prod`); verified the live
`.env` stays ignored. Stripped ALL secrets to `CHANGE_ME` incl. `TWENTY_BASE_URL` (the real CRM host).
`ENV.md` template link repointed from the (untracked) `dev/.env.{dev,prod}.example` to the new root
files. NB pre-existing `dev/.env.dev.example` / `dev/.env.prod.example` are stale + untracked (ignored)
— left for the user to clean up.

The user's draft used pre-`env_prefix_scheme` names (`APP_PROFILE`/`SERVER_WORKERS`/
`SCHEDULER_ENABLED`/`app_migrate.py`) which `Config` no longer has (`extra="ignore"` would
silently drop them). Rewrote to current names: `APP_ENV`/`SERVER_PROCESSES`/`WORKER_ENABLED`,
migrations via `app.py migrate upgrade`, `app_hash_password.py` (not the deleted PyInstaller
hash binary). DB block uses prod values from the draft (`external-database`/`urb_research`).
Flagged: admin hash is still the dev one (dev password) → regenerate for prod.

## Stage (2026-06-04) — container artifacts live (supervisord, multi-process)

The deployment artifacts (previously "TBD") now exist alongside the project checkout in the
deployment dir `containers/projects/core.example.com/` (OUTSIDE the app repo): `docker-compose.yml`,
`docker/backend/` (Dockerfile + entrypoint + `supervisor/supervisord.conf`), `docker/nginx/`,
`tools/` (`connect.sh`, `migrate.sh`).

Done this stage:
- **supervisord** drives the backend container (image gained `apt-get install supervisor`; `CMD` →
  `supervisord -c …`). Two programs off the SAME `src/app.py`: `server` =
  `--backend --no-worker` (uvicorn, may fork `SERVER_PROCESSES`), `worker` =
  `--worker --no-backend` with `numprocs=%(ENV_WORKER_COUNT)s` identical processes. All logs →
  container stdout/stderr (`maxbytes=0`, no rotation/seek on the pipe); local control socket for
  `supervisorctl status`. `WORKER_COUNT` plumbed through compose `.env` (default 3); verified
  env-expansion in `numprocs` actually spawns N workers.
- **entrypoint.sh fixed for the refactor**: it called the now-gone `project/storage_mount.sh`; the
  script moved to `tools/storage_mount.sh` and takes a profile. Now runs
  `tools/storage_mount.sh --prod` (matches `APP_ENV=prod`) before exec'ing supervisord.
- **`tools/migrate.sh`** — explicit deploy migration step: `docker exec` into the backend container
  and run `uv run --frozen python src/app.py migrate <upgrade|check>` (default `upgrade`). Pairs
  with `DB_AUTO_MIGRATE=false`.
- **`project/.env` (boevoy, gitignored)** assembled from `.env.example.prod` with real DB creds from
  `backup/.env.bak` (`DB_HOST=external-database` confirmed = postgres alias on the `postgresql-primary`
  network; container `postgresql-primary_external-database`, `postgres:18`). User filled the remaining
  secrets (LLM/Intercom/Twenty/admin) in place.
- **`static/` frontend** now lands via `git pull` (built SPA committed); nginx serves it as docroot.
- **BUILD.md** got a "Контейнерный деплой (Docker)" section; top "в работе" note updated.

## Stage (2026-06-04 cont.) — live bring-up, tuning, bugfix

End-to-end verified against the live host (4× Neoverse-N1, 7.7GB RAM, 75GB disk; DB =
`postgresql-primary_external-database`, postgres:18):
- `docker compose up -d --build` brings up server + 3 workers under supervisord; entrypoint
  wires symlinks and runs migrations. Health endpoint moved (old `/api/health` now 404) but
  uvicorn serves (`Application startup complete`, `:13410`).
- **mem_limit 512m → 2g, cpus 1.0 → 2.0**: at 512m the workers were OOM-killed (exit 137,
  crash loop) — 1 server + 3 workers each import the full app (~200-300MB RSS incl. PySide6).
  Now steady ~600MiB/2g. (Reinforces the open item: move PySide6/qasync to an optional group.)
- **Per-worker limits via CLI** (user request): worker command now
  `--worker-max-concurrent 3 --worker-tick-seconds 5` (the full worker knob set; `--worker-module`
  left unset = all modules). Total fleet parallelism = 3 × WORKER_COUNT.
- **Migrations moved into `entrypoint.sh`** (user request): single `migrate upgrade` before
  supervisord — avoids cross-process races; `DB_AUTO_MIGRATE` stays false.
- **BUG FIX in `src/app.py::_run_migrate`**: the `upgrade` branch was inverted
  (`if not status.up_to_date: return 0` → skipped the upgrade whenever there WERE pending, and
  only ran `upgrade_head` when already at head). `migrate upgrade` never applied anything. Fixed
  to `if status.up_to_date: return 0` else upgrade. Verified: applied 3 pending
  (cu02_email_partial_unique, ci06_result_session_id, …) → now at head; re-run idempotent.

Still open:
- MCP delivery in the server world (the original user-flagged unknown) — untouched.
- Move `PySide6`/`qasync` out of core `dependencies` into an optional `gui` group (shrinks image
  + per-process RSS, the OOM driver).
- `core_auth` module + middleware (gates `protected/` file serving).
- Health endpoint path drift: BUILD.md smoke test still lists `/api/health` (now 404) — confirm
  the new liveness path and update the doc.
