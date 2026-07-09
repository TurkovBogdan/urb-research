---
title: Core module state store (arbitrary per-module KV)
date: 2026-06-10
status: completed  # in-work | completed | deferred
description: "Core-provided generic per-module key/value store for arbitrary runtime state (e.g. import cursors), distinct from the user-facing settings store. Implemented + tested."
tags: [core, database, module-system]
---

## Task

User: the core should give modules an arbitrary data store as a table/entities.
Example: a task needs to persist its import state — today there is no obvious place
for it. Wants a table of the shape `module | code | value | created_at | updated_at`
for arbitrary values. Asked to work it out and create a plan.

## Context

No generic per-module state home exists. The only adjacent thing,
`core_modules_settings` (+ `_settings/*` stack), is user-facing **configuration**
(schema-typed, surfaced in UI) — wrong place for internal machine state. First real
consumer would be the `mail_sync` gmail-api `history_id` cursor (task
`2026-06-10-mail-sync-gmail-api-import.md`), which currently proposes a bespoke column.

## What was done

- Investigated core DB layer and wrote plan `AGENTS/plans/2026-06-10-core-module-state-store.md`.
- User confirmed: column **`code`** (not `key`), JSONB value, accessor + CRUD — implemented:
  - Model `src/core/models/module_state.py` (`CoreModuleState`, PK `(module, code)`,
    `value` `JSON().with_variant(JSONB, "postgresql")`, `created_at`/`updated_at`);
    registered in `src/core/models/__init__.py`.
  - CRUD `src/core/crud/module_state.py` (mirror of `module_settings`, dialect-aware
    upsert): `list_for_module`/`get_one`/`get_value`/`upsert`/`seed_if_absent`/
    `delete`/`delete_for_module`/`list_all`.
  - Accessor `src/core/module_state.py`: `ModuleStore` (frozen dataclass, module
    pre-bound) `get`/`set`/`seed_if_absent`/`delete`/`all` + `module_store(code)`.
  - `Module.store` property in `src/core/module.py` (= `module_store(self.name)`,
    lazy import; TYPE_CHECKING import for the annotation).
  - Migration `src/core/migrations/versions/20260610_0002_init_core_modules_state.py`
    (`c0re00010005`, `down_revision=c0re00010004`).
  - Doc `AGENTS/docs/platform/module-state.md` + docs INDEX entry + memory router line.
- Tests added: `tests/core/test_crud_module_state.py` — 9 `db` tests (upsert
  insert→update with frozen `created_at`; get misses; `seed_if_absent` first-wins;
  JSONB nested round-trip; composite-key module isolation; delete + delete_for_module;
  accessor set/get/all; accessor seed+delete; `Module.store` binds name). Extended the
  `heavy` migration test `test_upgrade_head_applies_core_migrations` to assert
  `core_modules_state` in the core table set.

## Problems

First combined `pytest` run reported only "2 passed" (xdist/area selection quirk when
mixing `--heavy` with db tests in one invocation). Re-ran each file separately:
`test_crud_module_state.py` 9 passed, `test_migrations.py --heavy` 2 passed.

## Result

Shipped (code + tests). Created/changed:
- `src/core/models/module_state.py`, `src/core/models/__init__.py`
- `src/core/crud/module_state.py`
- `src/core/module_state.py`, `src/core/module.py`
- `src/core/migrations/versions/20260610_0002_init_core_modules_state.py`
- `tests/core/test_crud_module_state.py`, `tests/core/test_migrations.py`
- `AGENTS/docs/platform/module-state.md`, `AGENTS/docs/INDEX.md`, `AGENTS/memory/MEMORY.md`

Verified: 9 db + 2 heavy green; dev DB migrated to `c0re00010005`, `migrate check`
no drift. First consumer (mail_sync gmail-api `history_id` cursor) intentionally NOT
wired — that lands with its own task.
