# Database & migrations — working rules

**Read before touching DB models, tables, columns, or Alembic migrations.** Conventions that cannot
be derived from the code. Related: [migrations.md](migrations.md) (revision naming), [dates.md](dates.md)
(timestamp columns), [soft-delete.md](soft-delete.md) (logical deletion).

## Database provider — `postgres` (base) | `sqlite` (zero-install)

`DB_PROVIDER` (env, `src/core/config.py`) selects the relational backend. The relational seam is the
**general DB only** — the vector store will be a separate concern (its own module/provider).

- **postgres** (default, the base; pgvector target): `database_url` = `postgresql+asyncpg://…`,
  full pool + verify-full TLS via `db_connect_args`. Requires `DB_HOST/NAME/USER/PASSWORD` (a
  `model_validator` enforces this only for postgres). Schema = **Alembic** (`upgrade_head` at lifespan).
- **sqlite** (zero-install, no server, single file): `database_url` = `sqlite+aiosqlite:///<path>`
  (`DB_PATH`, default `<runtime_root>/app.sqlite3`); engine takes only a busy-`timeout`. Schema =
  **Alembic** (`upgrade_head` at lifespan / `migrate upgrade`) — portable types make migrations run on
  SQLite too. `create_all` is used **only for the in-memory test tier** (`config.sqlite_in_memory`,
  StaticPool, one run, no migration history). Schema changes ship as **new forward-only migrations**
  (extend the module's chain); applied migrations are not edited in place. Wiping/rebuilding the dev
  DB (drop the file + `migrate upgrade`, preserving `core_modules_settings` by backup/restore) is done
  **only on explicit user request**.
  Postgres connection fields are not required. Caveat: SQLite is **single-writer** (concurrent
  `--backend --worker` writes contend), and Postgres-only SQL (rich JSONB ops, partial indexes,
  `LISTEN/NOTIFY`) is unavailable — keep code on the common denominator.

Portability mechanics (already in place):
- **Types:** `database/types.py` — `timestamp()` / `json_value()` resolve to PG-native (`TIMESTAMP(0)`
  / `JSONB`) via `.with_variant()`, else generic (`DATETIME` / `JSON`). Use these in models.
- **Upserts:** each CRUD picks `dialects.{postgresql,sqlite}.insert` by `session.bind.dialect.name`
  (`_insert_for`) — both dialects support `on_conflict_*`.
- **Engine:** `config.engine_kwargs` returns the provider-appropriate pool/connect args;
  `runtime.create_all(engine)` builds the schema from `Base.metadata` for the **in-memory test tier only**.
- **Driver:** `aiosqlite` (dependency). `migrate` CLI runs on both backends (portable-typed migrations
  apply on SQLite as well as Postgres); each module with tables ships a `migrations_dir`.

## Table naming — explicit name dependency

A table that holds rows belonging to another table (1:N, M:N) must include the **full parent table
name** as a prefix, not the singular root.

- `my_module_things` (parent) → child `my_module_things_sessions` / `my_module_things_tokens`, **not** `my_module_sessions`.
- General form: `<parent_table_name>_<relation_plural>`. Don't drop the parent's plural marker.
- Same rule for index / constraint names: `ix_my_module_things_tokens_thing_id`,
  `uq_my_module_things_tokens_thing_name_live`.

**Why:** reading any child table name immediately tells you which parent it belongs to, with no
inference from a shortened root. Avoids ambiguity when multiple modules could own a `*_sessions`
table (e.g. `my_module_things_sessions` vs some other module's sessions).

**Applies to:** migrations, ORM `__tablename__`, index/constraint names.

## Timestamps — no microseconds (`precision=0`)

Project-wide DB timestamps use `postgresql.TIMESTAMP(precision=0)` — microseconds are dropped at
insert. `utc_now()` returns a naive UTC datetime **with** microseconds; once it round-trips through
the DB the subseconds are gone. Nothing in this project needs sub-second granularity, and the
convention is uniform across every table (full datetime contract in [dates.md](dates.md)).

- **Migrations:** always `postgresql.TIMESTAMP(precision=0)` (migrations are Postgres-only). **Models:**
  use the portable `timestamp()` helper from `database/types.py` (→ `TIMESTAMP(0)` on Postgres, `DATETIME`
  on SQLite); never bare `sa.TIMESTAMP()` or raw `postgresql.TIMESTAMP` in a model.
- **Tests:** when comparing "before vs after" timestamps, do NOT hold the in-memory value from the
  create call — it still has microseconds, while the DB-stored copy is truncated, so an immediate
  update can appear to go *backwards* by sub-second drift. Re-fetch the row from the DB first, then
  compare.

  ```python
  # WRONG — original.updated_at has microseconds, updated.updated_at is truncated
  original = await crud.create(...)
  updated = await crud.update_(...)
  assert updated.updated_at >= original.updated_at  # flaky

  # RIGHT — both values come from the DB, both truncated
  await crud.create(...)
  original = await crud.get(...)
  updated = await crud.update_(...)
  assert updated.updated_at >= original.updated_at
  ```

- Same applies anywhere a fresh `utc_now()` value is compared against a value that has been through
  the DB.

## DB connection TLS — secure-by-default, fail-closed

DB connection TLS is env-driven (`src/core/config.py`), **secure-by-default and fail-closed**.

- `DB_SSL: bool = True`, `DB_CERT: str | None = None`. A `model_validator(mode="after")` raises
  `ValueError("DB_CERT required when DB_SSL is enabled")` whenever `db_ssl and not db_cert`. There is
  **no `require`-without-verification fallback** — if SSL is on, the mode is strictly **verify-full**
  (`ssl.SSLContext` from the CA at `db_cert`, `check_hostname=True`, `verify_mode=CERT_REQUIRED`).
- `db_cert` relative paths resolve against `_app_root()` (project root) — same base as `_env_file()`.
- **Gotcha:** because the default is `True`, any environment without TLS **must** set `DB_SSL=false`
  explicitly, else `Config()` (and thus the whole app/tests) raises at construction. The local `.env`
  (profile `dev`) sets `DB_SSL=false`; the test suite reads that same root `.env`. New machines / CI
  cloning `.env.example` must flip it.
- **Why:** the server is self-hosted and self-configured, so verify-full with our own CA is achievable
  (we control the cert CN/SAN = `DB_HOST`); weaker modes would only add insecure footguns.

**Apply (remote prod):** set `DB_SSL=true` + `DB_CERT=<CA path>` and ensure the server cert's CN/SAN
equals `DB_HOST` (use a stable DNS name; an IP needs an `IP:` SAN). Pool/timeout knobs
(`DB_CONNECT_TIMEOUT`, `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE` / `DB_POOL_TIMEOUT`) live
in the same Database env block; the engine applies them in `src/core/database/runtime.py`. Plan:
[`AGENTS/plans/archive/2026-05-30-remote-database.md`](../../plans/archive/2026-05-30-remote-database.md).

### mTLS (mutual TLS) — supported

The remote server (`postgres:18`) uses `pg_hba` `hostssl … scram-sha-256 clientcert=verify-full` +
`hostnossl reject` — **mutual TLS**: the client must present a client cert signed by the CA whose **CN
equals the role name**, plus the scram password. `Config` carries `db_client_cert` / `db_client_key`
(env `DB_CLIENT_CERT` / `DB_CLIENT_KEY`); `db_connect_args` calls `ctx.load_cert_chain(...)` when both
are set (a validator enforces they come as a pair). The client cert is optional — without it the
context does server-only verify-full. A standalone validation kit (asyncpg + SQLAlchemy, positive + 3
negative cases) lives at the server-side repo `…/server_semaphore-dev/test/check_connection.py`.

**Prod cert layout:** `assets/prod/` (gitignored) holds the prod `.env` + `cert/` (root-ca.crt +
per-role client cert/key). `.env` cert paths are relative (`cert/root-ca.crt`) and resolve against
`_app_root()`.

## Migration naming

Migration files in `src/modules/<name>/migrations/versions/` (and `src/core/migrations/versions/`)
are named `<prefix><NN>_<slug>.py` — short module prefix (1–3 letters), zero-padded sequence,
snake_case slug. The `revision` string inside the file equals the filename basename; `down_revision`
chains to the previous migration in the same module. **Never** accept an Alembic autogen 12-char
revision ID — they hide ordering and are unreadable. Example for a hypothetical `my_module`:
`mm01_init.py`, `mm02_email_partial_unique.py`, ….

Full rules in [migrations.md](migrations.md); cross-module FK ordering in
[conventions/db-migrations](../conventions/db-migrations.md).
