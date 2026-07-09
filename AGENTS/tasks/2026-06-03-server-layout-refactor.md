---
title: Server-layout refactor (headless API + nginx static + storage split)
date: 2026-06-03
status: in-work  # in-work | completed | deferred
description: "Refactor core_semaphore from the Qt-GUI + PyInstaller-binary model to the on-server layout described in new_structure/README.md: headless API (app_api.py) behind nginx, committed built static/, public/protected storage split. Deploy target: server core.example.com (docker-compose: nginx + thin uv backend)."
tags: [deploy, build, frontend, layout]
---

## Task

Refactor the project to the structure described in `new_structure/README.md`. Decisions
confirmed with the user:
- Qt GUI removed entirely; app becomes headless-only (`app_api.py`).
- Frontend build → committed `static/` (drop the PyInstaller binary deploy path).
- Proceed in phases, starting with the frontend reconfiguration.
- Deploy target: `/path/to/deploy/core.example.com`
  (docker-compose: `nginx:1.27-alpine` serving `project/static` + thin `python+uv` backend
  running `app_api.py`; storage symlinks via `storage_mount.sh`).

## Context

`new_structure/` is a self-contained boilerplate of the on-server layout (the deploy target's
`project/` was seeded from it). The real app keeps its modules/DB/scheduler/MCP but switches its
deploy + packaging model: nginx serves a git-committed built `static/`, the backend is API-only
(uvicorn), and durable files live in `storage/{public,protected}` reached via deploy symlinks.

## Phases

1. **Frontend → committed `static/`** (this pass): vite `outDir=../static` + `emptyOutDir=false`,
   build script cleans only `static/assets`, commit built `static/`, `.gitignore` updates.
2. Backend headless + storage split: `/api/files` (protected, X-Accel-Redirect), AppPath `prod`
   profile + storage paths, `storage_mount.sh`.
3. Remove Qt GUI: `src/gui/`, `app_run.py`, `run_gui_app`, Qt deps, PyInstaller (`app_build.py`),
   GUI `.run` configs.
4. Deploy wiring: `runtime/prod` + symlinks, align with the server docker-compose/nginx, `.env.example`.
5. Cleanup: drop `dist/`/mcp-build leftovers, update docs/memory.

## What was done

**Phase 1 — Frontend → committed `static/`** (done):
- `web/vite.config.ts`: `build.outDir` `../dist/build/web` → `../static`; `emptyOutDir` `true` → `false`
  (so the build never wipes `static/storage`).
- `web/package.json`: build script now cleans only `../static/assets` (node `fs.rmSync`) before `vite build`.
- `src/apps/app/web.py`: `_web_root()` now points at repo-root `static/` (was `dist/build/web`); dropped
  the `sys.frozen`/`_MEIPASS` branch (PyInstaller deploy path being removed). Backend SPA mount kept for
  local one-shot dev; nginx serves `static/` in prod.
- `.gitignore`: `static/` is committed (built SPA travels via git pull); `/static/storage/public` (deploy
  symlink) ignored. `static/storage/.gitkeep` real folder added.
- Ran `pnpm build` → `static/` populated (verified `static/storage/.gitkeep` survives the build).

**Entry-point switch + old-build teardown** (done, pulled forward from phases 3/5):
- `app_api.py` (repo root) is now the canonical entry point: `uvicorn src.apps.app.server:app`,
  host/port/workers/log_level from `Config`. Verified the target app imports cleanly (113 routes);
  `create_app` lifespan already wires DB init + Alembic (gated by `DB_AUTO_MIGRATE`) + module startup +
  scheduler, so headless boot is complete. `gui.py` only added the Qt shell around the same `app`.
- Deleted `app_build.py` (the PyInstaller binary builder — sole code carrier of `assets/` refs; obsolete
  under the git-pull deploy model) and its IDE configs `.run/build-app.run.xml`, `.run/build-mcp.run.xml`.
- `assets/` removed by the user (Qt icon + local prod secrets + a stray mbox). `.gitignore`: dropped the
  now-dead `/assets/prod/` rule.

**`old/` archive** (user-created dustbin for retired-concept artifacts):
- `git mv app_run.py old/app_run.py` (old Qt entry), `git mv app_run_mcp.py old/app_run_mcp.py` (MCP launch).
- `assets/` also moved here by the user (`old/assets/`).
- Root now has only the live entries: `app_api.py` (API) + `app_migrate.py` (migrations).
- DANGLING after the MCP-launch move (open decision — retire the MCP feature entirely?): 5 module
  `api.py` (`conversations`, `llm_providers`, `mail_sync`, `team`, `conversation_insights`) still emit a
  UI connect-config pointing at `{root}/app_run_mcp.py` (now broken); `src/apps/mcp_*/server.py` docstrings
  + module `mcp/README.md` reference the old path. NOT rewired to `old/` on purpose.

**`app_migrate.py` → check/upgrade tool** (done):
- `AlembicRunner` gained dry-run inspection: `status(engine) -> MigrationStatus` (current heads vs target
  heads + ordered `pending: list[PendingRevision]`), built via `ScriptDirectory.iterate_revisions(heads,
  current_heads)` + `MigrationContext.get_current_heads()`. Split `_base_config()` (no connection, for
  ScriptDirectory) out of `_build_config(connection)`. `upgrade_head` unchanged (real apply). New exports
  `MigrationStatus`, `PendingRevision`.
- `app_migrate.py` now has subcommands: `check` (default, dry-run — prints heads + pending, **exit 1 on
  drift**, no DB change) and `upgrade` (apply to head, no-op if up-to-date). Unknown cmd → exit 2.
- `.run/tool-migrate.run.xml`: pass `upgrade` (preserves its apply intent now that bare = safe `check`).
- Docs synced: `docs/DEVELOPMENT.md` (3 spots) + `src/core/database/README.md`.
- Verified against dev DB: `check`/`upgrade` report up-to-date (exit 0), bad cmd exit 2, pending-ordering
  validated on a simulated fresh DB (63 revisions in apply order).

**RESOLVED DECISION — scheduler/tasks vs API process** (decided 2026-06-03; was parked "подумает завтра"):
How to separate background tasks from the request-serving flow once the API runs headless behind nginx
(possibly with `SERVER_WORKERS>1`). Infra already supports it: `Config.scheduler_enabled` (default True)
gates `scheduler.start`; the runner is **multi-instance safe** — `runner.py` takes a distributed DB lock
`task:<module>:<code>` via `core_locks` (`CoreLock.acquire`), so a task runs on only one instance even if
several tickers exist; plus partial-unique `(module, code) WHERE status='running'` + heartbeat zombie-cleanup.
The ticker currently starts inside `create_app` lifespan → every uvicorn worker spins its own.

Decisions confirmed with the user:
- **Worker shares the codebase** (same `semaphore-core` booted in worker mode), NOT a separate system. The
  task registry is built from module code (`entry.handler` is a Python fn registered via module `register`),
  so the worker must import the same modules to execute tasks. `new_structure/` is the deploy skeleton for
  the **API**, not the worker. → chosen layout = **A+**: dedicated `worker` container, one image, clean
  `app_worker.py` (no FastAPI); requires lifting task registration out of `create_app` into a shared bootstrap
  both the API and the worker call.
- **Manual-run signal API → worker = run-request row in the DB** (+ optional Postgres `LISTEN/NOTIFY` on top
  for immediacy). The one coupling point that breaks on split is `src/core/api.py:121`
  `asyncio.create_task(run_entry(entry))` — it runs the task IN the API process. After the split the API
  must instead persist a "run requested" record; the worker's ticker picks it up next tick. Persistent,
  multi-instance-safe, idempotent, zero new infra (DB-centric, matches the existing design). NOTIFY is a
  latency optimisation only — the run-request row is the source of truth (worker re-reads pending on boot,
  so a NOTIFY missed while the worker was down is not lost).
- Cron flow needs **no** cross-process signal: move the ticker into the worker, set `SCHEDULER_ENABLED=false`
  on the API. The worker checks schedules off the DB on its own.

Deploy: one image, two containers — `backend` (`app_api.py`, `SCHEDULER_ENABLED=false`, N uvicorn workers) +
`worker` (`app_worker.py`, `SCHEDULER_ENABLED=true`, 1 process). Migrations in any multi-process layout: run
once via `app_migrate.py upgrade` (entrypoint), API + worker with `DB_AUTO_MIGRATE=false`.

Full implementation plan: [`AGENTS/plans/2026-06-03-tasks-worker-split.md`](../plans/2026-06-03-tasks-worker-split.md).

**Phase 4 (partial) — `tools/storage_mount.sh`** (done): deploy-symlink wiring moved into a new
root `tools/` dir (was at boilerplate root). Profile-aware: `tools/storage_mount.sh (--dev|--prod|
--test)` selects which `runtime/<profile>` gets the instance links (`runtime/<profile>/storage ->
../../storage` + `runtime/<profile>/web -> ../../static`); requires exactly one flag (no default,
exit 2 on missing/unknown). The web-root link `static/storage/public -> ../../storage/public` is
ALWAYS (re)created + re-verified regardless of mode (`ln -sfn`, idempotent). `mkdir -p` guards the
`static/storage`, `storage/{public,protected}`, `runtime/<profile>` parents. All targets relative
to each link's location → survive copy. `ROOT=$(cd "$(dirname "$0")/.." && pwd)` (script now one
level down). Verified: no-arg/bad-arg → exit 2; `--prod` twice = idempotent; all 3 links resolve;
`git check-ignore` confirms the symlinks stay ignored (`/static/storage/public` + `/runtime/*`).
Still TODO in phase 4: `runtime/prod/{logs,cache,tmp,import}/.gitkeep`, `.env.example`,
docker-compose/nginx alignment.

**Phase 3 (partial) — Qt GUI teardown** (done): deleted `src/gui/` (5 files: `__init__`,
`gui_window`, `log_console`, `runtime`, `server`), `src/apps/app/gui.py` (`run_gui_app` Qt entry),
and `dev/app_run.py` (its only consumer). The GUI layer was fully self-contained — `GuiRuntime`/
`ServerThread`/`log_console`/`PySide6`/`qasync` lived only under those files; no other module
imported them (verified `grep` clean across `src/` post-delete). **Dev run rewired off Qt onto
`app_api.py`**: `app_api.py` now branches on `Config.is_dev` — dev → `uvicorn.run(reload=True,
reload_dirs=[src])` (replaces the old `DevServerProcess` subprocess `--reload`; `workers` ignored),
prod → `workers=server_workers`. The two IDE configs (`run-dev`/`watch-dev`) now point at
`$PROJECT_DIR$/app_api.py` (were the stale `$PROJECT_DIR$/app_run.py`). Browser is no longer
auto-opened — open Vite (`watch-web`) or the SPA manually. Docstring in `src/apps/app/server.py`
("web API + GUI…") and `AGENTS/docs/core-architecture.md` (gui.py / `gui/` tree lines) updated to
headless. Verified: `APP_PROFILE=dev python -c 'import app_api; from src.apps.app.server import app'`
→ 113 routes, no Qt; no `PySide6`/`qasync` imports remain in `src/`.

Still TODO in **phase 3**: Qt deps in `pyproject.toml` (`PySide6`, `qasync`, `pyinstaller` — now
unused, need `uv` re-lock), the `sys.frozen`/`_MEIPASS` branch in `app_path.py` + `config.py`
(PyInstaller prod root resolution), and the PyInstaller/`app_run.py` mentions in `docs/BUILD.md` +
`docs/DEVELOPMENT.md`. (Module `api.py` `sys.frozen` checks are the MCP-connect-config path — that's
the separate parked MCP-retire decision, not Qt.)

**SPA mount removed from backend** (done 2026-06-04): Phase 1 left `mount_spa` wired for the
local one-shot dev fallback, but it stayed gated only on `BACKEND_API_ENABLED` (not profile), so
`app_backend.py` would still serve a repo-root `static/` in prod — contradicting the API-only
contract in its own docstring. Per user decision: dropped serving SPA entirely. Deleted
`src/apps/app/web.py`; removed the `mount_spa` import + call from `src/apps/app/server.py` (docstring
now "web API, без раздачи SPA"). Backend is unconditionally API-only — статику раздаёт nginx (prod) /
Vite (dev). Docs synced: `core-architecture.md` (tree), `router.md` (BACKEND_API_ENABLED gate),
memory `project_architecture.md` + `project_overview.md`. Syntax-checked `server.py`.

## Result

Phase 1 files: `web/vite.config.ts`, `web/package.json`, `src/apps/app/web.py`, `.gitignore`,
`static/` (built SPA, 519 tracked files incl. `static/storage/.gitkeep`).
Entry-point step: `app_api.py` (new entry, now tracked), deleted `app_build.py` +
`.run/build-app.run.xml` + `.run/build-mcp.run.xml`, removed `assets/`, `.gitignore` cleanup.
Phases 2 (storage split / headless wiring), 3 (Qt teardown), 4 (deploy), 5 (docs) pending.
