---
name: alembic_retire_module_branch
description: "Removing a module deletes its independent alembic branch — orphaned head row breaks `upgrade heads`; fix = tombstone + merge migration"
metadata: 
  node_type: memory
  type: project
  originSessionId: dc9c4868-eab7-4c52-8f55-899443070a57
---

Each module owns an **independent** alembic branch (own root, separate head row in `alembic_version`). Deleting the module drops its `migrations_dir` from `version_locations`, but existing DBs still carry its head → alembic can't resolve it → `command.upgrade(cfg, "heads")` raises «Can't locate revision» **before** any new migration runs. A plain `DROP TABLE IF EXISTS` core migration can't fix this (it never executes).

Fix (used to retire `team` 2026-06-10): **relocate** the dead module's revision files into `src/core/migrations/versions/` and empty their `upgrade`/`downgrade` to `pass` (tombstones — keep `revision`/`down_revision` so the head stays resolvable), then add a **merge** migration whose `down_revision=(<core_head>, <dead_branch_head>)` that does the `DROP TABLE IF EXISTS` and collapses the orphan head into core. Fresh DBs: tombstones are no-ops (tables never created); existing DBs: tables dropped + head row merged. See [[full_update_task_split_skip_guard]] for the AlembicRunner model.
