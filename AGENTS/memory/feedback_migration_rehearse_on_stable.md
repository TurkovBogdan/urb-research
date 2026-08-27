---
name: feedback_migration_rehearse_on_stable
description: "Standard — rehearse every migration chain on a copy of urb-research-stable's DB, after backing it up tagged with its head revision."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fb4d35d3-b9de-4349-8a3e-207add024829
  modified: 2026-08-27T01:00:20.599Z
---

Before shipping migrations, rehearse them against the **stable instance's real data**, not just dev:

1. Back up stable's DB into its own gitignored backup dir, named with the revision it is frozen at:
   `urb-research-stable/runtime/dev/backup/app.sqlite3.<head_revision>.<YYYY-MM-DD>`
   (verify with `git check-ignore` — the file is ~40 MB).
2. Copy that backup to scratch and apply the pending chain to the **copy**:
   `DB_PATH=/tmp/... uv run python src/app.py migrate upgrade`. Never the original.
3. Diff the outcome (row counts per status, joins that must hold, `PRAGMA integrity_check` +
   `foreign_key_check`, final constraints, no orphan `_alembic_tmp_*`), then ship.

**Why:** stable and dev drift apart — stable lagged 3 revisions behind dev and carried different
data volumes, so a chain that is green on dev is unproven. Its data is the real target.

**How to apply:** treat it as a required step of any migration task, alongside
[[feedback_migration_verify]]. Stop the backend before applying anything to a real file — `.env`
ships `DB_AUTO_MIGRATE=true` with `--reload`, so a running backend is a second writer.

Related: [[migration_file_naming]], [[dev_query_hits_postgres_not_sqlite]].
