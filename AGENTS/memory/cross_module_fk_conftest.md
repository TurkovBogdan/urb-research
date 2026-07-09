---
name: cross_module_fk_conftest
description: "db-tests cross-module FK needs the target module's models imported in the source module's conftest"
metadata: 
  node_type: memory
  type: project
  originSessionId: bf9f2eeb-5a6f-4f9c-83f4-a2a6ea8cfc0f
---

A `db`-test builds its schema via `Base.metadata.create_all` (not Alembic). A
cross-module FK (e.g. `intercom_conversation_messages_attachments.file_id` →
`core_storage_files`) resolves at create_all **only if the target table is in
`Base.metadata`** — i.e. the target module's models were imported.

The **full suite** gets this for free: every module's `conftest.py` is collected, so
`core_storage`'s conftest imports its models globally. But an **area-filtered run**
(`--module=intercom,...`) skips uncollected modules' conftests → `NoReferencedTableError`
at the first create_all, and (because `Base.metadata` is a process-global singleton
polluted by import order) the failure spills into *unrelated* modules' tests.

**Fix:** in the source module's `tests/modules/<m>/conftest.py`, import the FK-target
module's models — `from src.modules.core_storage import models  # noqa: F401`. Mirror
this in any conftest that pulls the source module (e.g. conversations `importers`/`tasks`
conftests import intercom+mail_sync, so they need core_storage too). Precedent:
`tests/modules/mail_sync/conftest.py`. See [[feedback_migration_verify]].
