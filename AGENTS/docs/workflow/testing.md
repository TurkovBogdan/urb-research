# Testing

Agent-facing guide: how to run the suite and which flags to pass. Full human reference (markers, examples, rationale): [`tests/README.md`](../../../tests/README.md).

## Parameters

Every test carries exactly one type marker. Type flags and area flags are orthogonal and compose freely.

- **Markers:** `pure` (no DB/network), `db` (needs a DB — in-memory SQLite), `heavy` (real Alembic migrations — Postgres-only), `live` (real external services + creds).
- **Default filter** (`pyproject.toml` → `addopts = -m 'not heavy and not live'`): runs `pure` + `db`. `heavy`/`live` are opt-in.
- **Type flags** (run only that group): `--pure`, `--db`, `--heavy`, `--live`; `--all` lifts the filter (everything, incl. heavy + live).
- **`--unmarked` — standard audit:** collects only tests carrying *no* type marker. Every test must have exactly one (`pure`/`db`/`heavy`/`live`); a non-empty result means those tests violate the standard and need a marker. Use it to find stray/untagged tests, not as a normal run.
- **Area flags** (which directories): `--core` (= `tests/core` + `tests/apps`), `--module=<name>[,<name>...]` (one or more modules, comma-separated or repeated). Can't be combined with an explicit test path.
- **Parallelism (`pytest-xdist`):** each worker is a separate process with its own in-memory SQLite, so isolation is free and unbounded. `-n` defaults to `auto` (cpu count); `-n0` = inprocess (use for `--pdb`).

## Workflow — default agent behaviour

1. **No DB setup, no `--dbs`.** Tests run on in-memory SQLite — no Postgres pool. `--dbs` is a deprecated no-op (kept so old commands don't error); never pass it.
2. **Inner loop = the working set:** run `--core` and the specific `--module=<name>` you touched. The default markers (`pure` + `db`, no `heavy`/`live`) keep it fast and cover the change. Do not run `heavy`/`live` or the whole tree while iterating.
3. **Full run only for final verification:** `uv run pytest --all` (all markers, all modules) right before declaring done / handing off. `heavy` migration tests are Postgres-only — without `TEST_PG_DSN` they self-skip (see below).

## Examples

> **Run via `uv run`** — the venv is not on `PATH`. A bare `pytest` fails with `No such file or directory`; prefix every command with `uv run` (or call `.venv/bin/pytest`).

```bash
# Inner loop — core (default markers: pure + db)
uv run pytest --core

# Inner loop — the module you changed (bare-core has no modules yet — generic example)
uv run pytest --module=<module>

# Final verification — everything (heavy skips without TEST_PG_DSN)
uv run pytest --all

# Audit — list tests missing a type marker (should be empty)
uv run pytest --unmarked

# Single-process for debugging
uv run pytest --module=<module> -n0 --pdb

# Heavy Alembic-migration tests against a real Postgres
TEST_PG_DSN=postgresql://user:pass@host:5432/dbname uv run pytest --core --heavy
```

## Test DB & fixtures

- `tests/conftest.py` forces `DB_PROVIDER=sqlite`, `DB_PATH=:memory:` **before importing `src`**, so any `Config()` in a test gets a fresh in-memory DB — dev/prod can't be touched.
- No autouse schema wipe: each `db` test (or the app lifespan) calls `init_database` → a brand-new `:memory:` engine, so the previous test's DB is gone automatically. Schema is built from the ORM models (`Base.metadata.create_all`); on SQLite the app lifespan does the same (Postgres → Alembic).
- An autouse `_dispose_engine_between_tests` closes any lingering module-level engine after each non-`pure` test.
- Live creds are optional: a module's `live/` tests read their own `LIVE_*` env vars; absent → those tests self-skip in their fixtures.

## Parallelism internals

Each xdist worker is a **separate OS process** with its own in-memory SQLite — `db` parallelizes like `pure`, no pool, no serial grouping.

- **`-n` defaulting** (`pytest_cmdline_main`, tryfirst, controller-only — guarded by `PYTEST_XDIST_WORKER`): `-n` not given → `-n auto`; explicit `-n N` / `-n0` honoured (`-n0` = inprocess, the escape hatch for `--pdb`).
- **In-memory mechanics:** `Config.sqlite_in_memory` (`DB_PROVIDER=sqlite` + `DB_PATH=:memory:`) makes `database_url` = `sqlite+aiosqlite://` and adds `poolclass=StaticPool` + `check_same_thread=False` to `engine_kwargs` — the single shared connection keeps the in-memory DB alive for all sessions of that engine.
- **Heavy = Postgres-only:** migrations use `postgresql.*` column types (JSONB/TIMESTAMP) that don't run on SQLite. `pytest_collection_modifyitems` skips every `heavy` test unless `TEST_PG_DSN` is set (which flips the run to `DB_PROVIDER=postgres`). **NB `--db` (marker) ≠ `--dbs` (deprecated no-op).**

## Live tests

- Layout: `tests/modules/<module>/live/` (HTTP to real services); regular unit tests stay at `tests/modules/<module>/test_*.py`.
- `tests/conftest.py` sets the in-memory `DB_*`; a module's live tests read their own `LIVE_*` creds from the environment. Without the keys the tests self-skip in their fixtures.
