---
name: feedback-migration-verify
description: "After writing any migration, run migrate upgrade immediately; db-tests bypass Alembic and won't catch migration code bugs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 621c133e-c7eb-4784-bead-0af355e42a80
---

Always run `uv run python src/app.py migrate upgrade` immediately after writing a migration file — before considering the task done.

**Why:** `db`-tests create schema via SQLAlchemy `create_all` (bypasses migration files entirely); only `--heavy` tests run actual Alembic `upgrade heads`. A broken migration `.py` file passes all `db`-tests silently.

**How to apply:** After writing a migration, verify it applies cleanly. Also: grep neighbouring migration files for dialect-specific types before writing (e.g. `postgresql.TIMESTAMP(precision=0)`, not `sa.TIMESTAMP(precision=0)`).
