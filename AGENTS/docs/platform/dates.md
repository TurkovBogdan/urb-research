# Dates — conventions and patterns

**Always read if working with dates** — migrations, ORM models, DB entities, API schemas, frontend date display, data processing with timestamps.

---

## Backend — storage

All `datetime` values in the DB are stored as **naive UTC** (`TIMESTAMP WITHOUT TIME ZONE`).
PostgreSQL is configured to UTC.

### TIMESTAMP type in migrations and models

Use the **portable `timestamp()`** from `src.core.database.types` — in **both models and migrations**. Never raw `sa.TIMESTAMP()`, and no longer the dialect-bound `postgresql.TIMESTAMP` directly.

`timestamp()` is `DateTime().with_variant(TIMESTAMP(precision=0), "postgresql")`: second-precision `TIMESTAMP` on Postgres, generic `DateTime` on SQLite — so the same model **and migration** runs on both providers (migrations are dialect-agnostic; same for `json_value()` ↔ `JSONB`/`JSON`).

```python
# models
from src.core.database.types import timestamp
some_at: Mapped[datetime | None] = mapped_column(timestamp(), nullable=True)

# migrations (run on SQLite and Postgres)
from src.core.database.types import timestamp
_TS = timestamp()
op.add_column("some_table", sa.Column("some_at", _TS, nullable=True))
```

SQLite ignores the `precision` variant (raw column would keep microseconds), so **`utc_now()` truncates to seconds** (`microsecond=0`) — second-precision storage holds on both providers, matching the `YYYY-MM-DD HH:MM:SS` serialization. Mixing in `sa.TIMESTAMP()`/`datetime.now()` reintroduces microsecond artifacts.

**`utc_now()` / `utc_today()` always:**
```python
from src.core.utils.date import utc_now, utc_today

utc_now()    # → datetime  naive UTC — for timestamps stored in DB
utc_today()  # → date      UTC date only — when time component is not needed
```

Never `datetime.now()` (server local time) or `datetime.utcnow()` (deprecated).

### `created_at` / `updated_at` column defaults — single source is `utc_now()`

Timestamp columns default **Python-side** through `utc_now`, never the DB clock:

```python
from src.core.utils.date import utc_now

created_at: Mapped[datetime] = mapped_column(timestamp(), default=utc_now)
updated_at: Mapped[datetime] = mapped_column(
    timestamp(), default=utc_now, onupdate=utc_now
)
```

Migrations declare the column **without** a server default (`sa.Column("created_at", _TS, nullable=False)`) — Python-side `default`/`onupdate` emit no DDL default, so model and migration stay in parity.

**Never `server_default=func.now()` / `onupdate=func.now()`.** Two reasons: (1) on Postgres `now()` written into a naive `TIMESTAMP` stores the **DB session's timezone**, not guaranteed UTC — `utc_now()` always stores true UTC; (2) it becomes a **second time source** alongside `utc_now()` and, on SQLite, a second storage format (`func.now()` → no fractional, `utc_now()` → `.000000`). One source only: `utc_now()`. As a bonus, Python-side `onupdate=utc_now` is client-computed, so it no longer needs the `s.refresh(row)` dance that a SQL-side `onupdate` required (see backend.md).

### Why not TIMESTAMPTZ

Deliberate decision: keep `TIMESTAMP WITHOUT TIME ZONE` and store explicit UTC.
Migration to `TIMESTAMPTZ` is not planned. `DatetimeUTCStr` serializer and `{ zone: 'utc' }` on the frontend cover the absent timezone suffix.

**Why:** user explicitly declined changing column types; migration complexity is not justified.

---

## Backend — API serialization

In Pydantic schemas that return datetimes to the client, use `DatetimeUTCStr` from `src.core.utils.date`:

```python
from src.core.utils.date import DatetimeUTCStr

class SomeOut(BaseModel):
    created_at: DatetimeUTCStr          # naive UTC → "2026-05-06 15:01:18"
    updated_at: DatetimeUTCStr
    finished_at: DatetimeUTCStr | None
```

`DatetimeUTCStr` is `Annotated[datetime, PlainSerializer(...)]`: accepts naive or aware datetime, returns `"YYYY-MM-DD HH:MM:SS"` without timezone suffix. Frontend treats all such strings as UTC via `DateTime.fromSQL(s, { zone: 'utc' })`.

### Where already applied

> Indicative list — `grep -rn 'utc_now\|DatetimeUTCStr' src` for the live set.

`utc_now()` (from `src.core.utils.date`): scheduler/locks core (`src/core/locks/lock.py`, `src/core/scheduler/ticker.py`) + every CRUD layer that stamps `synced_at`/`processed_at`.

---

## `synced_at` — external data import timestamp

Any table that receives data from an external source (API, email, etc.) carries a `synced_at` column: **when did our system last fetch and process this record**.

### Semantics

| Field | Owner | Meaning |
|---|---|---|
| `created_at` | external source | when the entity was created in the source system |
| `updated_at` | external source | when the entity was last modified in the source system |
| `synced_at` | **our system** | when we last fetched + stored this record |

`synced_at` is set to `utc_now()` at every upsert, regardless of whether the data changed.

### Incremental import cursor

`synced_at` doubles as the cursor for incremental imports. The importer queries `max(synced_at)`, subtracts an overlap window (typically 15 min to absorb clock skew), and requests only records updated after that threshold:

```python
max_synced = await crud.get_max_data_built_at()   # or get_max_synced_at()
threshold  = max_synced - timedelta(minutes=15)
query = {"field": "updated_at", "operator": ">", "value": parse_ts(threshold)}
```

**Important:** `synced_at` is only updated when a record is actually written. If an importer run skips a record (unchanged `updated_at`), `synced_at` stays at the previous value — it does not mean "last time the importer looked at this record".

### CRUD convention

Set `synced_at` explicitly in the CRUD layer, not in the model or importer:

```python
row["synced_at"] = utc_now()   # always overwrite, even on conflict-update
```

This keeps importers free of lifecycle concerns: they construct objects with the data they received; CRUD stamps when it was stored.

---

## `processed_at` — internal processing timestamp

Any record that is post-processed by our own handlers (filters, parsers, classifiers, etc.) carries a `processed_at` column: **when did our system last run its processing pipeline on this record**.

Use instead of `updated_at` when the only thing our system modifies is the result of processing — not the source data itself.

### Semantics

| Field | Owner | Meaning |
|---|---|---|
| `synced_at` | our system — import layer | when we last fetched + stored this record from the source |
| `processed_at` | our system — processing layer | when we last ran our handlers (filter, parser, etc.) on this record |

`processed_at` is updated every time a processing task runs on the record, regardless of whether the output changed.

### CRUD convention

Set `processed_at` explicitly in the CRUD layer when writing processing results:

```python
await s.execute(
    update(Model)
    .where(Model.id == entity_id)
    .values(processed_at=utc_now(), ...)
)
```

---

## `ingested_at` — derived-layer upstream cursor

Any **derived/aggregate** table that is built from other tables in our own DB (not directly from an external API) carries an `ingested_at` column: **up to which point of upstream activity is this aggregate consistent**.

Use instead of `synced_at` in derived layers. `synced_at` is reserved project-wide for the external-import boundary (see above) — overloading it on a derived table hides whether the timestamp reflects external sync or our own re-processing.

### Semantics

| Field | Owner | Meaning |
|---|---|---|
| `ingested_at` | derived layer | latest upstream-row activity (`processed_at` if upstream has it, else `synced_at`) the aggregate has incorporated |
| `processed_at` | derived layer | when our aggregator last (re)built this row |

`ingested_at` is computed at build time as `max(upstream.processed_at or upstream.synced_at)` over all source rows that contribute to the aggregate. It is **not** `utc_now()`.

### Why both fields exist

A delta filter on derived data must catch any upstream change, including **re-processing without re-sync** — e.g. a processing rule is edited, an upstream row's `processed_at` is bumped, `synced_at` is not. If the aggregate's cursor were `max(upstream.synced_at)`, it would miss this and the aggregate would go stale silently.

### Incremental rebuild cursor

```python
threshold = await crud.get_min_ingested_at(provider)
# fetch upstream rows where upstream.processed_at|synced_at > threshold (minus lag)
```

`min` (not `max`) over the provider: guarantees no aggregate is skipped if it was built earlier than the freshest one. Newly arriving upstream rows trivially exceed any threshold.

---

## Frontend — date formatting

All date formatting goes through `@/shared/utils/date`. Never import `DateTime` from `luxon` directly in components.

**Why:** The backend sends UTC timestamps as `"YYYY-MM-DD HH:MM:SS"` without timezone info. `DateTime.fromSQL(s)` without options treats a bare (offset-less) string as local time — wrong. The utility parses every string as UTC (`{ zone: 'utc' }`), then **renders it in the user's chosen timezone**: the internal `_zoned` helper applies `.setZone(currentZone)`, where `currentZone` comes from the reactive prefs (`@/plugins/preferences`, localStorage `app.timezone`, default «Авто» = browser zone). The single exception is `fmtDateUtc`, which renders in UTC with no zone shift (day-aligned bounds, filters). Date-format choice (`app.dateFormat`) is read the same way.

| Function | Format | Use for |
|---|---|---|
| `fmtDate(s)` | `dd.MM.yyyy` | date only (in user tz) |
| `fmtDateUtc(s)` | `dd.MM.yyyy` | date only, **no tz shift** — day-aligned filter bounds |
| `fmtDateTime(s)` | `dd.MM.yyyy HH:mm` | timestamps in tables |
| `fmtDateTimeSec(s)` | `dd.MM.yyyy HH:mm:ss` | task runs, logs |
| `fmtTime(s)` | `HH:mm` | chat bubbles |
| `fmtTimeSec(s)` | `HH:mm:ss.SSS` | log timestamps |
| `fmtRelative(s)` | «5 минут назад» | secondary line under date |
| `fmtRelativeShort(s)` | «5 мин» | compact relative (no «назад»/«через») |
| `fmtDaysAgo(s)` | «сегодня» / «вчера» / «N дней назад» | whole-day delta |
| `fmtDuration(start, end)` | `1m 23s` | duration between two timestamps |

All accept `string | null` and return `'—'` (or `''` for `fmtRelative`/`fmtRelativeShort`) on null.

**Standard table date cell** — date on the first line, relative time dimmed below:
```vue
<template #item.created_at="{ item }">
  <div>{{ fmtDateTime(item.created_at) }}</div>
  <div class="text-caption text-medium-emphasis">{{ fmtRelative(item.created_at) }}</div>
</template>
```
