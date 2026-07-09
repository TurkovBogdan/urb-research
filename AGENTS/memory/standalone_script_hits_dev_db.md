---
name: standalone_script_hits_dev_db
description: "CRITICAL — ad-hoc `uv run python`/asyncpg scripts hit the DEV DB; NEVER run destructive DDL (DROP SCHEMA/TABLE, TRUNCATE) outside pytest"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4d928d49-dbec-4c2b-b759-bb7caa3779ab
---

# ⚠️ CRITICAL — READ BEFORE ANY AD-HOC DB SCRIPT

**A plain `uv run python` script connects to the DEV database** — the real one with the
user's data. `Config().database_url` is built straight from `.env` (dev provider, currently
sqlite `runtime/dev/app.sqlite3`; postgres if `.env` says so). `APP_ENV=test` only changes
`runtime/<env>/` paths, **NOT the DB**. The redirect to a throwaway DB (now `DB_PROVIDER=sqlite`
+ `DB_PATH=:memory:`) exists ONLY inside `tests/conftest.py` (os.environ rewrite at import) and
runs ONLY under pytest. So any script using `Config()` outside pytest = DEV.

## HARD RULES (never violate)
- **NEVER** run `DROP SCHEMA` / `DROP TABLE` / `TRUNCATE` / `DELETE` from an ad-hoc
  `uv run python` or `asyncpg` script. Destructive DDL is irreversible.
- To touch a real Postgres DB: connect by **explicit literal name**, never via `Config()`,
  and **`assert current_database()`** before any write.
- To reproduce a `db`-fixture scenario: run it as a **real pytest** (gets the conftest
  in-memory-sqlite redirect) — do not hand-roll `Config()` + `create_all`/`DROP` in a heredoc.
- Test schema isolation is automatic: each `db` test builds a fresh `:memory:` engine via
  `init_database` — no manual schema reset is ever needed. See [feedback_migration_verify].
- Read-only checks against dev → use `AGENTS/tools/dev-query.sh` (SELECT only).

## What happened (2026-06-14) — the incident this rule exists for
While debugging flaky importer tests, a standalone repro script mimicking the `db` fixture
ran `DROP SCHEMA public CASCADE; CREATE SCHEMA public` against `Config().database_url`,
believing it targeted a test DB. It **wiped the entire DEV database** — all module data,
`alembic_version`, `core_modules_settings` (Gmail/Twenty API tokens), `core_users` — leaving
only the 12 tables the script's own `create_all` rebuilt (core + core_storage + intercom).
Recovery required a backup restore + `migrate upgrade` + full re-import.

**Cost:** destroyed the user's working dev environment. This is the most expensive kind of
mistake — guard against it every single time before running anything that writes to a DB.
