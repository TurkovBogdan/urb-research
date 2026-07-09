# tools

Run: `bash AGENTS/tools/<script>.sh` from the project root.

Ports are read from `.env`: `SERVER_PORT=12200` (backend), `SERVER_VITE_PORT=12100` (Vite).

## Backend

The dev backend (`run-server-worker` / `run-server` → `app.py --hot-reload`) runs uvicorn with `--reload` (`SERVER_HOT_RELOAD=true`) — Python source changes are picked up automatically. A standalone `run-worker` reloads too (via `watchfiles`). **Do not restart for ordinary code edits.**

| Script | Trigger |
|--------|---------|
| [restart-backend.sh](restart-backend.sh) | **Migrations only** — a new Alembic migration was added or the DB schema changed. Kills `:12200`, restarts uvicorn on `src.apps.app.server:app`. Log → `/tmp/hh-server.log`. Vite is unaffected. Do NOT run for regular Python edits — live-reload handles those; running it creates a second server instance alongside the IDE one. |

## Frontend (Vite)

Managed by IDE `watch-web` run config (`pnpm dev`, HMR on `SERVER_VITE_PORT=12100`). Vue/TS changes apply automatically — no action needed.

## Cleanup

| Script | Trigger |
|--------|---------|
| [stop-all.sh](stop-all.sh) | Zombie processes after IDE/app close. Kills `:12200` (backend), `:12100` (Vite), `:13410` (release), `app.py`. TERM then KILL. |

## Database

Ad-hoc SQL против **dev**-базы. Бэкенд выбирается по `DB_PROVIDER` из `.env` — как в приложении: `sqlite` (dev по умолчанию) идёт в файл `runtime/<APP_ENV>/app.sqlite3` (либо `DB_PATH`) через stdlib `sqlite3`, `postgres` — в `DB_*` креды через `uv run` + `asyncpg`. `psql` в системе нет.

| Script | Trigger |
|--------|---------|
| [dev-query.sh](dev-query.sh) | Нужно быстро посмотреть/посчитать данные в dev-базе без поднятия приложения. Запрос — аргументом или из stdin: `bash AGENTS/tools/dev-query.sh "SELECT count(*) FROM web_search_page"` либо `echo "..." \| bash AGENTS/tools/dev-query.sh`. `SELECT`/`WITH`/`SHOW`/`EXPLAIN`/`TABLE`/`PRAGMA` печатаются таблицей (длинные ячейки обрезаются до 80 симв.), прочее (DDL/DML) — статусом команды. Только dev; ограничений на запись нет — ответственность на вызывающем. |
