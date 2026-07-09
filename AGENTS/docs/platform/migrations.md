# Migrations

Naming and authoring rules for Alembic revisions inside `src/modules/<name>/migrations/versions/` (and `src/core/migrations/versions/`).

## Filename format

```
<prefix><NN>_<slug>.py
```

- `<prefix>` — short module abbreviation, 1–3 lowercase letters. One stable prefix per module. In bare-core only the **core** chain exists (its own scheme, see below); module prefixes (`mm`, …) appear once domain modules land.
- `<NN>` — zero-padded sequence number within the module, starting at `01`. Three digits once you cross 99.
- `<slug>` — short snake_case description of what the migration does. Verb-first when it's a change (`add_synced_at`, `drop_thread_admin`, `rename_thread_message_timestamps`), noun-only for the initial table (`admins`, `contacts`).

Good (`mm` = a hypothetical `my_module`):

```
mm01_init.py
mm02_email_partial_unique.py
mm03_add_group.py
mm04_tokens.py
mm05_add_last_login_at.py
```

Bad — do not generate or accept names like these:

```
m0y0m0o0d0u0l0e13a0dd0_email_unique.py        # autogen ID interspersed with module letters
m0y0m0o0d0u0l0e0_init_things.py               # zero-padded letters, no ordering signal
m0y0m0o0d0u3l0e0_add_group.py                 # unreadable, position in chain not visible
```

The Alembic-style 12-char random revision ID is unreadable and hides the order of migrations. Always use the `<prefix><NN>_<slug>` form.

### Legacy chains (do not rename)

Some retired modules' legacy revisions now live as no-op tombstones in the core chain — leave them
as-is (renaming a `revision` breaks `down_revision` links and applied-history):

- `team` — module retired 2026-06-10; its two legacy revisions (`t1e0a0m0_init_team`, `t2e0a0m0_rename_team_contacts`) now live as no-op tombstones in `src/core/migrations/versions/`, collapsed into the core chain by merge revision `c0re00010004`.

New migrations in **any** module must use `<prefix><NN>_<slug>`; only the historical tombstone
files stay untouched.

The **core** chain (`src/core/migrations/versions/`) uses its own date-based scheme
(`YYYYMMDD_NNNN_<slug>.py`, e.g. `20260504_0001_init_core_tasks_locks.py`) — separate from the
module `<prefix><NN>` convention.

## Revision ID

The `revision` string inside the file must equal the filename basename without `.py`. `down_revision` points at the previous migration in the same module's chain (or `None` for the first one).

```python
revision: str = "mm02_email_partial_unique"
down_revision: Union[str, None] = "mm01_init"
```

This makes the chain trivially auditable: `ls versions/` already shows order, and grep on a revision ID lands in exactly one file.

## File header

```python
"""<module>: <short summary>

Revision ID: <prefix><NN>_<slug>
Revises: <previous revision or empty>
Create Date: YYYY-MM-DD
"""
```

Keep the docstring one line of summary — the slug already names the change.

## Per-module chain

Each module owns its own `versions/` directory and its own linear chain. Modules do not share revision IDs and do not cross-reference each other's `down_revision`. The merged graph is assembled at runtime by `AlembicRunner` from `version_locations`.

When adding a migration:

1. Pick the next `NN` after the highest existing one in that module.
2. Set `down_revision` to the previous revision ID in the same module.
3. Match the `revision` field to the filename.

## Schema changes = new forward-only migrations

Every schema change — even on a module still under active design — is its own **new forward-only
migration** with a fresh `NN` (`add_*`, `drop_*`, `rename_*`). Do **not** edit an already-applied
migration in place, and do **not** squash/rebuild the chain by default. Wiping and rebuilding the dev
DB (drop the file + `migrate upgrade`) is done **only on explicit user request** — see the rebuild
steps in [database.md](database.md) (stop backend first → back up `core_modules_settings` → drop →
`migrate upgrade` → restore).

## `AlembicRunner.status` — pending computation (new-root gotcha)

`status()` computes pending as **«ancestors of target heads minus applied»** — NOT the old
`iterate_revisions(heads, current)`, which only yielded **descendants** of `current`. The old form
dropped a module's first migration (`down_revision=None`) when it was added to an
already-populated DB → false `up_to_date`. This bit `app.py migrate upgrade` (gated on
`status.up_to_date` → skipped the new root); dev was safe (lifespan calls `upgrade_head` directly,
no status gate; tests use a fresh DB). Fixed 2026-06-04 when a module's first migration was added;
regression test in `tests/core/test_migrations.py`.

> A heavy migration test that reads any module's build-time config seed should override the relevant
> env var with `monkeypatch.setenv(..., "")` (NOT `delenv`) — the migration reads `<Module>Config()`
> from the `.env` FILE; an env-var override beats `env_file`, but `delenv` doesn't.

## Reference

- `src/core/migrations/versions/` — the core chain (date-based scheme); a future module's
  `versions/` would be the canonical `<prefix><NN>` example.
- `src/core/database/README.md` — how revisions are discovered and applied (`AlembicRunner`, `version_locations`).
- `dates.md` — always `postgresql.TIMESTAMP(precision=0)` in migrations, never `sa.TIMESTAMP()`.
- `soft-delete.md` — adding `deleted_at` in a migration.
