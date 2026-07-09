# Backend conventions

Read this before writing or refactoring backend Python — module models, CRUD, DTOs, API routes, or any derived/processed table. Code-shape rules the user enforces.

## Field change = three layers in one edit

Changing the **type or shape** of an entity field is always a three-layer edit in one task:

1. **Migration** in `src/modules/<m>/migrations/versions/` — `alter_column` with `postgresql_using` for existing-data conversion, correct `down_revision`, and a `downgrade()` path.
2. **ORM model** in `src/modules/<m>/models.py` — `Mapped[...]` updated to the new type; for arrays — `ARRAY(Text)` via `mapped_column`.
3. **DTO/Draft** in the relevant location (`<m>/content/draft.py`, `dto/rows.py`, `dto/api.py`) — must match the same type, otherwise mypy passes but inserts/selects fail at runtime.

**Why:** ORM model and draft/DTO must strictly match the DB schema. Missing migration → column doesn't exist; missing model → SQL complains about an absent field; missing DTO → the channel writes an incompatible type. These bugs surface only at runtime on live data.

**How to apply:** for any request to "update field X" (type, nullable, default, rename, move to array) — make all three edits in one task and apply the migration. If unsure whether a field can be renamed/changed — ask, but never do only part of the work.

## CRUD — one file per entity

In each module's `crud/` folder — one file per ORM entity. Do not mix CRUD operations for different tables in the same file.

**Why:** this makes `crud/` mirror `models/` 1:1, makes it easy to find CRUD by table/model name, and prevents a bloated catch-all file from growing.

**How to apply:** new CRUD for an existing entity → its file (`crud/<entity>.py`). New entity → new file, name matches the model (`models/<entity>.py` ↔ `crud/<entity>.py`). E.g. `crud/user.py` for a `User` model, `crud/session.py` for a `Session` model.

## CRUD descriptive names

Name CRUD methods by **what is being queried by** — e.g. `token_by_public_id`, `token_list_by_user`, `token_count_by_user` — NOT vague verbs like `list_for_user` / `get`.

**Why:** the call site should read as "what we look up by", self-documenting.

**How to apply:** name CRUD functions `<entity>_<verb>_by_<key>` (e.g. `token_by_public_id`, `token_mark_used`). Prefix with the entity name (`token_…`/`user_…`/`session_…`) even though the file is already entity-scoped — the user asked for the entity prefix explicitly. Illustrative for a hypothetical user/token/session module: `user_get`, `user_list`, `user_update_profile`, `session_create`, `session_mark_used`, …. An actor-split self-surface (`crud/own_user.py`) carries a **`_self` suffix** (`user_get_self`, `user_update_profile_self`) so the actor is visible in the method name itself — not only in the file / import alias — and a self-op never reads as its same-SQL admin twin (`user_get`/`user_update_profile` in `crud/user.py`).

## CRUD delete — single `delete`, soft-by-default + optional `hard`

There is exactly **one** delete entrypoint per entity, named `<entity>_delete` (never `soft_delete` + a separate `delete`). When the entity supports soft delete, the signature is `<entity>_delete(id, *, hard: bool = False)` — **soft is the default** (sets `deleted_at`/`revoked_at`), `hard=True` issues a physical `DELETE`. Entities without a soft-delete column (ephemeral rows like `Session`) have plain hard `<entity>_delete_by_<key>` and no `hard` param.

**Why:** one name for "remove this row" — the caller picks the strength via a flag, instead of memorizing which of two similarly-named functions is destructive.

**How to apply:** canonical shape — `user_delete(user_id, *, hard=False)`, `token_delete(public_id, *, hard=False)` (soft path = `revoked_at`). Bulk cleanups keyed by FK (`token_delete_by_user`) stay separate and hard. Always trace the `hard=True` path against derived state (see *Hard delete breaks aggregates*).

## CRUD owns its session

Since 2026-05-08 every CRUD function in the project owns its own session.

**Why:** previously ~155 call sites wrapped every CRUD call with `async with session_scope() as s:` + passing `s` inside, adding 5–6 lines of boilerplate per simple list-of-ids read. Multi-step "atomic" transactions (`vacancy_scraper.scrape_vacancy`, `probe.probe_all`, `ticker._tick_once`) existed but on review each had a fallback (idempotent upsert + retry tick; uptime audit is best-effort; lock TTL cleans up). Atomicity was convenience, not load-bearing → decomposed to eventually consistent.

**How to apply:**
- Writing a new CRUD function: signature **without** `session: AsyncSession`, body starts with `async with session_scope() as s:`. Returns detached ORM rows or plain types.
- Mutating functions accept **id**, not an ORM instance: `update_status(id, status)`, `update(id, **fields) -> row | None`, `delete(id) -> bool`. This removes the temptation to "get in one session → mutate in another".
- Timestamp columns use **Python-side** `default=utc_now`/`onupdate=utc_now` (never `func.now()` — see `docs/platform/dates.md`), so their value is known client-side and needs no refresh. But if a column has a genuinely **server-side** recomputation (`server_default`/`server_onupdate` / a SQL-expression `onupdate`) and the function returns a row after UPDATE — **`await s.refresh(row)` is required** before exiting scope. Otherwise accessing the attribute outside raises `DetachedInstanceError` (SQLAlchemy marks such columns expired regardless of `expire_on_commit=False`).
- `expire_on_commit=False` is already set on the factory (`src/core/database/runtime.py`), no separate configuration needed.
- FastAPI endpoints call CRUD directly without `Depends(get_session)`. The dependency is removed from runtime — do not reintroduce it.
- Multi-step operations in services = multiple sequential CRUD calls. If splitting breaks an invariant that cannot be compensated, write a domain transactional function that **internally** opens `session_scope` and writes `INSERT/UPDATE` directly, bypassing CRUD. Atomicity cannot be threaded through CRUD.
- CRUD tests do not need a `session` fixture: a `db` fixture that calls `init_database(Settings()) → create_all → close_database` is enough. Tests call `await crud.x(...)` directly without `await session.commit()`.

**Read-only ORM queries also go through CRUD.** If a function reads a row from a specific table — its place is in `<module>/crud/<entity>.py`, not inline `select(...)` in api/services. Example: `core/crud/lock.py:get(key)` — the only channel for reading `CoreLockRow` outside `core/locks/lock.py`.

**Pitfall:** during refactors it is easy to miss a call site if the path has no tests. Real example — `browser_scraper.py` wrapped `create_if_missing(db, ...)` in `session_scope`; after the signature changed to by-id this became a TypeError, but the path (streaming recommended vacancies via Qt browser) has no test coverage. After any CRUD signature change, grep all call sites — not just tests.

## Actor-split CRUD — `crud/<entity>.py` vs `crud/own_<entity>.py`

When an entity has operations from two distinct actors — split `crud/` into two files:

- `crud/<entity>.py` — admin/infra half: creates, lists, deletes, and any operation an admin performs *on someone else's* record. Also actor-neutral lookups used by both sides (e.g. `user_get_by_email` for login).
- `crud/own_<entity>.py` — self-surface: reads and edits the user performs *on their own* record only. Exactly two typical operations: `user_get_self(user_id)` (principal resolve by session/token) and `user_update_profile_self(...)` with a hardcoded column set. Methods carry a **`_self` suffix** so the self-actor is visible in the name (not only in the file / alias) and never reads as its admin twin.

The file boundary makes privilege escalation physically impossible: a self-route that imports only `own_<entity>` cannot accidentally reach `user_delete` or any other admin op — there is no such symbol in scope. Code review would otherwise need to catch this manually on every diff.

**Why:** the motivating pattern — `get(user_id)` lived in `crud/user.py` alongside `soft_delete` and `create`. A self-route that needed `get` would import the whole admin file, silently acquiring access to destructive operations. After the split, the self-paths import only `own_user`; `crud/user.py` is never reachable from them.

**How to apply:**
- Split only when the actor boundary is real: most entities are admin-only (no self-surface) → a single `crud/<entity>.py` is correct.
- A `User` entity is the canonical case: `crud/user.py` owns `user_create`/`user_list`/`user_delete`/`user_update_password_hash` (+ admin twins `user_get`/`user_update_profile`); `crud/own_user.py` owns `user_get_self`/`user_update_profile_self`.
- In services, alias imports explicitly: `from ... crud import own_user as own_user_crud` and `from ... crud import user as user_crud` — the alias makes the actor visible at every call site.
- `own_<entity>.py` must never import from `<entity>.py`; the dependency is one-way only.

## DTO layout — split files, role suffix by kind

When DTOs of different kinds accumulate in a module, split into files: `dto/rows.py` — table record mappings, `dto/api.py` — external API contracts (a single-DTO module like `page_scraper/dto.py` needs no split until a second kind appears).

Name DTOs by their **role**, and let the suffix disambiguate from the same-named ORM model:

- **`<Entity>Row`** — a thin Pydantic mirror of one DB row (`model_config = {"from_attributes": True}`). The `Row` suffix is **required**: the CRUD returns the ORM model (`User`) and the API layer imports both the model and its DTO in the same module — without the suffix the two classes collide (`User` vs `User`). This is the project-wide standard (`UserRow`, …).
- **`<Entity>View`** — a composed/enriched API representation (joins, derived fields, nested abilities), not a 1:1 row mirror. E.g. `UserView` / `TokenView` / `AbilityView`.
- **no suffix** — shapes whose role is already obvious from the name: `*Request` / `*Response` / `*Page` / `*Dicts` / `*Detail` / `*Batch` / `*Stats`, and pure value objects / dataclasses that have no ORM twin (`dto/principal.py` `User`).

**Why:** the earlier "no suffixes at all" rule (chat 2026-05-08) never held in code — every module mirroring a table uses `Row`, because the DTO and its ORM model share the entity name and must coexist in one import scope. The suffix encodes the role (`Row` = raw row, `View` = composed) and prevents the name clash; dropping it would force import aliases everywhere.

**How to apply:** new DTO that maps a table row 1:1 → `<Entity>Row` in `dto/rows.py` (or `dto/api.py` for API-only modules). Enriched/composed payload → `<Entity>View`. Request/response/page wrappers → no suffix. Never reuse the bare ORM model name for a DTO in a module that imports the model.

## Free-form text field naming — `description` vs `note`

A `description` column answers exactly one question: **"what is this entity / what is it responsible for"** — the entity's own purpose. It defines the row's role, not a remark about it. Use `description` *only* for that.

A human annotation/remark *about* a particular row — an operator's side-note that is not part of the entity's definition — is **not** a `description`. Name it `note` (or `notes`). Do not overload `description` for annotations.

**Why:** the codebase already splits this way and the line was blurring. `description` is the entity's self-definition: `tagging_rule.description`, `agent_config.description`, `mcp_server.description` (each describes what that rule/agent/server *is*). Annotations use other names (e.g. an operator `note`). Fixing the rule keeps `description` meaning one thing project-wide instead of drifting into a catch-all comment field.

**How to apply:**
- Field defines the entity's purpose/role → `description`.
- Field is an operator's free-form remark on the row → `note` (singular preferred). `comment` exists in some legacy tables but prefer `note` for new code.
- Never use `description` for a remark, nor `note` for the entity's self-definition.
- "About self" prose on a person stays domain-specific: e.g. a `User.bio` column.

## Minimal indirection

When designing APIs the user prefers minimal indirection: start with "by the book" (service classes, separate models/crud/service layers), then ruthlessly collapse layers through discussion.

Concrete iterations in the `core/locks` task (2026-05-04):
- `Lease` context-manager → removed in favour of runner-cleanup in `finally`.
- `LockService(app)` → removed, only `Lock` with classmethod `acquire` remains.
- `Lock.acquire(app, ...)` → `Lock.acquire(...)` without `app`, after moving `session_scope` to module-global.
- Three files (`models/locks.py`, `crud/locks.py`, `locks/lock.py`) → one `locks/lock.py`.
- `ttl: timedelta` → `ttl: int` (seconds).
- Multi-app DB support via `app.state` → removed after verifying it's not actually used in the project.

**Why:** with ~50 modules ahead, the user wants the core to be simple and readable. Extra layers are justified only by a real usage scenario.

**How to apply:** when designing core components, propose the minimal form first. If adding a service/abstraction feels tempting — first ask whether there is a real scenario with two+ implementations. Before keeping a layer for "multi-X" reasons, grep to confirm that "X" is actually used in two or more places. No service classes without a real scenario.

## API URL style — hyphens, not underscores

Use hyphens (kebab-case) in HTTP URL paths, not underscores.

**Why:** REST convention; underscores in URLs are less readable and inconsistent with web standards.

**How to apply:** when setting `prefix=` in `app.include_router(...)` and `BASE` constants in frontend `api.ts`, always use kebab-case (e.g. `/api/my-module`, not `/api/my_module`). Internal Python identifiers (module `name`, table names, Python variables) keep underscores — only the HTTP path segment changes.

## Hard delete breaks aggregates

When reviewing code that maintains derived state (thread builders, indices, denormalized aggregates, change-feed consumers), always think through **both** delete paths the CRUD exposes:

- soft delete (`deleted_at` set) — usually bumps `processed_at` or similar, so change-feed-style consumers pick it up.
- hard delete (`hard=True`, raw SQL, `ON DELETE CASCADE`) — row is gone, no timestamp to bump, no change event. Consumers that key off "what changed since X" miss it entirely.

If the derived state depends on the parent row's existence (e.g. "thread has at least one message"), a periodic orphan sweep is mandatory — change-feed updates alone are insufficient.

**Why:** a real change-feed incident. A thread builder's `update()` queried `list_changed_thread_ids_since(threshold)`, which relies on `processed_at > threshold`. Messages deleted via raw SQL → no `processed_at` bump → threads stayed visible with stale aggregates. The hard path was missed in initial review even though `delete(id, hard=True)` has the same effect and was right there in the signature.

**How to apply:**
- When reading/writing any "list changed since X" / cache-invalidation / re-aggregation logic, explicitly trace what happens under `delete(..., hard=True)` and raw SQL `DELETE`, not just the soft-delete happy path.
- Pair every change-feed-driven rebuild with a periodic orphan sweep (`live_parents - live_children_parent_ids`).
- In tests for such code, include at least one case that deletes rows via raw SQL or `hard=True`, not just `crud.delete()`.

## Versioning pattern — three axes for derived rows

Any derived/processed record (tagging, scoring, filtering, parsing) carries three independent version fields. Re-processing fires on a change in **any** of them.

| Field | Meaning | Type | Source |
|---|---|---|---|
| `parser_version` | fingerprint of the **algorithm** (code) | `String(22)`, hex, `server_default=""` | `PARSER_VERSION = dict_hash({"version": "X.Y"})` — module-level constant |
| `config_version` | fingerprint of the **runtime config** read from DB (prompts, dictionaries, enabled flags, filter rows) | `String(22)`, hex, `server_default=""` | `dict_hash({...})` computed from DB rows at runtime |
| `content_hash` | snapshot of the **source data's** `content_hash` at the moment of processing | `String(22)`, hex, `server_default=""` | copy of `Source.content_hash` (`text_hash`, SHA-256 hex) |

**Re-process trigger:**

```
WHERE
    parser_version  IS DISTINCT FROM :current_parser_version
 OR config_version  IS DISTINCT FROM :current_config_version
 OR content_hash    IS DISTINCT FROM source.content_hash
```

Each axis answers a different question:
- `parser_version` changed → we shipped new code, redo everything we own.
- `config_version` changed → user edited prompts/rules in admin UI, redo affected rows.
- `content_hash` changed → upstream source mutated, only that row needs redo.

**Existing usages (non-uniform names):**
- `headhunter_match` — `generator_model` + `generator_hash` (legacy nomenclature). Maps to `parser_version` + `config_version`.

For **new** modules: pick the code-axis name by what it versions — `parser_version` only if it's really a parser, else `agent_version` / `generator_version` / etc. Config axis: `config_version` (or a domain name like `tagger_version`). Always `content_hash` for source data.

**Manual-override fields:** fields populated by humans (e.g. `research_tags`) live on the same row but are NOT invalidated by version bumps — they survive re-processing. The processor must preserve them on upsert (mark in a `_NO_UPDATE` frozenset).

**Why:** prior modules invented ad-hoc names (`filter_version`, `generator_hash`) and conflated config with code into a single hash. Splitting axes makes selective re-processing cheap and observable — a `config_version` mismatch tells you which rows are stale because the user changed settings, not because we shipped code.

**How to apply:** when modeling any derived table (insights/results/scores), add all three columns from day one. Even if one axis is currently trivial (no config), keep the column so the schema doesn't need a later migration when config arrives. Source `content_hash` is `String(22)` SHA-256 hex via `text_hash`; algorithm/config fingerprints are `String(22)` hex via `dict_hash`. (2026-06-05: `content_hash`/`fingerprint_dict` renamed `text_hash`/`dict_hash`, unified on SHA-256 hexdigest[:22] = 88-bit; the old 16-hex version columns widened 16→22.)
