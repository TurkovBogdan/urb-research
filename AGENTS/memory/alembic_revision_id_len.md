---
name: alembic_revision_id_len
description: Alembic revision id must be ≤32 chars — alembic_version.version_num is varchar(32)
metadata: 
  node_type: memory
  type: project
  originSessionId: 3119a4f6-81f6-4958-8f10-dd7f425382cb
---

Alembic `revision` id strings must be **≤32 characters**: the `alembic_version.version_num` column is `VARCHAR(32)`. A longer id passes Python but fails at upgrade time with `StringDataRightTruncationError: value too long for type character varying(32)` on the `UPDATE alembic_version SET version_num=...` step (only surfaces when a heavy/real-migration test or actual upgrade runs).

Keep ids short and area-prefixed, e.g. `c12_last_activity_at`, not `c12_conversations_last_activity_at` (33 chars → fails). Module migrations: [[conversations_lifecycle_timestamps]] live under each module's own revision chain.
