# DB & migration conventions

Read this before writing Alembic migrations or modeling a new table — column ordering/naming, and cross-module FK dependency rules.

## Table column order & naming

1. **`enabled` goes right after identifier columns** (`id` / `code` / natural PK), before any payload fields (label, description, prompt_fragment, etc.).
2. **Use `sort` as the column name**, not `sort_order`. Integer, default `0`, higher means later (or define per-table).

**Why:** scanning a row left-to-right, "is this row active at all" is the first signal you need after knowing which row it is. Putting `enabled` next to the PK makes it visible in `SELECT * FROM ...` output without horizontal scrolling, and matches how the field is mentally grouped — "row identity + row aliveness" form the row's metadata header. `sort_order` is redundant: the column is already in a row context, the `_order` suffix adds no information.

**How to apply:**
- Schema layouts (migrations, models, DTO row docs) order columns as: `id` / `code` → `enabled` → payload (label, description, …) → `sort` (UI hint) → `created_at` / `updated_at` / `deleted_at` (lifecycle).
- Name the UI ordering field `sort` (integer). Never `sort_order`, `order`, `position`, `display_order`.

## Migration filename / revision-id naming

Filename stem **==** the Alembic `revision` id, in the form **`<abbr>m_<NNN>_<description>`**:

- **`<abbr>m`** — the module abbreviation with a trailing **`m`** (marks it as a *module* migration). `my_module` → `mmm`.
- **`<NNN>`** — zero-padded sequence number within the module's chain: `001`, `002`, …
- **`<description>`** — what the migration does. The **first** migration is named after the **first table it creates**, never `init` — e.g. `mmm_001_files` (creates `my_module_files`), `mmm_002_files_refs` (creates `my_module_files_refs`).

**Rules:**
- One table per migration (a table-creating migration is then a non-head once its successor lands → safe cross-module `depends_on` target; see below).
- Keep the id ≤ 32 chars (`alembic_version.version_num` is `varchar(32)` — a longer id raises `StringDataRightTruncationError` at upgrade).
- Renaming a revision id ⇒ update every `down_revision`/`depends_on` that points at it (other modules included) **and** re-stamp the dev `alembic_version` row.

This is the canonical scheme for new migrations; some older module chains predated it (form `<prefix><NN>_…`) and were left as-is.

## Cross-module FK → depends_on

Each module has its own independent Alembic revision chain (own `version_locations`). Order **within** a chain comes from `down_revision`; order **between** chains is undefined unless a revision declares `depends_on`.

**Why:** a migration in module A that creates a table with a FK to a table owned by module B will fail with `UndefinedTableError` if Alembic happens to run A before B. The order is stable-but-arbitrary (by revision id) and can shift when migrations are added/renamed — a latent floating bug.

**How to apply:** any cross-module FK ⇒ set `depends_on` to the **migration that creates the referenced table** (always a non-head, since it has descendants), NOT to the branch head. Example: `module_b`'s `bm_002_links.py` (FK `module_b_links.item_id → module_a_items.id`) sets `depends_on = "am_001_items"` — the migration that creates `module_a_items` — not `am_006_archive` (module_a's head).

**When the referenced object is created by the *newest* migration (a head):** you can't `depends_on` it directly (it's a head → overlap, see below). Split the producing migration so the part that creates the referenced object becomes a **non-head**: e.g. migration `aN` adds the column + backfill, a follow-up `aN+1` adds the index. Now `aN` (column creator) is buried under `aN+1` (the new branch head), and the dependent cross-module migration safely sets `depends_on = "aN"`. Real case: `am_004_status` (column) + `am_005_status_index` (index) split so `module_b`'s `bm_003_backfill` (backfills from `module_a_items.status`) can `depends_on = "am_004_status"`. **Gotcha with `DB_AUTO_MIGRATE=true` in dev:** hot-reload may apply the *pre-split* migration (column **and** index in one), recording it as a head with the index physically present. After splitting, the dev DB is then both wedged (head you now depend on) **and** has a duplicate index. Recover: temporarily `depends_on=None`, `DROP INDEX IF EXISTS` the orphan (via `tools/dev-query.sh`), `migrate upgrade` to apply the follow-up, then restore `depends_on`.

**Why never depend on another branch's head:** `AlembicRunner._do_upgrade` runs `command.upgrade(cfg, "heads")`. Each module is its own branch, so after applying, `alembic_version` records one head row per module — including both the depended-on row and the dependent row. If the dependent (`bm_002_links`) `depends_on` a row that is *itself a head* (`am_006_archive`), then a recorded head is a dependency-ancestor of another recorded head, and Alembic's overlap check (`_get_ancestor_nodes(current_revisions, check=True, include_dependencies=True)` in `_collect_upgrade_revisions`) raises `RevisionError: Requested revision X overlaps with other requested revisions Y` — **even just reading the current state**, so the app can't start and the DB is wedged. Depending on a non-head (the table-creating migration) keeps the dependency-ancestor out of the head set, so no overlap at read or at `upgrade heads`. This bit once: hot-reload (uvicorn `--reload`) applied `bm_002_links` with `depends_on="am_006_archive"`, recording both as heads; fixed by repointing `depends_on` to `am_001_items` (no `alembic_version` surgery needed).
