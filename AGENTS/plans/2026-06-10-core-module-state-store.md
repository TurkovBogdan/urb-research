---
title: Core module state store (arbitrary per-module KV)
date: 2026-06-10
status: completed  # in-work | completed | deferred
description: "Core-provided generic per-module key/value store for arbitrary runtime state (import cursors, counters, run markers) — a new `core_modules_state` table + CRUD + a module-bound accessor, distinct from the user-facing settings store."
tags: [core, database, module-system]
---

## Goal

The core exposes a **generic state store** any module can use to persist arbitrary
runtime data without inventing its own table. A task that needs to remember "where
the import stopped" calls a single bound accessor:

```python
store = module_store("mail_sync")          # or self.store inside a Module
await store.set("gmail_import_cursor", {"history_id": "98213", "synced_at": "..."})
state = await store.get("gmail_import_cursor")   # -> dict | None
```

Finished state: a `core_modules_state` table keyed by `(module, key)` with a JSONB
`value`, a CRUD layer mirroring `crud/module_settings.py`, and a thin
`ModuleStore` accessor (plus a `Module.store` convenience property).

## Context

Today a module that needs to persist transient state has **no home for it**. The
only adjacent thing is `core_modules_settings` (`src/core/models/module_settings.py`
+ `src/core/crud/module_settings.py`): PK `(module, key)`, `value` Text, with a full
**settings** stack on top — registry, schema, bootstrap, API, UI
(`src/core/_settings/*`). That table is **user-facing configuration**: values are
typed via a schema and surfaced/edited in the settings UI. It is the wrong place for
internal machine state (import cursors, counters, last-run markers, dedup
checkpoints) — those are not user-tunable, have no schema, and would pollute the
settings surface.

The shapes are deliberately near-identical so the two stay easy to reason about, but
they are **two homes for two concerns**:

| | `core_modules_settings` | `core_modules_state` (new) |
|---|---|---|
| Purpose | user-tunable config | internal runtime state |
| value | `Text` (typed by schema) | `JSONB` (arbitrary structure) |
| Surfaced in UI | yes (settings page) | no |
| Schema/registry | yes (`_settings/*`) | none |
| Written by | operator via API | module code |

Concrete first consumer: `mail_sync` Gmail-API import needs a `history_id` cursor
(see task `2026-06-10-mail-sync-gmail-api-import.md`, which currently proposes a
bespoke column). This store removes the need for per-feature state columns.

Reference files:
- Mirror target: `src/core/models/module_settings.py`, `src/core/crud/module_settings.py`
- Migration pattern: `src/core/migrations/versions/20260512_0001_init_core_modules_settings.py`
- Module contract (`name` = module code, integration point): `src/core/module.py`
- DB session/CRUD conventions: `src/core/database/README.md`, `AGENTS/docs/conventions/backend.md`

## Scope

**In scope:**
- New table `core_modules_state` (`module`, `key`, `value` JSONB, `created_at`, `updated_at`).
- ORM model `CoreModuleState` + registration in `src/core/models/__init__.py`.
- CRUD `src/core/crud/module_state.py` (dialect-aware upsert, mirrors settings).
- A bound accessor `ModuleStore` + factory `module_store(code)` and a
  `Module.store` convenience property.
- Core migration creating the table.
- Tests (db) for CRUD + accessor round-trips; (heavy) migration up/down.
- Short platform doc + memory routing entry.

**Out of scope:**
- Wiring `mail_sync` (or any module) onto the store — that lands with its own task.
- Any HTTP/API surface or UI for the store (it is internal; not user-facing).
- TTL/expiry, history/versioning, optimistic-locking columns — add only if a real
  consumer needs them.
- Touching `core_modules_settings` or the `_settings/*` stack.

## Approach

Clone the `module_settings` model + CRUD shape into a sibling `module_state`, with
two deliberate differences: (1) `value` is **JSONB** (the data is structured state,
not a typed-by-schema string — storing dicts natively avoids manual `json.dumps`
round-trips at every call site and keeps the door open to field-level queries/index);
(2) **no settings stack** — this is internal, so there is no registry/schema/API.

On top of the free CRUD functions, add a tiny `ModuleStore` accessor bound to a
single module code, so call sites read as `store.set("cursor", {...})` instead of
threading `module=` through every call — this is the ergonomic win the user asked for
("куда положить" → one obvious place per module). `Module.store` returns
`module_store(self.name)` so a module never even types its own code.

**Alternative considered — reuse `core_modules_settings`:** rejected. It would
conflate machine state with operator config, leak internal keys into the settings UI,
and force JSON-in-Text. The tables are cheap; the conceptual separation is worth one
more table.

**Alternative considered — bound accessor only, no free CRUD:** rejected. The free
functions mirror the established `crud/*` convention (each opens its own
`session_scope`), are directly testable, and the accessor is a thin wrapper over them
— keeping both matches how the rest of core is layered.

**`value` portability:** declare the column as
`sa.JSON().with_variant(postgresql.JSONB, "postgresql")` so it is JSONB on Postgres
(prod + the `db`/`heavy` test DBs) and plain JSON if a SQLite path is ever exercised
— same defensive dialect handling the settings CRUD already carries for `insert`.

## Steps

Ordered; each is a single review unit.

1. **Model** — `src/core/models/module_state.py`: `CoreModuleState(Base)`,
   `__tablename__ = "core_modules_state"`, columns `module: String(64)` PK,
   `key: String(128)` PK, `value` JSONB-variant `NOT NULL`, `created_at`/`updated_at`
   `TIMESTAMP(precision=0)`. Mirror `module_settings.py` exactly except `value` type.
2. **Register model** — `src/core/models/__init__.py`: import `module_state` so the
   table lands in `Base.metadata`; add to `__all__`.
3. **CRUD** — `src/core/crud/module_state.py`, mirroring `crud/module_settings.py`
   (keep the `_insert_for(session)` dialect helper):
   - `list_for_module(module) -> list[CoreModuleState]`
   - `get_one(module, key) -> CoreModuleState | None`
   - `get_value(module, key) -> Any | None` (returns `.value` or `None`)
   - `upsert(module, key, value: Any) -> None` (INSERT … ON CONFLICT DO UPDATE
     value+`updated_at`; `created_at` only on first insert)
   - `seed_if_absent(module, key, value: Any) -> bool`
   - `delete(module, key) -> None`
   - `delete_for_module(module) -> None` (clear a namespace)
   - `list_all() -> list[CoreModuleState]`
4. **Accessor** — `src/core/module_state.py`: a small `ModuleStore` (frozen
   dataclass holding `module: str`) with async `get(key, default=None)`,
   `set(key, value)`, `seed_if_absent(key, value)`, `delete(key)`, `all() -> dict`,
   each delegating to the CRUD with `module` pre-bound; plus
   `module_store(module: str) -> ModuleStore`.
5. **Module integration** — `src/core/module.py`: add a `store` property returning
   `module_store(self.name)` (lazy import to avoid a DB import at class-build time).
   Document it in the class docstring next to the lifecycle hooks.
6. **Migration** — `src/core/migrations/versions/20260610_0002_init_core_modules_state.py`:
   `revision = "c0re00010005"`, `down_revision = "c0re00010004"` (current core head
   after the team-drop merge). `create_table` mirroring the settings init migration,
   `value` as `postgresql.JSONB(astext_type=...)` NOT NULL; `downgrade` drops it.
   Keep the revision id ≤32 chars (see memory `alembic-revision-id-len`).
7. **Exports** — surface `module_store`/`ModuleStore` where the rest of core is
   imported from (e.g. re-export from `src/core/__init__.py` if that is the
   convention for such helpers — verify before adding).
8. **Docs + memory** — add `AGENTS/docs/platform/module-state.md` (what it is, when to
   use vs settings, the accessor API, the settings-vs-state table) and a routing line
   in `MEMORY.md` §2 under Platform; optionally a one-line gotcha distinguishing it
   from settings.

## Tests

- **db — CRUD** (`tests/core/crud/test_module_state.py`): upsert insert→update
  (created_at frozen, updated_at advances, value replaced); `get_one`/`get_value`
  miss → `None`; `seed_if_absent` returns True first / False second and does not
  overwrite; `delete` and `delete_for_module`; JSONB round-trips a nested
  dict/list/number/bool/null unchanged (not stringified); two modules with the same
  `key` are isolated (PK is composite).
- **db — accessor** (`tests/core/test_module_state.py`): `module_store("x").set/get`
  round-trip; `get` default on miss; `all()` returns the namespace as a dict;
  `Module.store` binds to `name`.
- **heavy — migration** (`tests/core/.../test_migration_module_state.py` or the
  existing core migration test): upgrade creates the table with the right columns +
  composite PK; downgrade drops it; no drift after upgrade-to-head
  (`migrate check`-style parity).

## Validation

- `uv run pytest --core` green (CRUD + accessor), `--heavy` green (migration).
- `uv run python src/app.py migrate check` on the dev DB reports **no drift** after
  applying `c0re00010005`.
- Manual: in a Python shell / throwaway task, `module_store("scratch").set(...)` then
  `.get(...)` returns the structured value; row visible in `core_modules_state`.

## Risks / open questions

- **Open — column name `key` vs `code`.** User phrased the table as
  "module **code** value". Plan uses `key` to mirror `core_modules_settings` (one
  mental model for both). If the user prefers `code`, rename in steps 1/3/6 — trivial,
  but decide before step 1.
- **Open — `value` JSONB vs Text.** Plan picks JSONB (structured state, native dicts).
  If symmetry with settings (`Text`) is preferred, the module serializes JSON itself
  and the accessor does `json.dumps/loads`. Decide before step 1. *(Asked; defaulting
  to JSONB.)*
- **Open — accessor vs free-CRUD-only.** Plan ships both (accessor over CRUD). If only
  free functions are wanted, drop steps 4–5. *(Asked; defaulting to the accessor.)*
- **Risk — JSONB on a non-Postgres dialect.** Mitigation: `with_variant` JSON fallback
  + the existing dialect-aware insert helper; real test DBs are Postgres so JSONB is
  exercised for real.
- **Risk — naming collision with a module's own keys.** PK is `(module, key)`, so
  namespaces never collide across modules; within a module it is the module's own
  responsibility (same as settings).
- **Risk — unbounded growth / stale keys.** No TTL in v1; `delete_for_module` gives a
  cleanup hook. Revisit only if a consumer accumulates churn.

## References

- Related task: `AGENTS/tasks/2026-06-10-core-module-state-store.md`
- First consumer (separate task): `AGENTS/tasks/2026-06-10-mail-sync-gmail-api-import.md`
- Mirror: `src/core/models/module_settings.py`, `src/core/crud/module_settings.py`
- Migration pattern: `src/core/migrations/versions/20260512_0001_init_core_modules_settings.py`
- Memory: `AGENTS/memory/alembic_revision_id_len.md` (revision id ≤32 chars)
- Conventions: `AGENTS/docs/conventions/backend.md`, `AGENTS/docs/platform/migrations.md`
