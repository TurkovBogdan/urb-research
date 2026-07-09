---
title: Remote PostgreSQL migration — connection hardening
date: 2026-05-30
status: completed  # in-work | completed | deferred
description: "Make the DB connection layer ready for a remote (self-hosted) Postgres: env-driven TLS (strict verify-full), connection/pool timeouts, explicit pool sizing. Plain env-backed Config; no behaviour change when DB_SSL=false."
tags: [core, database, deployment]
---

## Goal

The DB connection layer works against a remote, self-hosted PostgreSQL over TLS:
- TLS is an env toggle (`DB_SSL`); when on, the mode is strictly **verify-full** using a project-local CA file (`DB_CERT`).
- Connection establishment and pool checkout have explicit timeouts (no indefinite hangs on network faults).
- Pool size / overflow / recycle are explicit (no blind SQLAlchemy defaults), tuned so idle connections are recycled below the server's idle timeout.
- Local dev (`DB_SSL=false`) behaves exactly as today.

## Context

Currently the app talks to a **local** Postgres configured purely via env (`db_host`, …) — there is no embedded/managed Postgres in code (no `pg_ctl`/`initdb`). The engine (`src/core/database/runtime.py:52`) is created with only `pool_pre_ping=True`; no SSL, no timeouts, no pool sizing. `database_url` (`src/core/config.py:69`) builds a plain `postgresql+asyncpg://…` URL with no `sslmode`.

Risks specific to a remote DB (full analysis in chat / this plan's Risks section): passwords + data in cleartext without TLS; indefinite hangs without `connect_timeout`; periodic "connection closed" errors when a firewall/Postgres kills idle connections without `pool_recycle`; scheduler/lock latency sensitivity.

Server is **self-hosted, configured by us** — so verify-full with our own CA is achievable (we control the cert's CN/SAN) and is the chosen baseline.

User decisions:
- TLS as a bool env (`DB_SSL`, default `true`) + `DB_CERT` path; not a string sslmode enum.
- When SSL is on, mode is **fixed to verify-full** (no `require`-without-verification fallback) — `DB_CERT` required, else raise on start (strict-normalization style, see `feedback_strict_normalization`).
- Full set of pool/timeout fields, not a minimal subset.

## Scope

**In scope:**
- New `Config` fields + validator + `db_connect_args` builder (`src/core/config.py`).
- Apply pool/timeout/connect_args in `create_async_engine` (`src/core/database/runtime.py`).
- `.env.example` Database block.
- Verify `app_migrate.py` builds its engine through the same path (inherits TLS/timeouts).
- Verify lock TTL / scheduler heartbeat are sane vs network RTT (decision only; change values only if clearly needed).

**Out of scope:**
- Server-side Postgres setup (postgresql.conf / pg_hba / TLS certs / firewall / backups) — documented as a runbook, not code.
- DB-probe in `/api/health` — deferred (changes health semantics); revisit separately.
- Disabling `auto_migrate` on prod — runbook guidance, not a default change.
- Multi-instance / connection-pooler (PgBouncer) topology.

## Approach

Keep `database_url` unchanged (user/pass/host/port/db only). Pass SSL + timeouts via asyncpg `connect_args`, and pool sizing via `create_async_engine` kwargs — cleaner and type-safe vs stuffing query params into the URL. Migrations reuse the app engine (`AlembicRunner.upgrade_head` runs `run_sync` on the same `AsyncEngine`), so they inherit TLS/timeouts automatically; only the standalone `app_migrate.py` needs a sanity check.

Alternative rejected: encode `sslmode`/params as URL query string — works but spreads connection config across a string blob, weaker validation, and asyncpg's URL `ssl=` handling is more limited than passing a prepared `ssl.SSLContext`.

TLS as a fixed verify-full (not a free-form sslmode enum) chosen because the server is ours: we can guarantee a correct CN/SAN, so the only safe-and-achievable mode is verify-full; offering `require`/`verify-ca` would only add insecure footguns.

## Steps

1. `Config`: add fields `db_ssl: bool = True`, `db_cert: str | None = None`, `db_connect_timeout: int = 10`, `db_pool_size: int = 10`, `db_max_overflow: int = 5`, `db_pool_recycle: int = 1800`, `db_pool_timeout: int = 30`. — `src/core/config.py`
2. `Config`: add validator — `db_ssl and not db_cert` → `ValueError("DB_CERT required when DB_SSL is enabled")`. — `src/core/config.py`
3. `Config`: add `db_connect_args` property — `{"timeout": db_connect_timeout}` plus, when `db_ssl`, `{"ssl": <SSLContext from db_cert, check_hostname=True>}`. CA path resolved against the app root (same base as `_env_file()`: project root, or the binary dir when frozen). — `src/core/config.py`
4. Engine: pass `pool_size`, `max_overflow`, `pool_recycle`, `pool_timeout`, `connect_args=config.db_connect_args` into `create_async_engine` (keep `pool_pre_ping=True`). — `src/core/database/runtime.py`
5. `.env.example`: extend Database block with the new keys + comment (`DB_SSL=false` for local dev). — `.env.example`
6. Verify `app_migrate.py` constructs its engine via the shared path (so it gets TLS/timeouts); align if it builds a bare engine. — `app_migrate.py`
7. Check lock TTL + scheduler heartbeat (`src/core/locks/`, `src/core/scheduler/`) cover worst-case RTT; record decision. — read-only unless a change is clearly warranted.

## Tests

- Unit: `db_connect_args` with `db_ssl=False` → no `ssl` key, has `timeout`. — covers dev path.
- Unit: `db_ssl=True` + valid `db_cert` → `ssl` is an `SSLContext` with `check_hostname=True` and `verify_mode=CERT_REQUIRED`. — covers verify-full.
- Unit: `db_ssl=True` + missing `db_cert` → `ValueError` (validator). — covers the strict fail-fast.
- Unit: `db_cert` relative path resolves against app root. — covers path resolution.
- Regression: existing config/DB tests pass unchanged with defaults (test profile sets its own `.env`). — `uv run pytest --core`.

## Validation

- `uv run pytest --core` green.
- Manual against the real remote: `psql "host=… sslmode=verify-full sslrootcert=… user=…"` connects.
- App boots with `DB_SSL=true` + CA against remote; scheduler ticks without latency-driven errors; one background task acquires/releases its lock cleanly.
- `app_migrate.py` runs against the remote over TLS.

## Risks / open questions

- Risk: cert CN/SAN must equal `DB_HOST` or verify-full fails — mitigation: documented in server runbook (use a stable DNS name; if connecting by IP, SAN must include `IP:<addr>`).
- Risk: CA file must ship with the frozen binary — mitigation: ensure `DB_CERT` resolution + `app_build.py` packaging cover it (note in runbook; not auto-bundled).
- Risk: `pool_recycle` must stay below the server's idle timeout / `tcp_keepalives` — mitigation: set server-side timeouts and `DB_POOL_RECYCLE` consistently in the runbook.
- Open question: exact current lock TTL / heartbeat values vs target RTT — answered in step 7 during implementation.

## References

- Related tasks: `AGENTS/tasks/2026-05-30-remote-database.md`
- Memory: `AGENTS/memory/project_architecture.md`, `feedback_strict_normalization.md`, `feedback_no_single_use_vars.md`
- Code: `src/core/config.py`, `src/core/database/runtime.py`, `src/core/database/migrations.py`, `app_migrate.py`
