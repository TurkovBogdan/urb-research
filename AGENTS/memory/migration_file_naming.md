---
name: migration_file_naming
description: Alembic migration filename / revision-id naming scheme for new migrations
metadata: 
  node_type: memory
  type: reference
  originSessionId: 371392ca-1a63-4f7e-a5e1-8357002566f1
---

Migration **filename stem == Alembic `revision` id** = **`<abbr>m_<NNN>_<description>`**:
- `<abbr>m` — module abbreviation + trailing `m` (= "module"); `core_storage` → `csm`.
- `<NNN>` — zero-padded sequence (`001`, `002`, …).
- `<description>` — what it does; the **first** migration is named after the **first table it
  creates**, never `init` — e.g. `csm_001_files`, `csm_002_files_refs`.

One table per migration. Id ≤ 32 chars ([[alembic_revision_id_len]]). Renaming an id ⇒ fix every
`down_revision`/`depends_on` that targets it (other modules too) + re-stamp dev `alembic_version`.
Canonical for new migrations; older modules (`cg01_`, `ci01_`, `i01_`) predate it. Full rule +
cross-module `depends_on` mechanics → `docs/conventions/db-migrations.md`.
