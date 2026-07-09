# core_semaphore — documentation

Reference documents cited repeatedly. Update when the described subject changes — stale descriptions are worse than no documentation.

## Rules

The **on-demand reference tier** (read when working in the area; length is free). This is the home for *all* structured/multi-section prose — including anything promoted out of `AGENTS/memory/` when a memory entry outgrew ≤3 lines. See *Memory vs Docs* in `agent-primary.md` for the boundary.

The primary navigation axis is **modules** — each module has a per-module hub at `docs/<module>/INDEX.md`; cross-cutting code-shape conventions live in `docs/conventions/` (backend / frontend / db-migrations), and behavioral rules + atomic gotchas live in `AGENTS/memory/MEMORY.md` (the always-loaded router that points here).

- Create a file in `AGENTS/docs/` for reference information that needs to be cited repeatedly, or for any topic that needs sections/headings.
- One topic, one home: docs own the detail; `AGENTS/memory/` may carry at most a one-line pointer here. Don't restate a doc's content in memory.
- Update it when the described subject changes — stale descriptions are worse than no documentation.

## Inventory

### Core platform

#### [platform/module-system.md](platform/module-system.md) — module registration and lifecycle

Complete reference for the module system.

- `Module` ABC: declarative attributes, four lifecycle hooks
- `create_app` build sequence + lifespan order
- Config (env, build-time) vs Settings (DB, runtime)
- How to register a new module; current module table

#### [platform/module-state.md](platform/module-state.md) — generic per-module state store

`core_modules_state` — arbitrary runtime KV for module code (import cursors, counters, markers).

- `Module.store` / `module_store(code)` accessor; CRUD `crud/module_state.py`; JSONB `value`
- When to use vs the settings store (internal state vs operator config)

#### [platform/architecture.md](platform/architecture.md) — module platform

How the app is composed from modules.

- `Module` ABC + `create_app([modules, ...], config)`
- `apps/<name>/` layout and key principles
- API conventions: `DatetimeGMT5` required in all response schemas

#### [platform/router.md](platform/router.md) — zones, route registration, guards

**Read before adding routes or auth checks.** Implemented reference (code in `src/core/router/`,
`create_app`).

- Zones (`internal` active; `api`/`webhook` stub routers; `mcp` servers mounted at `/mcp/<code>` via `mount_mcp_servers` — mechanism present, no module currently ships one); module gives `internal_router`/`internal_router_prefix` (+ declarative `mcp_servers`/`mcp_token_resolver`), `create_app` mounts
- `@guard("kind", *args)` label (params, built-in `allow_all`/`deny_all`; a module may contribute more guard kinds via `Module.guards`, AND); `zone_guard` execution + default-on + `request.state.user`
- `GuardRegistry` (`add`/`has`/`resolve`), declarative `Module.guards`, build-time `validate_guard_rules`
- middleware ≠ guard; `SERVER_ENABLED` flag + `app.py` CLI (`--backend`/`--worker`); how to add a guard kind

#### [platform/api-zones.md](platform/api-zones.md) — API request zones (original design)

Historical design note. **Superseded by [platform/router.md](platform/router.md)** for current behaviour (this file
predates the registry/`@guard` implementation and still describes the rejected `set_guard` seam).

- /internal (SPA + auth, session cookie) / /api (external, token+scope) / /webhook (signature)
- declarative per-zone routers on `Module`, mounted with the zone's auth centrally

#### [platform/locks.md](platform/locks.md) — distributed locks

Locks used across scheduler tasks.

- `CoreLock.acquire`/`release`/`extend`
- Behavior inside scheduler tasks

#### [platform/loggers.md](platform/loggers.md) — logging channels

Channel-based logging system: one channel = one file.

- `get_logger` / tee / proxy mechanics
- Channel table (all active channels)
- Bootstrap, test substitution

#### [core-scheduler README](../../src/core/scheduler/README.md) — scheduler internals

Lives next to the code in `src/core/scheduler/`.

- Task registration, `TaskContext`, lifecycle
- `Ticker`/runner internals

#### [platform/migrations.md](platform/migrations.md) — Alembic revision naming

**Read before creating a new migration.**

- Filename: `<prefix><NN>_<slug>.py` (e.g. `i05_admins_add_synced_at.py`)
- `revision` string must equal the filename basename; `down_revision` chains to the previous in the same module
- Anti-pattern: 12-char autogen IDs interspersed with module letters — unreadable, hide ordering
- Canonical example: `src/core/migrations/versions/`

#### [platform/database.md](platform/database.md) — DB & migrations working rules

**Read before touching DB models, tables, columns, or migrations.**

- Table naming: explicit name dependency — child tables prefix the full parent name (`<parent>_<child>`, e.g. `my_module_items` under `my_module`); same for index/constraint names
- Timestamps: `TIMESTAMP(precision=0)` (no microseconds); re-fetch rows in tests before comparing `updated_at`
- Migration naming: `<prefix><NN>_<slug>.py`, no autogen IDs (gist; full rules in `platform/migrations.md`)
- (Hub for DB conventions not captured by code; complements `platform/migrations.md` / `platform/dates.md` / `platform/soft-delete.md`)

#### [platform/soft-delete.md](platform/soft-delete.md) — soft delete pattern

Project-wide logical deletion convention.

- `SoftDeleteMixin` — adds `deleted_at` column; usage and placement rules
- CRUD conventions: filtering, `soft_delete()`, upsert un-delete
- Migration template and when to use soft vs hard delete
- Table of all entities where soft delete is applied

#### `src/core/utils/hashing.py` — deterministic fingerprints

`dict_hash(params: dict[str, str]) -> str` — SHA-256 [:22] of `key=value` pairs sorted by key.
Use wherever a short stable hash of a config/parameter set is needed (filter versions, builder versions, etc.).
`text_hash(text: str | None) -> str` — SHA-256 [:22] of a string (`None == ""`); change-detection hash of content.
Both emit 22 lowercase-hex chars (88-bit). (Renamed 2026-06-05 from `fingerprint_dict`/`content_hash`; old output was 16-hex / BLAKE2b-base64url.)

#### [platform/overview.md](platform/overview.md) — project overview & stack

`core_semaphore` extracted from `hh-support-agent`; runs **headless from source** (no binary; Qt GUI + MCP apps removed).

- Stack: Vue3 + Vuetify4 + Pinia + Vite → `static/` (committed); FastAPI + uvicorn via `src/app.py` (`--backend`/`--worker`/`migrate`); pnpm
- Ports + `APP_ENV` (`dev`/`test`/`prod`)
- Two run scenarios: dev (Vite + embedded worker) / prod (nginx + split processes)

#### [platform/run-configs.md](platform/run-configs.md) — IDE run configurations

`dev/.run/*.run.xml` taxonomy, `<category>-<name>` verb standard.

- Categories: `run` (one-shot, second token = process role) / `watch` / `build` / `test` / `sync` / `tool` / `group`
- Per-config table; role axis (`server-worker`/`server`/`worker`); compounds = Vite + backend
- Hot-reload covers both surfaces (uvicorn `--reload` vs `watchfiles` for standalone worker)

#### [mcp/INDEX.md](mcp/INDEX.md) — MCP server surface

Infrastructure for exposing a module **as an MCP server** at `/mcp/<code>` (standalone `fastmcp` fork). Mechanism + introspection exist; no registered module currently ships one.

- Declarative registration: `Module.mcp_servers` (code→`mcp_server` ctor fn, lazy-import to keep fastmcp out of the worker); `src/core/mcp/` = sole fastmcp boundary
- Auth: agnostic `McpServerTokenVerifier` + injected `Module.mcp_token_resolver` (supplied by a future auth module); fork API gotchas (mount `path="/"`)
- https-only in prod (plain http → CF 522 by design)

---

### Conventions

Cross-cutting code-shape rules the user enforces — read before writing or refactoring in that layer.

#### [conventions/code-style.md](conventions/code-style.md) — self-documenting code (read first)

- Code explains itself via **structure and names**, not comments; unclear logic → **extract and name it**
- No label/enumeration comments (`# Tier 1 …`) or reference/prose comments in code; comments justify the **why**, never the **what**
- Descriptive identifiers (`conversation_id`, not `cid`); worked example = the `outdated.py` priority-tier rewrite

#### [conventions/backend.md](conventions/backend.md) — backend Python conventions

- CRUD: one file per entity (`crud/<entity>.py` mirrors `models/`), CRUD owns its session (no `Depends(get_session)`, by-id mutators), descriptive `<entity>_<verb>_by_<key>` names
- DTO layout: `dto/rows.py` (table records) + `dto/api.py` (API contracts); role suffix by kind — `<Entity>Row` (thin row mirror, disambiguates from same-named ORM model), `<Entity>View` (composed), no suffix for `*Request`/`*Response`/`*Page`/`*Detail`
- Field change = 3 layers in one edit (migration + ORM model + DTO); minimal indirection (collapse layers, no service classes without a real scenario); API URL kebab-case
- Hard delete breaks aggregates (change-feed misses raw/`hard=True` DELETE → pair with orphan sweep); versioning pattern = 3 axes (`parser_version`/`config_version`/`content_hash`)

#### [conventions/frontend.md](conventions/frontend.md) — frontend Vue/Vuetify conventions

- `VDateInput` (labs), never `VTextField type=date` (permanent spinner bug)
- `VBtnToggle` for ≤4-option enums in dialogs (not `VSelect`); `VBtnGroup`/`VBtnToggle` `size` is NOT inherited — set on each `<VBtn>`
- `PageLayout` owns scroll under `meta.scroll` — no nested `h-100`/`overflow:auto` wrapper

#### [conventions/db-migrations.md](conventions/db-migrations.md) — DB & migration conventions

- Column order/naming: `enabled` right after the PK, UI ordering field named `sort` (not `sort_order`)
- Cross-module FK ⇒ `depends_on` the **migration that creates** the referenced table (never another branch's head — overlap `RevisionError` wedges the DB)

---

### Frontend

Everything for working in `web/src/`. The stack is Vuetify 4 + Vue 3 + Vite + TypeScript; conventions around theming, page composition, icons, and Vuetify quirks live below.

#### [frontend/rules.md](frontend/rules.md) — stack, layout, theme, Vuetify gotchas

One-stop reference for `web/src/`; deeper CSS recipes in [`frontend/vuetify-css-patterns.md`](frontend/vuetify-css-patterns.md).

- Stack (Vuetify 4.x, Vue 3.5, Tabler icons — no MDI) + `web/src/` layout (App/layout/features/plugins/styles)
- Page patterns: content directly in `<PageLayout>` (no double `pa-6`); KeepAlive → **pair `onMounted` + `onActivated`** for data loading; single-root view rule (dialogs INSIDE `<PageLayout>`)
- Color tokens single-sourced as hex (`main.scss` ↔ `vuetify.ts`, no `oklch()`); theme architecture + Vuetify 4 deprecated props / CSS gotchas (`@layer`, `VMain` height, `VSwitch` SASS vars)

#### [frontend/design-system.md](frontend/design-system.md) — showcase pages & coverage

Status of the `/design-system/` showcase.

- 23 showcase pages (tokens → world-map) registered in `routes.ts` + `nav.ts`; `date-pickers` covers all 4 date/time scenarios
- Design-system patterns + the non-obvious `main.scss` overrides the demos depend on (date-picker selection, time-picker accent, default tooltip)
- Next candidates: Snackbar/Alert, Tabs, Chips, Menu

#### [frontend/api-client.md](frontend/api-client.md) — internal API client

**Read before making any backend call.** `web/src/api/client/internal.ts` is the single way
the frontend talks to our backend — use it for **every** request, never raw `fetch`/`axios`.

- `internalApi.get/post/put/patch/del` over the `/internal` zone (prefix owned by the client)
- Typed `ApiError` from the backend `{ error, code?, fields? }` envelope; network/abort normalised too
- Per-feature `api.ts` convention; security posture (relative paths only, no foreign origin); `VITE_API_BASE` dev mode

#### [frontend/route-meta.md](frontend/route-meta.md) — route `meta` parameters

**Read before adding routes.** Reference for every `route.meta` key (`web/src/router/meta.ts`).

- Layout keys only (local site, no auth): `scroll` / `padding` (read by `PageLayout`), `fullscreen` / `transition` (read by `App.vue`)
- `router/guards.ts` only arms the progress bar, dismisses orphaned tooltips, records nav history

#### [frontend/layout.md](frontend/layout.md) — layout layer (shell, page wrappers)

Layout primitives and Vuetify 4 plumbing.

- `src/layout/` — `AppSidebar`, `PageHeader`, `PageLayout` (toolbar/content/footer slots)
- `route.meta.scroll` and `route.meta.padding` — content-zone behaviour
- Vuetify 4 height chain (`v-application__wrap` → `VMain.main-content` → `PageLayout`)
- Icon system: `@tabler/icons-vue`, `TablerIcon` type, Vuetify icon set aliases

#### [frontend/vuetify-css-patterns.md](frontend/vuetify-css-patterns.md) — Vuetify 4 CSS overrides

Practical recipes for overriding Vuetify 4 styles.

- `@layer` cascade and why our unlayered CSS wins
- `VBtn` sizing, `VBtnGroup`/`VBtnToggle` border-radius and height
- `VNumberInput`, `VSwitch`, `VField` variants — gotchas and fixes

#### [frontend/markdown-rendering.md](frontend/markdown-rendering.md) — markdown rendering (client side)

Client-side rendering of markdown for chat/LLM content.

- `MarkdownRenderer.vue` — marked + DOMPurify; `compact` prop
- CSS contract: all elements carry `md-*` classes, styled via `:deep()` in consumers

#### [platform/dates.md](platform/dates.md) — date formatting (frontend section)

Frontend half of the dates contract: `@/shared/utils/date`.

- Why never `DateTime.fromSQL(s)` without `{ zone: 'utc' }`
- `fmtDate` / `fmtDateTime` / `fmtTime` / `fmtRelative` / `fmtDuration`
- Standard table date cell pattern (date + relative caption)

#### [frontend/validators.md](frontend/validators.md) — Vuetify rule factories

Input validators for `:rules="[…]"`.

- Contract: factory → `(v) => true | string`; custom message via factory arg
- Why factories (closures over parameters), why empty values pass by default
- Current set: `isSlug` (a-z / 0-9 / `-` / `_`)
- Rules for adding new validators

#### Shared utilities in `web/src/shared/utils/`

- `date.ts` — date formatters (see [`platform/dates.md`](platform/dates.md))
- `validators.ts` — Vuetify rule factories (see [`frontend/validators.md`](frontend/validators.md))

---

### Cross-cutting contracts (backend ↔ frontend)

#### [frontend/i18n.md](frontend/i18n.md) — multi-language support (draft, in progress)

Conventions for translating the UI (ru + en).

- `vue-i18n` layout: `web/src/locales/` (common) + `web/src/features/<feature>/locales/` (per-feature)
- Key naming: `<feature>.<bucket>.<role>` (`settings.nav`, `administration.users.page.title`)
- Backend returns error codes (`{ error: { code, params } }`), frontend translates via `tError`
- Russian is primary; English falls back to Russian; missing keys render the key itself
- What is **not** done yet: Vuetify locale adapter, `AppError` handler, switcher UI, bulk migration


#### [platform/dates.md](platform/dates.md) — datetime conventions (full reference)

**Always read if working with dates** — migrations, ORM models, DB entities, API schemas, frontend date display, data processing with timestamps.

- Backend: naive UTC storage, `utc_now()`, `DatetimeUTCStr` serialization
- **Migrations/models: always `postgresql.TIMESTAMP(precision=0)`, never `sa.TIMESTAMP()`**
- Frontend: `@/shared/utils/date` functions, standard table cell pattern
- `synced_at` — external-data import timestamp, incremental sync cursor
- `processed_at` — internal processing timestamp (filters, parsers, builders)
- `ingested_at` — derived-layer upstream cursor

#### [frontend/markdown-rendering.md](frontend/markdown-rendering.md) — full rendering pipeline

Client-side markdown rendering and its CSS contract.

- `MarkdownRenderer.vue` — client-side (marked + DOMPurify), prop `compact`
- CSS contract: all elements carry `md-*` classes, styled via `:deep()` in consumers

---

### Workflow

#### [workflow/testing.md](workflow/testing.md) — running tests (params + agent workflow)

How to run the suite and which flags to pass.

- Markers (`pure`/`db`/`heavy`/`live`), default filter (`pure`+`db`), type/area flags, in-memory SQLite (no DB pool)
- Agent pattern: inner loop = `--core` + touched `--module` (no heavy/live); `--all` only for final checks; `heavy` needs `TEST_PG_DSN`
- In-memory DB swap (`DB_PATH=:memory:` + StaticPool), per-test fresh engine, live creds (`LIVE_*`)

#### [workflow/debugging.md](workflow/debugging.md) — debugging

Where to look when things break.

- Dev ports, browser DevTools (claude-in-chrome / F12), API/Swagger
- Common problems

#### [workflow/benches.md](workflow/benches.md) — local benches

How to use the `bench/` benches.

- Layout: `bench/<module>/<area>/` with `constants.py`, `run_*.py`, `stats_*.py`, `tmp/`
- Conventions, how to run, existing benches
