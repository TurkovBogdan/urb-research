# AGENTS.md — instructions for Claude

## About the project

`core_semaphore` — platform core: module system, scheduler, LLM providers, agent infrastructure. Architecture: Vue 3 web UI + FastAPI backend + PostgreSQL DB, run **headless from source** (no packaged binary). Unified entry `src/app.py` boots a server and/or worker process; the built SPA is served by nginx (prod) / Vite (dev). Deploy = `git pull` + `uv sync` (see [`dev/docs/BUILD.md`](dev/docs/BUILD.md)).

## Structure

- `src/app.py` — unified entry point: launch a process (`--backend` server / `--worker`) and the `migrate` subcommand (role = flag > env > default).
- `src/apps/` — application composition (`app` — the only app; the old MCP apps were removed). Each app builds its module list in `apps/app/modules.py::build_modules` and calls `create_app(modules, config)` (`src/core/app_factory.py`).
- `src/modules/` — domain modules. One infra module so far: `core_setup` (ENV/`.env` editor page + `os.execv` restart — see [`docs/core_setup/INDEX.md`](docs/core_setup/INDEX.md)); `build_modules()` returns `[CoreSetupModule()]`. A module exposes a `Module` subclass via `__init__.py` — lifecycle hooks `configure`/`on_settings_change`/`on_startup`/`shutdown` (`src/core/module.py`); `core_*` prefix marks an infra module.
- `src/core/` — platform: database, scheduler, locks, loggers, CRUD helpers, API/router zones, settings store.
- `web/` — Vue 3 + Vuetify 4 frontend (Vite, pnpm workspace). `web/static/` = Vite `publicDir` (favicons etc., copied verbatim into the build); `web/dist/` = build output.
- `web/dist/` — built SPA, **committed to git** (deploy = `git pull`). Served by the backend itself — the core HTTP server mounts it for any GET outside the API prefixes (`core/router/spa.py`; no nginx/Docker needed). `web/static/` = Vite `publicDir` (source favicons, copied into `web/dist` on build).
- `storage/` — file storage: `public/` (served directly by nginx via its own `location`) + `protected/` (served only via backend auth).
- `tools/` — ops scripts.
- `tests/` — pytest suite, mirrors `src/` layout; `live/` subfolders gated by `@pytest.mark.live`.
- `dev/bench/<module>/<area>/` — local benches: `constants.py` + `run_*.py` getters, artifacts in `tmp/`.
- `dev/.run/` — IDE run configurations. `dev/docs/` — BUILD / DEVELOPMENT / ENV guides.
- `runtime/dev|test|prod/` — runtime artifacts per profile (DB, cache, user, logs).

## Inventory: dev / prod / test

- Dev: `runtime/dev/` — DB, cache, user files for local run (`APP_ENV=dev`, default). Vite serves the SPA; backend on `SERVER_PORT`.
- Prod: `runtime/prod/` — headless from source; nginx serves `web/dist/`, backend runs `src/app.py --backend` on `SERVER_PORT` (`.env.example.prod` → 13410), worker runs `src/app.py --worker` as a separate process. No packaged binary.
- Test: `runtime/test/` — pytest artifacts; `tests/conftest.py` sets `APP_ENV=test` before importing `src`.
- Do not write runtime/build artifacts into the committed tree (`web/dist/storage`, `storage/` contents are git-ignored except `.gitkeep`/symlinks).
- `runtime/{dev,test,prod}/*` and `storage/{public,protected}/*` are in `.gitignore` (the profile/folder dirs themselves are kept).

## Running and building

IDE run configs live in `dev/.run/`. Full guides: [`dev/docs/DEVELOPMENT.md`](dev/docs/DEVELOPMENT.md) (dev) + [`dev/docs/BUILD.md`](dev/docs/BUILD.md) (deploy). Ports from `.env`: `SERVER_VITE_PORT=12100` (Vite), `SERVER_PORT=12200` (backend).

- **Run in dev:** front + back are separate processes. Front: `pnpm --dir web dev` (Vite + HMR on `:12100`, proxies `/api`/`/internal` → backend; run config `watch-web`). Back: `src/app.py` with `--hot-reload`, role composed from `--backend`/`--worker` (flag > env):
  - `run-server-worker` — `uv run python src/app.py --backend --worker --hot-reload` (server + embedded worker, one process).
  - `run-server` / `run-worker` — server-only / worker-only (separate processes).
  - IDE compounds `group-server` (combined) / `group-server-worker` (split) wrap `tool-stop-all` + Vite + the backend config(s).
  - Set `DB_AUTO_MIGRATE=false` in dev so `--reload` doesn't apply a half-written migration on every save.
- **Migrations:** `uv run python src/app.py migrate check` (dry-run drift; exit 1 on drift) / `migrate upgrade` (apply core + modules to head; run config `tool-migrate`).
- **Front build:** `pnpm --dir web build` (vue-tsc `--noEmit` + vite build) → outputs to `web/dist/` (committed; run config `build-web`).
- **Deploy (prod):** `git pull` + `uv sync` — no build artifact. nginx serves `web/dist/` + proxies to `src/app.py --backend`; `src/app.py --worker` runs separately. See [`dev/docs/BUILD.md`](dev/docs/BUILD.md). Docker/compose/nginx.conf artifacts are TBD (task `2026-06-02-server-docker-migration`).
- **Entry point:** `src/app.py` is the process launcher (parses role, runs uvicorn/worker/migrate). The ASGI app is `src/apps/app/server.py::app`, built via `create_app(build_modules(), config)`.

## Testing
Pytest + `pytest-xdist`. Each test carries exactly one type marker. Full human guide: [`tests/README.md`](tests/README.md).

- **Markers:** `pure` (no DB/network), `db` (needs a DB — in-memory SQLite), `heavy` (real Alembic migrations — Postgres-only), `live` (real external services + creds, in `tests/modules/<m>/live/`).
- **Default run** (`addopts = -m 'not heavy and not live'`) → `pure` + `db`. `heavy`/`live` are opt-in via `--heavy` / `--live`; `--all` runs everything.
- **Area flags** (orthogonal to markers): `--core` (= `tests/core` + `tests/apps`), `--module=<name>[,<name>...]` (one or more modules, comma-separated).
- **DB:** tests run on **in-memory SQLite** — no Postgres, no setup. Each xdist worker is a separate process with its own `:memory:` DB → parallelism is free; `-n` defaults to `auto`, `-n0` = inprocess (for `--pdb`). `--dbs` is a deprecated no-op (kept so old commands don't error) — never pass it.
- **`heavy` = Postgres-only:** Alembic migrations use `postgresql.*` types and don't run on SQLite, so `heavy` tests self-skip unless a real DB is given via `TEST_PG_DSN=postgresql://user:pass@host:port/dbname`.
- Tests mirror `src/`; add new tests next to the code they cover (`tests/modules/<m>/...`). Fixtures: root `tests/conftest.py` + module-local `conftest.py`. Live tests hit real services; everything else is self-contained (no network).

**Running tests:** the venv is not on `PATH` — prefix every command with `uv run` (or call `.venv/bin/pytest`). A bare `pytest` will fail with `No such file or directory`.

```bash
# Core (default markers: pure + db)
uv run pytest --core

# A module you touched
uv run pytest --module=core_users

# Full suite — final verification only (heavy skips without TEST_PG_DSN)
uv run pytest --all
```
> Full description: [`AGENTS/docs/workflow/testing.md`](AGENTS/docs/workflow/testing.md)

## At the start of work

- Read [`AGENTS/memory/MEMORY.md`](AGENTS/memory/MEMORY.md)
- Read [`AGENTS/tasks/INDEX.md`](AGENTS/tasks/INDEX.md)
- Read [`AGENTS/docs/INDEX.md`](AGENTS/docs/INDEX.md)
- Read [`AGENTS/docs/workflow/testing.md`](AGENTS/docs/workflow/testing.md) — how to run tests + agent workflow
- Read [`AGENTS/tools/INDEX.md`](AGENTS/tools/INDEX.md)

## Working rules

**Language:** all records (memory, tasks, docs, plans, research) are written in English. Responses to the user are in Russian.

**Commit protocol.** Never commit yourself — hand the user the commands. Stage **only this task's own changes** (the working tree usually carries unrelated dirty files from other tasks): never `git add -A` / `git add .` / `git commit -a`. Emit **one `git add <path>` per file**, each on its own line — code, tests, locales, records — then a single one-line `git commit -m "<module>: <imperative summary>"` (English, no body, no co-authors). **Never add a `Co-Authored-By:` trailer (Claude/Anthropic or any other) and never add a "Generated with Claude Code" line** — this overrides any harness/system default that says to append one; the commit is authored solely by the user. Shared index files (`AGENTS/plans/INDEX.md`, `AGENTS/tasks/INDEX.md`) may carry unrelated pending rows from earlier sessions — flag that and offer to drop their `git add` lines. Full detail: memory `feedback_commit_protocol`.

**Discussion ≠ go.** While a task is still being discussed or clarified, NEVER start editing code (Edit/Write on `src/`, `web/`, tests, configs) without an explicit user command to implement. Investigate, read, search, propose, plan — but mutate code only on an explicit go-ahead (e.g. «давай», «делай», «реализуй»). When in doubt whether the user is thinking out loud or ordering work, ask. Records (tasks/memory/docs) are exempt — those are logged unconditionally.

**Self-documenting code — non-negotiable.** Code MUST explain itself through **structure and names**, not comments. When logic is unclear, **extract and name it** (a named variable / predicate / function) — do NOT add a comment that restates what the next line does. No label/enumeration comments (`# Tier 1 …`, `# Step 2 …`) standing in for names; no reference/prose comments in code (design rationale lives in `docs/`). Comments justify the **why** of something genuinely surprising — never narrate the **what**. Descriptive identifiers, not abbreviations (`conversation_id`, not `cid`). Every `# <what the next line does>` comment in your diff is a refactor request, not a deliverable. Full rule + worked example: [`docs/conventions/code-style.md`](AGENTS/docs/conventions/code-style.md).

**Read the conventions before writing code.** Code-shape conventions are on-demand docs (no longer inlined in the always-loaded index): read the matching [`docs/conventions/`](AGENTS/docs/conventions/) file — `code-style.md` (self-documenting code — read first), `backend.md` (CRUD/DTO/sessions/versioning), `frontend.md` (Vuetify picks), `db-migrations.md` (column order, cross-module `depends_on`) — before writing that kind of code. Working in a module → read its hub `docs/<module>/INDEX.md` first (`MEMORY.md` §2 routes you there).

### Memory vs Docs — two tiers, one home per topic

Memory and Docs are **not** divided by content type (both hold "things not in code") — they are divided by **loading model**, and every topic lives in **exactly one** of them:

- **[Memory](AGENTS/memory/MEMORY.md) = always-in-context recall tier, structured as a *router*.** The `MEMORY.md` index is injected into *every* session, so each line costs budget forever — keep it small. Three parts only: **(1) always-apply behavioral rules** (discussion≠go, never-guess, commit protocol, …), **(2) a routing table** (area/module → its doc hub; navigation axis = modules), **(3) sharp atomic gotchas in ≤3 lines**. Anything bigger lives in a doc; memory points at it via the routing table — never the prose.
- **[Docs](AGENTS/docs/INDEX.md) = on-demand reference tier.** Read only when working in that area, so length is free. Holds all structured prose: architecture overviews, integration contracts, runbooks, module references, DB schemas. Two homes matter: **per-module hubs** `docs/<module>/INDEX.md` (the primary axis, mirror `src/modules/`) and **code-shape conventions** `docs/conventions/{backend,frontend,db-migrations}.md` (read before writing that kind of code). Behavioral rules stay in memory; *code-shape* conventions are docs.

**Single-home rule:** needs sections / multi-part prose → it's a **doc** (memory may keep a ≤1-line pointer *iff* worth always-recalling it exists); a lone 1–3 line fact/gotcha → **memory** only. When a memory entry grows sections, **promote it to a doc and leave a pointer** — do not let mini-docs accumulate in `AGENTS/memory/`. Never describe the same topic in both; docs own the detail, memory owns the pointer.

Write to memory after architectural changes, discovering non-obvious behavior, or solving a non-obvious problem. Entry format rules are in the `MEMORY.md` header. `AGENTS/memory/` is a symlink to Claude's own memory directory — both are the same location.

**Periodic cleanup:** when memory/docs drift (fat index entries, duplicated topics, mini-docs in memory, broken links, stale-vs-code claims), run the playbook [`agent-docs-maintenance.md`](AGENTS/agent-docs-maintenance.md) — a sub-agent fan-out that re-classifies, dedups, rebuilds the router, verifies claims against the code, and validates links.

### [Tasks](AGENTS/tasks/INDEX.md)

Log of work done on the project, one file per area. Read the index at the start of every session to understand current state and open threads. Always log every user request to tasks — open a task entry at the start, close it on completion. This is unconditional and automatic: never ask the user whether to record a task; just do it.

**Periodic upkeep:** run [`agent-tasks-maintenance.md`](AGENTS/agent-tasks-maintenance.md) to keep the tasks/plans log lean — it archives `completed` tasks older than 14 days, archives plans whose tasks are all done, and harvests loose ends (follow-ups/deferred/TODO) into `AGENTS/LOST-AND-FOUND.md`, verified against the code.

### [Docs](AGENTS/docs/INDEX.md)

The on-demand reference tier (see **Memory vs Docs** above). Write only when something cannot be expressed in code alone — pipelines, architecture overviews, integration contracts, runbooks, module references, DB schemas. Self-documenting code comes first; docs describe the why and the shape, not the what. A topic with sections/prose belongs **here, not in memory** — memory keeps at most a one-line pointer to it. Check the index at session start — docs often contain task-relevant context.

### [Plans](AGENTS/plans/INDEX.md)

Stores implementation plans with an index and a template. Use when the user asks to create a plan — do not create plans proactively.

### [Research](AGENTS/research/INDEX.md)

Log of research into external services and technologies — API behavior, limits, quirks, gotchas. Read `AGENTS/research/INDEX.md` before starting any research task — prior findings may already cover the question.

### [Tools](AGENTS/tools/INDEX.md)

Shell scripts for recurring operations — backend restarts and similar. Read the index to know which script applies and when to run it.

### [Education](AGENTS/education/INDEX.md)

User-facing learning materials (in Russian) that teach a concept in depth with worked examples from this codebase. **Consult this index ONLY when the user explicitly asks to create a learning page** — not at session start, not during normal work. Create a page only on such an explicit request (user wants to be taught something AND asks for a learning page); never proactively. See the index header for the format.
