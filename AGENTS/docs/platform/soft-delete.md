# Soft delete

## Pattern

Logical deletion: instead of removing a row, set `deleted_at` to the current UTC timestamp. The row stays in the DB; all CRUD queries treat non-null `deleted_at` as "does not exist".

## Mixin

`SoftDeleteMixin` lives in `src/core/database/mixins.py`, exported from `src/core/database`.

```python
class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(precision=0), nullable=True)
```

Apply before `Base`:

```python
class MyModel(SoftDeleteMixin, Base):
    __tablename__ = "my_table"
    ...
```

## CRUD conventions

Every entity with soft delete must follow these rules consistently.

**Filtering** — all read operations accept `include_deleted: bool = False` (keyword-only). Default always excludes deleted rows:

```python
async def list_all(*, include_deleted: bool = False) -> list[Model]:
    q = select(Model).order_by(Model.id)
    if not include_deleted:
        q = q.where(Model.deleted_at.is_(None))
    ...
```

Applies to: `list_*`, `get_by_id`, `list_ids`, any query used for business logic.

**Delete** — single method, soft by default. `hard=True` physically removes the row:

```python
async def delete(entity_id: int, *, hard: bool = False) -> None:
    async with session_scope() as s:
        if hard:
            await s.execute(sa_delete(Model).where(Model.id == entity_id))
        else:
            await s.execute(
                update(Model)
                .where(Model.id == entity_id)
                .values(deleted_at=utc_now())
            )
```

Prefer soft delete (default) when FK constraints exist. Pass `hard=True` only for leaf tables or admin tooling.

**Upsert un-deletes** — include `deleted_at` in the `ON CONFLICT DO UPDATE` set so that a reimported record is automatically un-deleted (`deleted_at` reset to `NULL`):

```python
# _SKIP = frozenset({"created_at"})  — deleted_at is NOT in _SKIP
.on_conflict_do_update(
    index_elements=[Model.id],
    set_={k: pg_insert(Model).excluded[k] for k in rows[0] if k not in {"id", "created_at"}},
)
```

## Migration

```python
op.add_column(
    "my_table",
    sa.Column("deleted_at", postgresql.TIMESTAMP(precision=0), nullable=True),
)
```

## When to use

Use soft delete when:
- The table is referenced by a FK with `ON DELETE RESTRICT` — hard delete would violate the constraint once child rows exist.
- Audit / history matters — deleted records should remain queryable (admin panels, support tooling).

Use hard delete when the table is a leaf (no FK children) and data retention is not required.

## Cascading soft delete

When a parent is soft-deleted and children must follow, do it in a single `session_scope` to keep the operation atomic:

```python
async def delete(user_id: int, *, hard: bool = False) -> None:
    async with session_scope() as s:
        if hard:
            await s.execute(sa_delete(User).where(...))
            # DB CASCADE removes children physically
        else:
            now = utc_now()
            await s.execute(update(User).where(...).values(deleted_at=now))
            await s.execute(update(Session).where(Session.user_id == user_id).values(deleted_at=now))
```

## Gotcha — unique columns + soft delete

A plain `UNIQUE` index covers soft-deleted rows too, so re-inserting a value freed by a soft-delete hits an `IntegrityError` (500) — and a `get_by_*` dedup pre-check (which filters `deleted_at IS NULL`) won't catch it. Two fixes:

- **(a) Partial unique** `UNIQUE(col) WHERE deleted_at IS NULL` — value reusable after delete; produces a new row/id.
- **(b) Upsert-un-delete** — one row per value, restores the id.

A unique column reusable after delete uses (a): declare the index as `Index(..., unique=True, postgresql_where=text("deleted_at IS NULL"))` in `__table_args__` — **not** `unique=True` on the column, else `create_all` in tests builds a full unique and diverges from the migration.

## Where applied

Source of truth: `grep -rl SoftDeleteMixin src/modules/*/models`. The `deleted_at`
column ships **inside each table's create-table migration** (not a separate
"add deleted_at" migration), so there are no dedicated migration IDs to track. Bare-core
ships no domain modules, so no entity currently uses the mixin — the pattern above is the
template for when one does.
