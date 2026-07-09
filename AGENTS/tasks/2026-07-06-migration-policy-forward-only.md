# migrations: forward-only policy; dev rebuild only on request

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** docs/memory — migration workflow policy

## Goal

Reverse the prior "edit the migration in place + rebuild dev" rule. New policy: schema changes are
**new forward-only migrations** (extend the chain); applied migrations are not edited in place; wiping/
rebuilding the dev DB happens **only on explicit user request**.

## What was done

- **MEMORY.md** §3 gotcha "dev sqlite строится МИГРАЦИЯМИ": replaced «Правка схемы = правка миграции
  (in-place) + пересборка dev» with «Изменение схемы = НОВАЯ forward-only миграция; пересборка/очистка
  dev — ТОЛЬКО по явному требованию пользователя». Kept the 🔴 deleted-inode warning + `migrations_dir`
  requirement (they apply whenever a rebuild IS requested).
- **docs/platform/database.md**: reworded the sqlite tier — schema changes ship as new forward-only
  migrations; dev wipe/rebuild only on explicit user request.
- **docs/platform/migrations.md**: replaced the "When to consolidate" section (squash-while-in-design)
  with "Schema changes = new forward-only migrations" (no in-place edits / no default squash; rebuild
  only on request).
- Verified no other memory files carry the old in-place/squash/rebuild policy.

## Problems

None.

## Result

Going forward: new migrations for every schema change (`add_*`/`drop_*`/`rename_*`, fresh `NN`); no
editing applied migrations; the earlier in-place-edit + dev-rebuild workflow is retired. DB wipe only
when the user explicitly asks. Unchanged: migration naming scheme, one-table-per-creation, cross-module
`depends_on`, "run `migrate upgrade` after writing a migration".
