---
title: Research groups (reference table + attachment)
date: 2026-08-27
status: in-work
description: "New reference table research_group (title / sort / icon / description); a research attaches to at most one group. Design phase — field structure only, no code yet."
tags: [research, database, frontend]
---

## Task

«Добавить группировку исследований. Простая таблица-справочник: название, сортировка (больше =
выше), иконка (наборы tabler), краткое описание. Любое исследование можно прикрепить к группе;
исследование — максимум в одной группе. Продумать структуру полей.»

(The user announced two items; only the first is stated so far.)

## Context

`research_index` is currently a flat list ordered by `updated_at` — 41 researches in dev and
growing, with no user-facing partitioning. Groups are a human-facing shelf, not part of the
research pipeline.

## Design (proposed, not yet approved)

`research_group` — sibling reference table in the `research` module:
`code` (PK, 22-hex, presentation prefix `GROUP@`) · `title` String(128) · `description` String(512)
NOT NULL `''` · `icon` String(64) NOT NULL `''` (tabler kebab name) · `sort` Integer NOT NULL 0
(**bigger = higher** → `ORDER BY sort DESC, title ASC`) · `created_at` / `updated_at`.

Attachment = a single nullable FK column on `research_index`:
`group_code String(25) NULL → research_group.code ON DELETE SET NULL` + index. One group per
research, no link table.

Two forward-only migrations: `rem_006_group` (create table) + `rem_007_research_group_code`
(add column + index).

### Findings that shape the design

- **Icons cannot be a free string today.** `@tabler/icons-vue` is imported as *components*
  everywhere (`web/src/plugins/vuetify.ts`, `shared/nav.ts`); the Vuetify icon set renders an
  unknown string icon as literal text (`<span class="v-icon__unknown">`). The package is 71 MB /
  ~5900 icons, so a runtime `import *` resolver is out. ⇒ a curated allowlist registry
  (name → component, explicit imports) is required; the picker offers exactly that set.
- **`ON DELETE SET NULL` will not fire on sqlite** (FK enforcement is off) — the manual-cascade
  pattern already used in `research_delete` applies: `group_delete` must `UPDATE research_index SET
  group_code = NULL` itself.
- **`group_code` is nullable** — an intentional exception to the module's "free-text is NOT NULL
  default `''`" policy: `''` is not a valid FK target.

### Decisions

- **MCP surface: yes, but later.** The agent will get groups (`groups_list` + optional `group_code`
  on research create/update) as a follow-up step, discussed separately. The schema is agent-ready
  as designed — no extra columns needed for it.

### Open questions (asked, awaiting answer)

1. `enabled` flag on a group — needed, or is delete + sort enough?
2. Default undeletable group vs `NULL` = ungrouped (recommendation given: `NULL`, no seeded row).

### Icon palette — 120 curated names

Produced by three sub-agents over disjoint themes (science/tech, business/life, abstract markers),
then merged and **verified name-by-name against the installed package** (`@tabler/icons-vue@3.44.0`,
6147 outline+filled components enumerated from `dist/esm/icons`): 120 rows, 0 duplicates, 0 missing.
No `*Filled` / `*Off` / `IconBrand*`. Scratch copies:
`runtime/dev/tmp/tabler-icon-names.txt` (full package list) + `runtime/dev/tmp/group-icons-120.txt`.

Science & tech (40): Atom, MathFunction, MathPi, Flask, TestPipe, Microscope, Dna, Virus, Vaccine,
Stethoscope, Planet, Satellite, Mountain, World, Code, Terminal2, GitBranch, Bug, Robot, BinaryTree,
Database, ChartHistogram, ChartPie, Server, CloudComputing, Network, ShieldLock, Key, Fingerprint,
Cpu, DeviceLaptop, Bolt, Battery, SolarPanel, BuildingFactory2, Cube, VectorBezier, RulerMeasure,
Gauge, Scale.

Business & life (45): Briefcase, TargetArrow, PresentationAnalytics, Coins, PigMoney, BuildingBank,
ShoppingCart, BuildingStore, Tag, Speakerphone, Gavel, License, School, Books, News, Microphone,
Messages, Mail, Palette, Brush, Music, Camera, Feather, Notebook, Article, BuildingSkyscraper,
Hammer, Crane, TruckDelivery, Ship, Plane, Compass, ToolsKitchen2, Wheat, Tractor, Barbell,
BallFootball, Home, Tree, Paw, Flower, DeviceGamepad2, MasksTheater, UsersGroup, BuildingCastle.

Abstract markers (35): Folder, Box, FileText, Notes, Book2, Bookmark, Star, Flag, Pin, Archive,
Search, Telescope, Bulb, Brain, Puzzle, Trophy, Rocket, Calendar, Clock, Hourglass, Route, Timeline,
Sitemap, Tools, Hexagon, Diamond, Cloud, Sun, MoodSmile, Heart, GridDots, LayersLinked, Package,
Stack2, Category.

Stored `icon` value = the kebab form without the `Icon` prefix (`building-factory-2`), matching
tabler.io's own naming so a name can be looked up on the site as-is.

## What was done

**Step 1 — the table itself** (link column and CRUD are separate steps, per the user's sequencing):

- `constants.py` — `GROUP_CODE_PREFIX = "GROUP"` (eighth presentation prefix) + `GROUP_TITLE_MAX`
  128 / `GROUP_DESCRIPTION_MAX` 512 / `GROUP_ICON_MAX` 64 / **`GROUP_SORT_DEFAULT = 500`**
  (non-zero start so a new group can be moved both up and down without renumbering neighbours).
- `models/group.py` — `ResearchGroup`; registered in `models/__init__.py`.
- `migrations/versions/rem_006_group.py` — `CREATE TABLE research_group`, `down_revision =
  rem_005_source_document`.

Applied and verified: `migrate upgrade` → head `rem_006_group`, `migrate check` clean, dev
`PRAGMA table_info(research_group)` matches the model (7 columns, `sort` DDL default `500`,
`description`/`icon` default `''`). No dev backend of this checkout was running, so no restart was
needed. Tests `--core --module=research` — **361 passed**. No tests added yet: the table has no
behaviour until CRUD lands.

**Step 2 — the link column:**

- `models/research.py` — `group_code` (nullable, FK `fk_research_index_group_code` →
  `research_group.code`, `ON DELETE SET NULL`), placed after `code`; docstring explains why this is
  the module's only nullable ref.
- `migrations/versions/rem_007_research_group_code.py` — `batch_alter_table` add column + FK, then
  `ix_research_index_group_code`.

Verified: head `rem_007_research_group_code`, `migrate check` clean, `PRAGMA foreign_key_list
(research_index)` shows the FK with `SET NULL`, index present, `foreign_key_check` empty,
`integrity_check` ok, child tables still reference the rebuilt `research_index`, data intact
(41 / 291 / 232). Tests `--core --module=research --module=web_search` — **420 passed**.

**Step 3 — the six methods** (no MCP layer yet, per the user's scope):

- `crud/group.py` — `group_code()` (`random_hash()`), `group_create` / `group_get` / `group_list` /
  `group_update` / `group_delete`. Same shape as `crud/area.py`: each function owns its session,
  oversized text is soft-clipped by code points, `None` means "don't touch" on update.
  `group_delete` **detaches** researches (`UPDATE research_index SET group_code = NULL`) instead of
  cascading — the group is a shelf, deleting it must not delete the work.
- `icons.py` — `GROUP_ICONS` (120 kebab names, thematic order) + `group_icons()`. Every name was
  converted PascalCase→kebab programmatically and checked against
  `@tabler/icons/icons/outline/*.svg` (5093 files): 120/120 matched, 0 mismatches.
- Tests: `tests/modules/research/test_group.py` (13 `db` tests — defaults, unique codes, sort
  ordering incl. the equal-`sort` tie-break, partial update, `sort=0` not swallowed by a truthiness
  check, code-point clipping on Cyrillic, delete detaches vs. keeps other groups, missing-row
  returns) + `tests/modules/research/test_group_icons.py` (3 `pure` tests — dedup/size snapshot,
  kebab shape, `group_icons()` returns a copy).

`--module=research` 91 passed · `--core --module=research --module=web_search` **436 passed** ·
`--unmarked` empty (every new test carries exactly one type marker).

The icon palette moved to the **backend** (it was going to be frontend-only in the original design)
because the user's method list includes `group_icons` — so the canonical set is served, and the
frontend keeps only the mirror map name → component for rendering.

**Step 4 — MCP surface** (six tools, mirroring the CRUD):

- `dto.py` — `GroupCode = prefixed(GROUP_CODE_PREFIX)`, `GroupCreated` (code only, like the other
  creates) and `GroupRow` (code/title/description/icon/sort/updated_at — a shelf has no body, so
  scan and detail are the same set).
- `mcp/group.py` — `group_create` / `group_list` / `group_get` / `group_update` / `group_delete` /
  `group_icons`; registered first in `mcp/__init__.py` (groups sit above researches).
- `_INSTRUCTIONS` — `GROUP@` added to the CODES paragraph, a Groups block in the tool reference,
  and the section header **`TOOLS BY GROUP` → `TOOL REFERENCE`**: with a `group` entity now in the
  domain, "by group" read as "grouped by group".
  The block states plainly that deleting a group keeps its researches and that **filing a research
  onto a shelf has no tool yet** — otherwise the agent hunts for one.
- Tests `tests/modules/research/test_group_mcp.py` (10 `db` tests through the fastmcp client:
  tagged codes round-trip, defaults, display order, partial update, delete true-then-false,
  `ToolError` on missing, palette identity, all six tools registered).

Surface is now **29 tools** (was 23), no duplicate names. `--module=research` 101 passed ·
`--core --module=research --module=web_search` **446 passed** · `--unmarked` empty.

**Step 5 — `group_code` + `group_name` on the research surface:**

- `crud/research.py` — joined reads `research_get_with_group` / `research_list_with_group`
  returning `(research, group | None)` (the `source_document` join pattern); `research_create` /
  `research_update` take `group_code`, where **`""` detaches** (`NULL`) and `None` means "keep".
  Plain `research_get` stays bare — four call sites use it purely as an existence check.
- `dto.py` — `group_code: GroupCode | None` + `group_name: str` on `ResearchScan` (→ inherited by
  `ResearchView`) and `ResearchListItem`, placed right after `description`; builders `group_fields`
  and `research_list_item`.
- `mcp/research.py` — `_resolve_group` validates an unknown `GROUP@` up front (mirrors
  `area_create`'s research check) instead of letting a dangling ref reach the DB, where SQLite
  would accept it silently.
- Instructions/docstrings actualised: `research_create` / `research_update` document `group_code`
  as optional cosmetic filing ("skip it unless the user asked"), `research_get` explains that
  `group_name` is derived and renaming happens via `group_update`, and the Groups block replaced
  its earlier "there is no tool for filing" line.
- Tests: two existing contract tests in `test_research.py` updated to the new key set (they lock
  the exact response shape — that is their job), +10 in `test_group_mcp.py` covering file-on-create,
  ungrouped pair, **rename propagation** (proves `group_name` is joined, not copied), move between
  shelves, `""` unshelves, omitted keeps, list rows, unknown group on create/update → `ToolError`,
  and group deletion leaving the research intact but unshelved.

29 tools, no duplicates. `--module=research` 111 passed ·
`--core --module=research --module=web_search` **456 passed**.

`group_name` is **not** stored on the research: a copied title would drift the moment a shelf is
renamed, which is exactly what one of the new tests asserts against.

**Step 6 — verification pass + free-mode coverage:**

New `tests/modules/research/test_group_flow.py` (13 `db` tests) covering what the per-tool contract
tests can't: **ungrouped researches survive `research_list`** (the join is outer — an inner one
would silently hide every unfiled research), group deletion unshelving several researches at once,
a group outliving deletion of a research it held, `body_add` not knocking a research off its shelf,
bare vs `GROUP@`-tagged codes both accepted, an off-palette icon stored as given (the palette is a
picker hint, not a validator), overlong fields trimmed rather than rejected, re-ordering shelves via
`sort` (and `sort=0` not swallowed), the search pipeline unaffected by grouping, a free-form session
(create → file → rename → move → unshelve → delete) ending consistent, and a stale group code
rejected after its shelf is gone.

`--module=research` 124 passed · `uv run pytest --all` **495 passed, 3 skipped** (the three skips
are the known Postgres-only `heavy` migration tests) · `--unmarked` empty · `migrate check` clean.

**Live check against the running dev backend** (`:22040`, hot-reloaded): MCP over HTTP reports 29
tools incl. all six `group_*`; `research_list` returns the real 41 rows carrying `group_code` /
`group_name`; `group_icons` returns 120 names. Then a reversible write loop through the live server
— create group → create research filed under it → rename the group (name propagated) → unshelve →
delete both. Dev DB verified back to its exact prior state (0 groups, 41 researches, 0 shelved,
`max(updated_at)` unchanged → no existing research touched), `foreign_key_check` empty,
`integrity_check` ok.

**Known gaps (deliberate, not defects):** the web API (`/research`) does not expose the group yet —
`ResearchRow` / `ResearchDetail` are untouched; the frontend has no icon registry, so `group_icons`
names cannot render in the SPA yet; there is no "researches of a group" tool (filter `research_list`
client-side).

**Step 7 — registries + group fields on the research model (web layer):**

Ambiguous instruction ("добавляй реестры и новые поля в модель исследования"); the clarifying
question went unanswered, so it was read as *the icon registry + group fields in the web contracts*,
explicitly **not** new tools/endpoints and **not** UI display. Assumption stated to the user.

- `crud/research.py` — `research_list_paged` now returns `(research, group | None)` (same
  `_with_group()` outer join, moved up next to `_filtered`).
- `dto.py` — `group_code` / `group_name` added to `ResearchListRow` and `ResearchDetail` (after
  `description`, as in the MCP DTOs). `ResearchRow` stays a pure row mirror — `group_name` is not a
  column, so it is filled by the shared `group_fields()` builder instead.
- `api.py` — `/researches` and `/researches/{code}` fill the pair; detail switched to
  `research_get_with_group`.
- `web/src/features/research/constants/groupIcons.ts` — **the frontend half of the icon contract**:
  120 explicit tabler imports, `groupIcon(name)` → component with `IconFolder` fallback,
  `groupIconNames()`. Generated, then verified: 120 unique imports all present in the package,
  keys identical to the backend palette **in the same order**, no duplicate components.
- `web/src/features/research/api.ts` — `ResearchListRow` / `ResearchDetail` type mirrors updated.
- Tests: new `tests/modules/research/test_api.py` (6 `db` tests — group in list and detail,
  ungrouped rows survive the join, counters intact, missing → 404) and a `pure` test in
  `test_group_icons.py` that **parses the TS registry** and asserts it covers exactly the backend
  palette — the one seam between the two languages, where drift silently degrades to a folder icon.

`vue-tsc --noEmit` exit 0. `--module=research` 131 passed · `uv run pytest --all`
**502 passed, 3 skipped**. Live read-only check: `/internal/research/researches` on the dev backend
returns all 41 rows with `group_code` / `group_name` alongside the existing counters.

**Collision fixed on the way:** adding `tests/modules/research/test_api.py` broke collection with
`import file mismatch` — `tests/modules/**` were not packages, so it clashed with
`tests/modules/web_search/test_api.py` (a latent trap: `test_crud.py` would have been next). Added
`__init__.py` to `tests/modules/` and all six module test dirs, matching `tests/core` /
`tests/apps`, which were already packages.

**Still not done (deliberate):** the SPA does not display the group anywhere yet (no picker, no
group page, `web/dist` not rebuilt), and there are no group write endpoints in the web API.

**Step 8 — group routes + list filter:**

Routes (`api.py`) — the module's **first write surface**, a deliberate exception to its "content is
written by MCP, not these handlers" stance, recorded in the module docstring: a shelf is the user's
filing, not the agent's output.

- `GET /groups`, `POST /groups` (201), `GET|PUT|DELETE /groups/{code}` (delete → 204, researches
  survive as ungrouped).
- `PUT /researches/{code}/group` — deliberately narrow: it moves a research between shelves and
  cannot touch title/description/body, so the read-only stance holds for research content.
- `GET /researches?group_code=…` — filter; the empty string means "only the unshelved". A string,
  not `None`: in a query parameter `None` is indistinguishable from "not passed".
- Bodies `GroupBody` / `ResearchGroupBody` with pydantic length limits (empty title → 422). Unknown
  group/research → 404 on every verb, including the list filter.

Filter plumbed through the CRUD once — `_filtered(stmt, query=…, group_code=…)` with the same
tri-state as `research_update` (`None` all / `""` ungrouped / code) — and reused by
`research_list_paged`, `research_count` and `research_list_with_group`.

MCP `research_list(group_code?)` gained the same filter (an updated tool, no new one), validating an
unknown shelf up front; instructions line updated.

Frontend client (`web/src/features/research/api.ts`): `GroupRow` / `GroupBody` types, `listGroups`,
`getGroup`, `createGroup`, `updateGroup`, `deleteGroup`, `setResearchGroup`, plus `group_code` in
`ListResearchesParams`. No UI yet — client layer only.

Tests: +16 in `test_api.py` (group CRUD incl. 201/204/422/404-on-every-verb, filing and unfiling,
both codes validated, filter by shelf / by unshelved / unknown → 404) and +6 in `test_group_flow.py`
(MCP filter: by shelf, unshelved, unfiltered, bare code, unknown → `ToolError`, empty shelf).

`--module=research` 151 passed · `uv run pytest --all` **522 passed, 3 skipped** · `--unmarked`
empty · `vue-tsc --noEmit` exit 0. Live check on `:22040` (reversible): created a group over HTTP,
filtered the list by it (0) and by the unshelved (41), deleted it (204) — dev DB back to 0 groups /
41 researches / `max(updated_at)` unchanged.

**Step 9 — `GROUP@` in the reference resolver:**

`crud/references.py` knew five prefixes, so a `GROUP@` code written into a body rendered as a raw
code instead of the shelf's name. Added `GROUP_CODE_PREFIX`, and collapsed the five near-identical
per-type blocks into a `_TITLE_COLUMN` table (`prefix → (model, title column)`) driving one loop —
adding a type is now one row. The source-document branch stays separate on purpose: its title is
not its own column, it comes from `web_search_page` via join.

`resolve_labels` had **no tests at all**; added `tests/modules/research/test_references.py` (4 `db`
tests): a group code resolves, all six types resolve in one call (incl. the two whose "title" is
borrowed — a search shows its query text, a source shows its page title), unknown / untagged /
unknown-prefix codes are skipped, empty input returns empty.

`--module=research` 155 passed · `uv run pytest --all` **526 passed, 3 skipped**. Live check on
`:22040`: `POST /references` with a fresh `GROUP@` code returned its title; the throwaway group was
deleted afterwards (dev DB back to 0 groups).

Per the user's call: the research doc hub (item 4) and the `DB_AUTO_MIGRATE` flip (item 5) are
deliberately **not** done.

**Step 10 — first UI: the groups page:**

- `views/GroupsView.vue` + `stores/groups.store.ts` — cards (icon + title + 2-line clamped
  description) in the `/connectors` grid idiom; click opens the group.
- Route `/research/groups` + nav entry «Группы исследований» (`IconCategory`) under «Данные», and
  locales `research.nav_groups` / `research.group.*`.
- **The group address is the research-list address with a `GROUP@` code**:
  `/research/researches/GROUP@<hash>`, per the user's requirement. Implemented as a
  prefix-dispatched route — `path: '/research/researches/:code(GROUP@.*)'` → `ResearchesView`,
  registered **before** `/research/researches/:code` → `ResearchView` (equal route score, first
  registered wins). Same list view under two addresses instead of a duplicated table.
- `ResearchesView` takes the shelf from the route (`store.groupCode` + header title/description +
  back arrow to `/research/groups`), reloading on `onActivated` and on an in-place param change.
  `groupCode` is page context, not a filter chip: `clearFilters` leaves it alone.

Verified in an isolated browser on Vite `:22041` and, after `vite build`, on the backend `:22040`:
the cards render, a card opens `…/GROUP@…` showing that shelf's researches (2 of 2) with the group
name and icon in the header, a `RESEARCH@` code still opens the research detail (the regex route
does not hijack it), the unfiltered list returns all 41, console clean. `vue-tsc` 0,
`--module=research` 155 passed. `web/dist` rebuilt (committed artifact).

**Dev-DB data I created and left in place** (say the word and I'll delete it): four sample groups —
Экология города / Фронтенд / Инфраструктура / Разное — and two existing researches filed under
«Экология города» (`RESEARCH@ef8a7d2f258de68b188bda`, `RESEARCH@ac7bcfb520ca700afb1fea`); their
`updated_at` changed as a result.

**Step 11 — nav order, card counter, extracted table:**

- Nav: new section «Исследования» with **Группы above Исследования**; Веб-поиск moved under a
  «Данные» section of its own. Labels shortened to «Группы» / «Исследования».
- Card counter: `crud/research.py::research_count_by_group_codes` (one `GROUP BY`, mirroring
  `area_count_by_research_codes`) + `GroupListRow(GroupRow)` with `research_count`, filled by
  `GET /groups`. The counter is **web-only** — MCP keeps returning the plain `GroupRow`, so agent
  calls don't pay for a number only the interface reads. Rendered as a KPI-style footer pinned to
  the card bottom (static caption «Исследований», no plural machinery — vue-i18n has no Russian
  plural rules configured here).
- `components/ResearchesTable.vue` — the registry table extracted from `ResearchesView` (data table
  + pagination, driven by the shared store, optional `emptyText`). Used by both the registry page
  and the group page.
- `views/GroupView.vue` — real group detail (card header with icon/description, back arrow, refresh)
  embedding `ResearchesTable`; the `GROUP@` route now points here instead of reusing
  `ResearchesView`. Leaving the group resets `store.groupCode` on the registry page's activation.
- Tests +2 (`test_api.py`): counts per group in the list, count drops after unfiling.

`--module=research` 157 · `uv run pytest --all` **528 passed, 3 skipped** · `vue-tsc` 0 ·
`web/dist` rebuilt. Verified in the isolated browser: counters (2/0/0/0), group page with the
shared table, registry page unfiltered after returning, console clean.

**Step 12 — automatic «Без группы» shelf (last in the list):**

No DB row and no new endpoint — the pseudo-shelf is **the existing code scheme with an empty hash**:
`GROUP@`. The backend's `strip_prefix` turns it into `""`, which its filters already read as "only
the unfiled ones", so `/research/researches/GROUP@` routes, filters and paginates through exactly
the same path as a real shelf.

- `api.ts` — `UNGROUPED_CODE = 'GROUP@'` with the reasoning; `groups.store` fetches its counter in
  parallel with the list (`listResearches({group_code: UNGROUPED_CODE, page_size: 1}).total`).
- `GroupsView` — the auto card is rendered after the loop (always last), muted and with a dashed
  icon frame so it doesn't read as a user-made shelf.
- `GroupView` — an empty hash means "don't fetch a group row": title/description come from the
  dictionary, the icon is the fallback, and the table filters the same way. Also switched both
  views to `SectionError` (the error component that landed in the meantime) instead of a raw
  `VAlert`.
- Locale `research.group.ungrouped.*`.
- Test: `GET /researches?group_code=GROUP@` returns only the unfiled ones (the empty-hash contract
  now has a regression test, not just an implementation detail).

`--module=research` 158 · `uv run pytest --all` **529 passed, 3 skipped** · `vue-tsc` 0 ·
`web/dist` rebuilt. Live: the card shows 39, its page lists those 39, console clean.

**Step 13 — re-read the frontend after the parallel API-client port:**

The client was replaced in parallel (`2026-08-27-frontend-api-client-errors-routing`, in-work):
`api/client/createClient.ts` (timeout, `redirect: 'manual'`, JSON-contract check, `retryAfter`,
`shouldReport` → `onError`), `internal.ts` as a zone config, `errorText`, `useToasts` + `ToastStack`,
`useShellError` + `ErrorScreen`, route `name` + `meta.title`, prefix-based nav highlight.

Checked the group code against it and fixed one real conflict:

- **Double report.** The client toasts every failure `shouldReport` doesn't silence (only
  401/403/422 are silent), while the group pages also render `SectionError`. A missing shelf showed
  the in-section state *and* a toast of the same sentence. Fixed by passing **`report: false`** on
  section reads (`listGroups`, the ungrouped counter, `getGroup`) — the doctrine ported by that task
  says a section-read refusal is a state inside the section, and the caller that shows it must
  silence the client. `listResearches`/`listGroups`/`getGroup` now take an optional `RequestOptions`
  passthrough instead of hardcoding the policy.
- Verified conformant: per-feature `api.ts` with a local `QueryValue` (same as `web_search`), stores
  keeping the raw error for `SectionError`/`errorText`, `del` → 204 → `undefined`, zone-relative
  paths only.

Still open, and **not** mine to fix (that task's territory): nav highlight — a group page lives at
`/research/researches/GROUP@…`, so prefix matching lights «Исследования», not «Группы»; the sidebar
still navigates with `router.push` instead of `:to`, so nav items are not real links; the same
double-report exists on other read pages that use `SectionError` without `report: false`.

`vue-tsc` 0 · `uv run pytest --all` **529 passed, 3 skipped** · `web/dist` rebuilt · toast no longer
duplicates the section error (checked live).

**Step 14 — the `%40` bug (group cards opened the wrong page):**

Clicking a group card navigated to `/research/researches/GROUP%400a21…`, which the route regex
`:code(GROUP@.*)` does **not** match — the address fell through to `/research/researches/:code`
and rendered the research view with «Исследование не найдено». Direct URL entry worked, which is
why earlier checks passed: the bug lived only on the click path.

Cause: `encodeURIComponent(code)` in `openGroup`. `@` is a legal path character (RFC 3986 pchar),
Vue Router does not encode it itself, and pre-encoding hid it from the matcher.

Fix: no encoding, and the card became a **link** (`:to`) instead of a click handler — matching the
sidebar, which the parallel task had already converted, so cards now support middle-click and
"open in new tab". Verified by clicking every card, including «Без группы» (`GROUP@`, empty hash).

Then walked every detail page in the browser — research, area, search, source, note — plus the
group→row→research path and the unfiltered registry: all render, console clean. `vue-tsc` 0,
`uv run pytest --all` **529 passed, 3 skipped**, `web/dist` rebuilt.

**Step 15 — `IconPicker` in the design system:**

- `web/src/components/IconPicker.vue` — search on top + a scrollable tray of icon tiles.
  Generic on purpose: the set (`icons`) and the name→component resolver (`resolve`) are props, not
  an import of the research registry — a runtime lookup over `@tabler/icons-vue` would pull ~6000
  components into the bundle, and there may be more than one palette later. Search matches the
  **code** (`building-factory-2`), the same string that goes into the DB, so no second 120-line
  dictionary is needed. `v-model` = the picked code; keyboard focus ring; `aria-pressed` on tiles.
- Colours from the existing tokens rather than literal white/grey: panel = `--surface-sunken` +
  `--border-sunken` (the project's "recessed tray" role, same as kanban columns), tiles =
  `--surface` + `--border-soft`. In the light theme that renders exactly as asked — grey panel,
  white tiles — and in dark it keeps the same figure/ground relation instead of glaring white.
- Showcase page `views/design-system/controls/IconPickerView.vue` (three demos: default, empty
  `v-model`, custom `height`), registered in `router/design-system.ts` + the index page + locales
  (`design-system.index.page.icon-picker`, `page.icon-picker`, `section.icon-picker`), plus
  `common.icon_picker.*` for the component's own strings. The demo runs on the real 120-code
  research palette — a made-up list would demo scrolling and search on data the app doesn't have.

Checked in the isolated browser: 120 tiles, search «building» → 5/120, selection highlighted,
scroll clipped by `height`, light theme verified separately, console clean. `vue-tsc` 0,
`uv run pytest --all` **536 passed, 3 skipped**, `web/dist` rebuilt.

**Step 16 — card menu + edit / delete dialogs:**

Backend — deletion gained a **strategy for the researches** (the shelf can hold work, so its removal
must ask): `GROUP_RESEARCHES_{DETACH,MOVE,DELETE}` in constants, `group_delete(code, *, researches,
move_to)` in CRUD, `DELETE /groups/{code}?researches=…&move_to=…` in the API. The `delete` strategy
loops `research_delete` per research instead of re-implementing the cascade — that cascade is
described once, and a second copy would be a second thing to remember. Defaults stay `detach`, so
the MCP tool's behaviour and its docstring are unchanged. Validation: `move` without a target or
into itself → 400, unknown target → 404, unknown strategy → 422 (all four have tests; +8 in
`test_api.py`, 181 in the module).

Frontend, on the design system's own dialog stack (`AppDialog` — header / body / action bar, three
widths):

- Three-dot `VMenu` in the card's top-right: Изменить (pencil) / Удалить (trash, error-coloured).
  The card is a link, so the button carries `@click.stop.prevent` — otherwise the menu click would
  open the shelf.
- `GroupFormDialog` — title / description / **icon via `IconPicker`** (with a preview in the shelf's
  own tile style) / position. Holds its own copy of the values and syncs on open, so an edit never
  touches the list until saved and Cancel leaves it untouched. Failures render **in the dialog**
  (`report: false`) — the window stays open with the typed text instead of dropping a toast
  somewhere else.
- `GroupDeleteDialog` — empty shelf gets a plain question; a non-empty one gets the three-way choice
  with the target `VSelect` for «переместить» (confirm disabled until one is picked) and a red
  caveat under «удалить». Selection resets to the mildest option on every open — a remembered
  «delete» would be a loaded gun.

Checked live end to end: menu opens without navigating, edit dialog prefilled (icon `tree`,
sort 900), delete dialog shows 2-research choice + select + warning, and an actual delete of the
empty «Разное» removed it from the list. `vue-tsc` 0, `uv run pytest --all` **552 passed, 3
skipped**, `web/dist` rebuilt, console clean.

**Step 17 — «Новая группа» in the header:**

Primary button to the right of «Обновить». Creation reuses `GroupFormDialog` rather than getting a
second component: the fields, the limits and the icon picker are identical, and the only differences
are the heading and which endpoint is called (`group === null` ⇒ create). Two forms would drift
apart at the first new column.

New shelves start at position **500**, shown in the field rather than left to the endpoint's
default — position drives ordering, so the user should see where the shelf will land before saving.
The constant mirrors `GROUP_SORT_DEFAULT`.

Verified live: the button opens an empty «Новая группа», Добавить is disabled until a title is
typed, a created shelf appears in the list with its icon and `0 исследований`; the test shelf was
deleted afterwards. `vue-tsc` 0, `uv run pytest --all` **552 passed, 3 skipped**, `web/dist` rebuilt.

**Dev-DB note:** the four sample shelves are gone — the user removed them while testing (the two
researches that sat on «Экология города» came back ungrouped, 41 total, content intact). My own
throwaway «Проверка создания» was deleted right after the check, so the dev DB is back to 0 groups.

**Step 18 — picker and dialog polish (by eye, in the browser):**

- `IconPicker`: the status line under the tray is gone (picked code + `120 / 120`) — a person picks
  a drawing, not a string, and the choice is already visible as the highlighted tile. The search
  field **moved inside the grey tray**, above the tiles, and stays put while the tiles scroll; only
  the tile area carries the `height`. Unused locale keys removed with it.
- `GroupFormDialog`: field order is now **название → описание → позиция → иконка** — what it is,
  then where it sits, then how it looks. The picker goes last because it is the tallest block and
  nothing should jump above it while scrolling. Counters under the text fields dropped
  (`hide-details`) — they added a second baseline under every field and made the gaps read as
  uneven; the limits are still enforced by `maxlength` and by the backend.
- Spacing: one 16px step between fields, 6px between the «Иконка» label and its tray (a label
  belongs to its field, not to the block above), preview tile 34→28px so it doesn't outweigh the
  label, tray height 160px = three rows plus the edge of a fourth — the clipped row **is** the
  scroll affordance, a flush height would read as "that's all there is".

Checked in both themes: light renders the described grey panel with white tiles and a white search
field; dark keeps the same figure/ground. `vue-tsc` 0, `uv run pytest --all` **552 passed, 3
skipped**, `web/dist` rebuilt, console clean. The shelf created for the check was deleted — dev DB
back to 0 groups.

**Step 19 — picker anatomy: search · rule · scroll zone:**

The tray is now three explicit bands instead of a padded stack: the search strip, a rule across the
full width of the panel, and the scrolling tile zone. Padding moved from the panel onto the bands —
that is what lets the rule run edge to edge (the same role the rule under a dialog header plays).
The panel clips its corners (`overflow: hidden`), the search and the rule stay put, only tiles move.

Checked in the dialog and in the design-system demo, both themes, console clean. `vue-tsc` 0,
`uv run pytest --all` **558 passed, 3 skipped** (count grew — the parallel task added sorting tests),
`web/dist` rebuilt, throwaway shelf deleted.

## Problems

**Half-applied migration on SQLite.** The first version of `rem_007` used a plain `op.add_column`
with an inline `ForeignKey`. Alembic's SQLite dialect has no `ALTER … ADD CONSTRAINT` and raises
`NotImplementedError` — but its DDL is non-transactional, so the `ADD COLUMN` had already
committed. Result: column present, index missing, revision unstamped, and every subsequent
`migrate upgrade` failing on `duplicate column name`.

Made worse by a second factor: `.env` has `DB_AUTO_MIGRATE=true` and a dev backend
(`--backend --worker`, pid 2533560, started earlier by the `urb-research-dev` MCP stdio shim) was
live — hot-reload made it apply each new migration file *concurrently* with the CLI run.

Fixed by dropping the leftover column (`ALTER TABLE research_index DROP COLUMN group_code`, all 41
rows were NULL — verified before dropping) and rewriting the migration with `batch_alter_table`,
which copy-and-moves the table on SQLite so the FK actually lands, and is a plain `ALTER` on
PostgreSQL. Written up in [`docs/conventions/db-migrations.md`](../docs/conventions/db-migrations.md)
→ *Adding a FK column ⇒ `batch_alter_table`*.

## Result

Files added: `src/modules/research/models/group.py`,
`src/modules/research/migrations/versions/rem_006_group.py`,
`src/modules/research/migrations/versions/rem_007_research_group_code.py`.
Files changed: `src/modules/research/constants.py`, `src/modules/research/models/__init__.py`,
`src/modules/research/models/research.py`, `AGENTS/docs/conventions/db-migrations.md`.

Next steps: `crud/group.py` (code generator `random_hash()`, create/get/list/update/delete with
manual detach of researches) + `group_code` in `crud/research.py` → DTO/API → frontend → MCP.
