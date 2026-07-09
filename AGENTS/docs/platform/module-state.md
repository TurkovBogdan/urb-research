# module-state — generic per-module state store

A core-provided key/value store for **arbitrary runtime state** a module needs to
persist — import cursors, counters, last-run markers, dedup checkpoints — without
inventing its own table. Backed by `core_modules_state`, keyed by `(module, code)`,
`value` is **JSONB** (store a dict directly, no manual `json.dumps`).

## When to use it (vs settings)

This is for **internal machine state written by module code** — not user-facing
configuration. Operator-tunable config belongs in the settings store
(`core_modules_settings` + `settings_schema`, surfaced in the settings UI). The two
are deliberately near-identical in shape but separate homes:

| | `core_modules_settings` | `core_modules_state` |
|---|---|---|
| Purpose | operator-tunable config | internal runtime state |
| `value` | `Text` (typed by schema) | `JSONB` (arbitrary structure) |
| Surfaced in UI / API | yes (settings page) | no |
| Schema / registry | yes (`_settings/*`) | none |
| Written by | operator via `PUT /core/settings/{module}` | module code |

## Accessing it

`Module.store` is bound to the module's own `name`, so a module never types its code:

```python
async def on_startup(self, app):
    cursor = await self.store.get("gmail_import_cursor")          # -> dict | None
    ...
    await self.store.set("gmail_import_cursor", {"history_id": "98213"})
```

Outside a `Module` instance, use the factory:

```python
from src.core.module_state import module_store

store = module_store("my_module")
await store.set("import_cursor", {"history_id": "98213"})
state = await store.get("import_cursor", default={})
keys  = await store.all()          # {code: value} for this module
await store.seed_if_absent("init_marker", {"done": True})   # True iff created
await store.delete("import_cursor")
```

`ModuleStore` is a thin wrapper over `src/core/crud/module_state.py`, which holds the
free CRUD (`upsert`/`get_one`/`get_value`/`seed_if_absent`/`delete`/
`delete_for_module`/`list_for_module`/`list_all`) — each opens its own
`session_scope` (the standard CRUD-owns-session convention). The store is available
only after DB init (startup/runtime), not in `configure()`.

## Semantics

- PK `(module, code)` — namespaces never collide across modules; within a module the
  `code` space is the module's own responsibility.
- `upsert` / `set` replaces `value` and bumps `updated_at`; `created_at` is frozen at
  first insert.
- `seed_if_absent` / `seed_if_absent` (accessor) inserts only when absent (returns
  whether it created the row) — never overwrites.
- No TTL/history/versioning in v1; `delete_for_module` clears a namespace.

## Files

- Model: `src/core/models/module_state.py` (`CoreModuleState`)
- CRUD: `src/core/crud/module_state.py`
- Accessor: `src/core/module_state.py` (`ModuleStore`, `module_store`)
- `Module.store`: `src/core/module.py`
- Migration: `src/core/migrations/versions/20260610_0002_init_core_modules_state.py` (`c0re00010005`)
