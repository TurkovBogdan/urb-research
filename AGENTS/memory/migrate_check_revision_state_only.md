---
name: migrate_check_revision_state_only
description: "migrate check compares revision heads only, not schema-vs-models (no autogenerate drift)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 76db7f57-8032-4f71-b2d1-d93a4f0e5876
---

`migrate check` / `AlembicRunner.status` (`src/core/database/migrations.py::_do_status`)
only compares **applied revision heads vs target heads** (pending list) — it does
**NOT** autogenerate-diff the DB schema against `Base.metadata`. So migrations can
silently diverge from models (extra/missing index, wrong column) and `migrate check`
stays green. Model↔schema parity is enforced only by `db`-tests (`create_all`) and the
heavy `tests/core/test_migrations.py::test_full_tree_upgrade_builds_model_schema_with_seeds`
(real `upgrade heads` → `compare_metadata` zero structural drift). Add a compare_metadata
check when you need true drift detection. See [[migration_file_naming]] · [[feedback_migration_verify]].
