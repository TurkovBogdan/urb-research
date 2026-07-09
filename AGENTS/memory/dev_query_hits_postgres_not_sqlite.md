---
name: dev_query_hits_postgres_not_sqlite
description: dev DB is the SQLite file runtime/dev/app.sqlite3 (DB_PROVIDER=sqlite); dev-query.sh now selects backend by DB_PROVIDER.
metadata:
  type: project
---

The real dev database is the **SQLite file** `runtime/dev/app.sqlite3` — `.env` has
`DB_PROVIDER=sqlite`, so the app (and lifespan `create_all`) uses it, NOT the
Postgres creds that also sit in `.env` (`DB_HOST/DB_NAME=core_semaphore_dev/...`,
a stale DB with old modules' tables).

`AGENTS/tools/dev-query.sh` → `dev_query.py` now **branches on `DB_PROVIDER`**
(fixed 2026-07-01): `sqlite` → opens `runtime/<APP_ENV>/app.sqlite3` (or `DB_PATH`)
via stdlib `sqlite3`; `postgres` → asyncpg. So the tool and the app agree again.
Before the fix it always hit Postgres and silently diverged — which once produced a
wrong conclusion ("web_search tables don't exist" — they did, in sqlite).

**Inspect dev data:** `bash AGENTS/tools/dev-query.sh "SELECT ..."` (auto-picks
sqlite) or directly `sqlite3 runtime/dev/app.sqlite3 "..."`. When something looks
empty/missing, check `DB_PROVIDER` in `.env` first. Related:
[[standalone_script_hits_dev_db]].
