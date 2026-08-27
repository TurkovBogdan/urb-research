---
title: Group filter and a sort picker on the researches list
date: 2026-08-27
status: completed
description: "Added a group filter to /research/researches and replaced the single newest/oldest toggle with a sort-field select plus a direction button; the backend list learned a sort_by whitelist covering the table's counters."
tags: [research, frontend, api]
---

## Task

«1. Добавь фильтр по группе исследований. 2. Кнопка "сначала новые" → выпадающий список
сортировки и рядом кнопка-иконка направления. По коду и логике посмотри, по каким полям можно
сортировать, и сделай».

## What can be sorted (the audit the task asked for)

The list row carries: title + description, four counters (areas / searches / kept / filtered) and
`updated_at`; `created_at` was already the hidden default sort key.

| Key | Source | Notes |
|---|---|---|
| `created_at` | column | default, the previous "сначала новые" |
| `updated_at` | column | the date the table actually shows |
| `title` | column | alphabetical; sqlite BINARY collation puts Latin before Cyrillic |
| `area_count` | correlated subquery | counters are computed per page in Python, so ORDER BY needs SQL |
| `query_count` | correlated subquery | |
| `document_kept` | correlated subquery | `status = kept` |
| `document_filtered` | correlated subquery | `status = filtered` |

Deliberately not offered: **group**. It is not a column of the table, and on the shelf page the
whole list is one shelf — sorting by it would order nothing visible. `description` / `body` are
prose, `code` is opaque.

## What was done

**Backend**

- `crud/research.py` — `_children_count(model, *conditions)` builds a scalar subquery correlated on
  `research_code`, so a counter can be used straight in `ORDER BY`. `RESEARCH_SORT_COLUMNS` is the
  whitelist (7 keys above) + `RESEARCH_SORT_DEFAULT`; `research_list_paged` takes `sort_by` and
  falls back to `created_at` on an unknown key, `code` stays the tiebreak in the same direction.
  Same shape as the existing `QUERY_SORT_COLUMNS` in `web_search` — the module already had a
  precedent, so nothing new was invented.
- `api.py` — `GET /researches` takes `sort_by`; the group filter (`group_code`, `""` = ungrouped)
  already existed from the groups work and needed no change.

**Frontend**

- `api.ts` — `RESEARCH_SORT_FIELDS` (order = order of the dropdown) + `ResearchSortBy`, `sort_by`
  in `ListResearchesParams`.
- `researches.store.ts` — new `sortBy`, and **`groupFilter` separate from `groupCode`**: the store
  is shared with the shelf page, where `groupCode` is page *context* from the address. Context wins
  over filter, they never coexist (different pages), and only the filter is cleared by
  `clearFilters` / counted in `hasActiveFilters`. Reusing one ref would have made the registry page
  drop the user's choice on every `onActivated` (which clears the context).
- `ResearchesView.vue` — group select (Все группы / Без группы / полки, loaded from
  `useGroupsStore` once), sort select, icon button toggling direction with a tooltip; a closable
  chip for the chosen shelf. «Без группы» reuses `UNGROUPED_CODE` (`GROUP@`) — the same pseudo-code
  the shelf route uses, which the backend strips to `""`.
- Narrow screens: search and each select take a full row, the direction button stays beside the
  sort select (it is meaningless on its own).
- `locales/ru.json` — `sort.label/asc/desc/by.*` (replacing `sort.newest`/`sort.oldest`),
  `research.filter.group`/`group_all`.

## Verification

- `tests/modules/research/test_api.py` +6 tests: title asc/desc, created_at vs updated_at as
  independent keys (dates written directly — the columns are `precision=0`, so rows created in the
  same second would be ordered by the random-code tiebreak), area_count, kept vs filtered as
  separate subqueries, a counter sort under the group filter (total stays right), and an unknown
  `sort_by` falling back to the default instead of erroring.
- `uv run pytest --module=research` — 187 passed; full `uv run pytest -q` — **558 passed**.
- `vue-tsc --noEmit` 0, `pnpm --dir web build` ok, `web/dist` rebuilt.
- Live on :22040 (isolated browser context): all seven keys checked over the real dev DB via curl,
  then in the UI — dropdown lists the shelves, selecting one narrows the list to 1 and raises the
  chip, sort by area count flips correctly with the direction button, console clean.
- The live check created a throwaway group «Проверка фильтра», filed one research on it and then
  deleted the group with `researches=detach`; the dev DB is back to zero groups. Side effect left
  behind: that research's `updated_at` was bumped twice by the shelf writes.

## Follow-up: the research detail header

«Деталка исследования: название и описание в заголовок, в шапку кнопку обновления».

`ResearchView.vue` carried a static «Исследование» header and repeated the artifact's title +
description one size smaller in a card directly beneath it. Now the header **is** the artifact:
`title` = the research title (the static label stays as the fallback while loading, where the
skeleton covers it anyway), `description` = its description, and the `#actions` slot holds the
`updated_at` line next to a refresh button calling the same `reload()` that `onActivated` uses.
The top card is gone with its three now-unused styles — nothing else moved, sections below are
untouched.

Checked live on the same page (`RESEARCH@ac7bcf…`): header renders title / 3-line description /
date + button, refresh re-fetches without losing state, sections still read
«Основное тело / Области 6 / Поиски 8 / Источники / Заметки 5», console clean. `vue-tsc` 0,
`web/dist` rebuilt.

Not touched (same shape, out of the asked scope): `AreaView` / `NoteView` / `QueryView` /
`SourceView` still show a static header plus a title card.

## Follow-up 2: «Вводные» card + a 12-column detail layout

«Создаём карточку вводные, в неё описание и дату обновления, оформление как у других карточек.
Сделай вёрстку всей деталки колонками: 12, 8 контент, 4 правая колонка — вводная и тело это 8».

- **Вводные** — a normal section (`SectionHeader` + outlined `rounded="lg"` card, like every other
  block on the page) holding the description and the `updated_at` line. The header above keeps only
  the title and the refresh button, so the description moved out of it again.
- **Layout** — `.detail-grid` is `repeat(12, minmax(0, 1fr))`; `.detail-grid__main` spans 8,
  `.detail-grid__side` spans 4. Written as a plain CSS grid, not `VRow`/`VCol`: the project has
  **zero** uses of the Vuetify grid and 61 hand-written `grid-template-columns` — following the
  house style, and the 12-track grid the ask described is literally what this is.
- **Split** — left: Вводные → Основное тело → Источники; right: Области / Поиски / Заметки.
  Источники is a `VDataTable` with url cells, so it takes the wide column; the other three are
  compact link lists and read fine in a rail. That division was my call — the ask only pinned
  Вводные + тело to the 8.
- `min-width: 0` on both tracks is load-bearing: without it the sources table with long urls blows
  its own track out and the whole grid overflows the viewport.
- Collapse at ≤1099px (measured, not guessed: at 1680px the tracks come out 910 / 443 = ratio 2.05,
  exactly 8:4; below ~1100 the rail stops being a readable card).

Live at 1680×1000: two columns, sections land where intended, table 910px inside its track, no
horizontal overflow; at 1000px wide both tracks stack full-width, still no overflow; console clean.
`vue-tsc` 0, `web/dist` rebuilt.

⚠ Mid-check the dev backend on :22040 went down on its own (only the neighbouring stable instance
was left); it came back before my own start attempt bound the port, so that attempt died with
`Address already in use` and left nothing behind.

## Follow-up 3: reading typography for the description + a relative update date

- **Description reads as prose now.** `.brief-desc` restates the reading zone's own properties —
  `--font-reading`, `--reading-size`, `line-height: 1.7`, `--reading-measure`, `--text`,
  `text-wrap: pretty` — instead of the 14px muted interface grey. Measured live: the description
  and a `.md-body` paragraph now compute identically (Onest / 14px / 23.8px / same colour / same
  856px measure). The class has to sit on the `<p>` itself: `main.scss` styles bare `p` outside any
  cascade layer, so inheriting from an ancestor does not beat it — the same trap `MarkdownRenderer`
  documents. Not routed through the markdown pipeline: a description is a plain-text field, and
  parsing it would be a behaviour change, not a typography one.
- **Update date carries the distance**: «Обновлено: 27.08.2026 05:12 (38 минут назад)», composed in
  an `updatedAt` computed from the existing `fmtDateTime` + `fmtRelative`
  (`web/src/shared/utils/date.ts`) — the project's normalized relative formatter, ported from
  portal-mk2's `resources/js/utils/date.ts`. The relative half is dropped when it comes back empty,
  so a bad date never renders a dangling «()».

Verified live at 1680×760, console clean; `vue-tsc` 0, `web/dist` rebuilt.

## Follow-up 4: notes as cards, two columns under the body

«Заметки размещаем под основным телом, сортируем по убыванию даты обновления, каждую выводим
карточкой, в две колонки с выравниванием».

- Moved out of the right rail into the wide column, between Основное тело and Источники — the
  reading order becomes тело → выводы → сырьё.
- `.note-grid` is `repeat(2, minmax(0, 1fr))` — literally two, not `auto-fill`: notes are peers,
  and a row count that changes with the viewport would read as a difference in weight. One column
  below 720px.
- Card follows the `/research/groups` shelf card: `:to` link (so middle-click and «open in new tab»
  work — a click handler would kill both), title + kind badge in the header, description clamped to
  three lines with a reserved `min-height`, date pinned down with `margin-top: auto`. Those last two
  are what make neighbours in a row line up on both the text and the bottom edge.
- **Sort lives in the store**, not the CRUD: `note_list_by_research` feeds three callers, and its
  `created_at asc` is right for the two MCP ones — for an agent the notes are a work log. The page
  wants the freshest first, so `research-detail.store.ts` sorts a copy by `updated_at` descending.
  Dates arrive as SQL strings, whose lexicographic order is the chronological one.

Live on `RESEARCH@123aba428c8bc692b0dfee` (11 notes): grid computes `449px 449px`, two cards per
row at equal height, dates descending from 04:47 to 02:46, card is an `<a>` to
`/research/notes/NOTE@…` and navigates; sections read «Вводные / Основное тело / Заметки 11 /
Источники» left and «Области 6 / Поиски 32» right; console clean. `vue-tsc` 0, `web/dist` rebuilt,
full suite **562 passed**.

## Follow-up 5: drop the searches block from the research detail

«Из исследования (но не зоны) убери блок поисков».

A search belongs to an area, so listing every search of every area on the research page duplicated
what the area page already shows. Removed from `ResearchView` only — `AreaView` keeps its «Поиски»
section, and it reads from its own `area-detail.store` (fed by `listAreaQueries`), so nothing there
was touched.

Cleaned up what the removal orphaned: the `queries` computed in `research-detail.store.ts` (its only
consumer was that block — `AreaView` never used this store) and the locale keys
`research.research.detail.queries` / `no_queries`.

⚠ Left alone deliberately: `ResearchDetail.queries` still ships from the backend
(`api.py::get_research` → `dto.py`) and now has **no consumer** on the frontend. Dropping it is an
API-contract change, not a UI one — the user's call.

Live: research page sections are «Вводные / Основное тело / Заметки 11 / Источники» + «Области 6»
in the rail; area page still reads «Синтез раздела / Поиски 12 / Источники» with all 12 rows. No
raw i18n keys in either DOM, console clean. `vue-tsc` 0, `web/dist` rebuilt, full suite
**570 passed**.

## Follow-up 6: copy-the-code button on the group card

«В списке групп добавь левее трёх точек кнопку копирования кода группы».

- New composable `web/src/composables/useClipboard.ts` — clipboard write + the hidden-textarea
  fallback (under Qt WebEngine the async API rejects while the document is unfocused) + a
  self-clearing mark. The mark holds **the copied text**, not a boolean: in a list of cards a
  boolean would light up every row at once. A single-target button just asks
  `isCopied(its own value)`.
- `GroupsView` — icon button left of the ⋮ menu, `IconCopy` → `IconCheck` in the success colour for
  1.8 s, `title` flipping «Скопировать код» → «Код скопирован». `@click.stop.prevent` like the menu:
  the card is an `<a>`, so an unstopped click would navigate to the shelf. The pseudo-shelf
  «Без группы» gets no button — it has no row in the DB and therefore no code.
- Copies the **prefixed** code (`GROUP@16b75…`) — the form the MCP tools accept, which is the point
  of the button: shelves are made by hand and then have to be named to an agent.
- Locale: `research.group.card.copy` / `copied`.

Live on `GROUP@16b7506a5bd66271026c6b`: two buttons in the header at x=642 (copy) and x=682 (menu),
`writeText` receives exactly `GROUP@16b7506a5bd66271026c6b`, the check appears and clears after the
timeout, the page does not navigate, «Без группы» shows zero buttons; console clean. `vue-tsc` 0,
`web/dist` rebuilt.

⚠ `CodeBlock.vue` still carries its own inline copy + the same fallback and could now adopt the
composable — left alone on purpose: that file is entangled with the uncommitted markdown/typography
work, and touching it would mix this change into that task's diff.

### Card menu: the icon-to-label gap

Measured in the browser on the user's report: **32px** between the pencil/trash and its label — the
menu read as two unrelated columns. It is Vuetify's default `--v-list-prepend-gap`
(`$list-item-icon-margin-start`, sized for avatars, not 18px icons). The app sidebar already fixes
the same thing for itself (`main.scss` → `.v-list-item__spacer { width: 10px }`), but that override
is scoped to the drawer, so every other `VList` still gets 32.

Fixed on the menu with the documented knob rather than fighting the spacer:
`.group-card__menu-list { --v-list-prepend-gap: 10px }` — the sidebar's value, so the two read
alike. Verified: both items now measure 10.

⚠ Any other dropdown built on `VList` + `prepend-icon` outside the drawer still inherits 32px. A
global default (`plugins/vuetify.ts` → `VList`) would fix all of them at once but touches the
navigation too — not done here.

### Header buttons: tighter, smaller, quieter

«Между кнопками копирования и тремя точками сократи расстояние, сделай их чуть менее выраженными,
слегка уменьши». Before → after, measured:

| | before | after |
|---|---|---|
| box | 30 × 30 | 26 × 26 |
| gap between boxes | 10 px | 4 px |
| icon | 18 px, stroke 2 | 16 px, stroke 1.6 |

- The 10px came from `.group-card__header { gap: 10px }`, which also spaces title↔buttons — so the
  pair gets `.group-card__action + .group-card__action { margin-left: -6px }` rather than a smaller
  header gap. The two buttons are one control group; the same gap that separates them from the
  title was tearing that group in half.
- **Size is set in CSS, not via `size`/`density` props.** Both props miss here: for an icon button
  Vuetify derives the side from `--v-btn-height + 12px`, while `main.scss` pins `--v-btn-height` and
  `min-width` per size class and density touches only the height. Measured outcomes:
  `density="compact"` → 30 × 22 (rectangle), `size="small"` → 38 × 38 (bigger than the original).
  An explicit `width`/`min-width`/`height` wins outright — our unlayered CSS beats
  `@layer vuetify-components` (`docs/frontend/vuetify-css-patterns`). `min-width` is not optional:
  without it `.v-btn--size-default { min-width: 30px }` holds the box at 30 wide against a 26 height.
- «Less prominent» done with weight, not colour: stroke 2 → 1.6 and 18 → 16 px. The resting colour
  stays `--text-faint` — it was raised to clear AA in the contrast audit, so dimming it further
  would walk that back.
- Right edge: the icon now sits 1px inside the description's right edge (was 3px outside), so the
  buttons read as aligned with the text column.

Re-verified after the resize: copy still captures `GROUP@16b7506a5bd66271026c6b`, check mark
appears, no navigation; menu gaps still 10; console clean.

### Edit dialog check (light theme, as reported)

Opened «Изменить» on `GROUP@16b7506a5bd66271026c6b`: dialog shows the title, the code under it, and
Название / Краткое описание / Позиция / icon picker with the current icon selected. Round-tripped a
real save — typed a description, saved, confirmed via `GET /internal/research/groups` and on the
card, then cleared it and saved again; the shelf is back to `description: ''`, icon `flask`,
sort 500. Dialog closes on save, list refreshes, console clean.

## Follow-up 7: sources table rebuilt as a design-system card

«Приведи таблицу источников к оформлению дизайн-системы, сделай карточкой, добавь внутрь поиск и
фильтр по статусу + релевантности, сортировку по всем полям, и в начало три точки и кнопку
копирования — порядок именно такой».

`DocumentsTable.vue` rewritten. It serves both the research and the area page, so all of this
landed in one place.

- **Design-system shape** (`views/design-system/data/DataTableView`): the whole thing is one
  `VCard variant="outlined" rounded="lg"` — filter row, divider, `VDataTable density="comfortable"
  hover hide-default-footer`, `TablePaginationBar`. Replaces the bare `<div>` + Vuetify's own
  footer. The error path moved from a hand-rolled `VAlert` + `error: string` to `SectionError` over
  the raw rejection, like every other view.
- **Filters inside the card**: search + status + relevance, in the `filter-grid` idiom of
  `QueriesView`, with closable chips and «Сбросить фильтры» underneath. The old status-chip strip
  is gone; its counts survive inside the status options («Ошибка · 202»), and only statuses that
  actually occur are listed — an option promising an empty result is a lie.
- **Relevance is filtered in bands**, not by exact value: высокая 8–10 / средняя 4–7 / низкая 1–3 /
  не оценён (`relevance = null`). The score answers «стоит ли читать», not «ровно ли восемь», and
  the `null` band is the only way to find sources nobody graded.
- **Search covers title + url only** — what the row actually shows. `summary`/`note` are not in the
  table, and a hit in invisible text reads as a broken filter.
- **Sorting on every column** — client-side, since the data is already fully loaded. The title
  column sorts on `title || url`, i.e. on the string in the cell, not on a `null` behind it.
- **Row actions at the head of the row, ⋮ then copy** as asked. The menu holds «Открыть карточку»
  and «Открыть источник» (external, disabled when the source has no url) — both real `<a>`, so
  middle-click works; the trailing external-link column is gone, folded into the menu. Copy takes
  the prefixed `SOURCE@…`. The cell stops click propagation — the row itself opens the source card.
  Buttons reuse the group-card sizing (26×26, stroke 1.6, `--text-faint`) and the menu the same
  `--v-list-prepend-gap: 10px`.
- Pagination is client-side over the filtered set (25 by default); a filter that shrinks the list
  below the current page snaps back to page 1.

Live on `RESEARCH@45b8e9843e939d2f7c50d8` (202 sources) and `AREA@0c017c9c8e57eddbaf727a` (70):
sort by relevance flips 2→10, search «google» narrows 202→170, band «Высокая» leaves only 9–10 and
53 rows, chips and reset restore 202; row buttons read «Действия» then «Скопировать код» 2px apart,
copy captures `SOURCE@178b84e7718d6b064c95ed` without navigating, menu items are `<a>` to the card
and to the external url with `target="_blank"`. No raw i18n keys, console clean. `vue-tsc` 0,
`web/dist` rebuilt, full suite **586 passed**.

## Follow-up 8: interface wording — документ / описание / зоны

«Основное тело → Основной документ, Вводные → Описание, Области → Зоны исследования. Переименуй
в интерфейсе».

Locale-only change, no code touched. Beyond the three named labels the sweep covered every other
place the same words reach the user, because a section header saying «Зоны исследования» over a
table column saying «Области» is worse than either name alone:

| where | before | after |
|---|---|---|
| `research.detail.brief` | Вводные | Описание |
| `research.detail.body` / `no_body` | Основное тело | Основной документ |
| `research.detail.areas` / `no_areas` | Области | Зоны исследования / «нет зон» |
| `research.col.areas` (table column) | Области | **Зоны** — the column is 96px, the full name wraps |
| `sort.by.area_count` | Число областей | Число зон |
| `research.list.description` | …области, поиски… | …зоны, поиски… |
| `area.detail.title` (page + `<title>`) | Область | Зона исследования |
| `area.detail.no_queries` | В области… | В зоне… |
| `group.delete.warning` | …со всеми областями… | …со всеми зонами… |
| `home.flow.steps.area` + two capability blurbs | Области / область | Зоны / зона |
| `settings` reading-font hint | …исследований, областей… | …исследований, зон… |

⚠ Only the **interface** was renamed. The domain still says `area` everywhere it is not shown to a
person: the table `research_area`, the `AREA@` code prefix, the MCP tools (`area_create`,
`areas_list`, …) and their instructions, the routes `/research/areas/…`, the stores and DTOs. That
is a much larger, cross-surface rename — say the word if the term should change there too.

Live: research page reads «Описание / Основной документ / Заметки 11 / Источники» + «Зоны
исследования 6»; list column «Зоны», sort options include «Число зон», list description «зоны,
поиски…»; area page `<h1>` and browser title read «Зона исследования». The only «област» left in
the DOM is source content (Оренбургская область). Console clean, `vue-tsc` 0, `web/dist` rebuilt.

## Follow-up 9: zones moved under the main document

«Области перемещаем под Основное тело, над заметками. Логика отображения та же».

The block moved verbatim — same `VList` of rows with description and chevron, same empty card, same
`go()` on click. Reading order is now Описание → Основной документ → Зоны исследования → Заметки →
Источники.

That emptied the right rail, so the `<aside>` and `.detail-grid__side` are gone. **The 8-of-12
width stayed**: the content keeps two thirds and the right third is now blank padding. Asked the
user which they wanted (8-wide vs full width) and got no answer, so I kept the narrower measure —
it is the one they built in the typography pass, and going full width would stretch the body cards
and the sources table across 1400px. One line to switch if that was the wrong read.

Live at 1680px: sections read «Описание / Основной документ / Зоны исследования 6 / Заметки 11 /
Источники», no `.detail-grid__side` in the DOM, main column 910px, six zone rows with chevrons, a
row click lands on `/research/areas/AREA@cf5e90…`. `vue-tsc` 0, `web/dist` rebuilt.

⚠ **Pre-existing defect found while checking** (not mine, not fixed): every navigation between a
research and an area fires a 404. All five detail views do
`watch(() => route.params.code, reload)`, and `route` is the global current route — a KeepAlive'd
`ResearchView` sees the param change on the way to `/research/areas/AREA@…` and requests
`/internal/research/researches/AREA@…` (404); `AreaView` does the mirror image on the way back.
Two wasted 404s per hop. The fix is to gate each watcher on `route.name`; say the word.

## Follow-up 10: sticky section nav on the left

«Перемещаем всю контентную зону правее. Слева фиксированная панель навигации по исследованию,
в линию ровно с основным телом, с подсвечивающимися ссылками на все разделы».

- New `web/src/components/SectionNav.vue` — no research knowledge, takes
  `sections: { id, label, count? }[]`. **The page does not scroll the window**: `PageLayout` owns
  the scroll on `.page-layout__content` (`meta.scroll`), so the component finds that element with
  `closest()` and both listens to and scrolls it. `window.scrollY` is always 0 here, and
  `scrollIntoView` would have dragged the whole layout.
- **Active section by a rule, not by IntersectionObserver**: the current section is the last one
  whose top has risen above a line 96px below the container's top. Deterministic and easy to reason
  about, unlike tuning `rootMargin`. Plus one special case — scrolled to the bottom pins the last
  section, which is otherwise unreachable when it is shorter than the viewport.
- Each block is wrapped in `<section :id>`; ids come from one `SECTION` map shared by the markup and
  the nav list, so an anchor cannot drift from its link.
- Grid is now 3 (nav) + 8 (content) of 12 — the content moved right and kept exactly the width it
  had. The nav is a grid child starting on the same row, so its top lines up with the first section
  by construction, and `position: sticky; top: 0` pins it while reading.
- Below 1099px the nav stops being a column: it lays out as a row of links above the content and
  drops the stickiness (a pinned bar would eat the little height there is). The active marker moves
  from the left border to the bottom one.
- The link is a `<button>` (it scrolls the current page, it does not navigate) and needs the UA
  reset — without `appearance: none; background: transparent; border: 0` Chrome renders grey boxes
  with borders, which is exactly what the first live check showed.

Live at 1680px: nav sticks at 24px from the container top once scrolling starts, active follows
Описание → Основной документ → … → Источники, every link scrolls its section to offset 0, and the
bottom of the page pins «Источники». At 1000px the panel is a single row above the content, both
697px wide, `position: static`. Console clean. `vue-tsc` 0, `web/dist` rebuilt, suite **599 passed**.

Note for the check itself: a click on «Зоны исследования» from the top of a long body looks like it
falls short if you measure after ~1s — that is Chrome's smooth scroll still running, not a bug;
at 2.5s the section lands at offset 0.

### Follow-up 10a: nav into a card, grid 3/9

«Оставляем слева, но навигацию в плашку и сетку на 3/9».

- `SectionNav`'s root is now a real `VCard variant="outlined" rounded="lg" tag="nav"` instead of a
  bare `<nav>` — same surface as every other block on the page, so the table of contents reads as
  one of them rather than as loose links. The flex column moved to an inner `.section-nav__list`
  (the card keeps only padding + sticky); the `ref` sits on that list, so the `closest()` lookup for
  the scroll container is unchanged.
- Grid is 3 + 9: measured 326px nav vs 1027px content, ratio 3.15 (9/3 plus the gap).
- **4px top margin on the nav column** — `SectionHeader` opens a section with `margin: 4px 0 10px`,
  so without it the panel sat exactly those 4px above the first section. Now the tops match to the
  pixel (verified, not eyeballed).
- Contrast on the card surface, both themes: idle link 7.18 (light) / 6.56 (dark), active 17.23 /
  13.60 — well over AA.

Re-verified after the change: tops aligned, sticks at 24px, active follows the scroll, «Источники»
jumps to offset 0. Console clean, `vue-tsc` 0, `web/dist` rebuilt.

### Follow-up 10b: the active item redone

«Смотрится плохо, особенно скругление у активного пункта».

The complaint was exact and the cause was structural: the marker was `border-left: 2px` on an
element that also had `border-radius: 6px`. A border **is** the box outline, so the radius clipped
its ends into arcs — a straight tick with rounded stubs against a rounded box. Two shapes fighting
in the same 2px.

Replaced with one coherent state instead of two competing decorations:

- The marker is now an absolutely positioned `::before` **inside** the item — 2×15px,
  `border-radius: 1px`, vertically centred. It is not part of the box, so nothing clips it, and the
  left padding (20px) reserves its lane permanently, so the label never shifts when the highlight
  moves.
- The active item is a soft tinted pill: `background: var(--accent-soft)` + `--text` + weight 500.
  Tint and tick are the same accent, so the state reads as one thing.
- The tick animates its **height** (3px → 15px) rather than appearing: moving between sections is a
  stroke growing, not a blink. Hover shows the 3px dot at `--text-faint` — the row hints at where
  its marker will land.
- Card padding 8→6, row gap 2→1, item padding 7/10/7/20 — the list reads as a block instead of five
  loose buttons.
- In the narrow row layout the tick is switched off entirely (`display: none`, symmetric padding):
  side by side, the tint alone already says which one is current.

Checked in both themes at 2.2× zoom: pill `rgba(59,158,255,.14)` dark / `rgba(22,103,190,.10)` light,
tick 15px in the theme's accent, radius 6px, `border-left: 0` — the clipped border is gone. Console
clean, `web/dist` rebuilt.

## Follow-up 11: document headings as nested nav items

«Из основного документа получить заголовки и вывести их в навигатор вложенными пунктами. По идее
авто-разметка заголовков в компоненте вывода + их получение».

That was the right shape, and the pipeline already had the seam for it: `render.ts` hands code
blocks back as data via `env`, so headings ride the same channel — no second pass over the HTML.

- **`render.ts`** — new core rule `heading_anchors`: sets an `id` on every `heading_open` and pushes
  `{ id, level, text }` into `env.headings`, returned as `RenderedMarkdown.headings`.
  - The label is built with `renderer.renderInlineAsText`, so emphasis and links drop out. The rule
    is registered **after** `entity_refs` on purpose: by then a `AREA@<22-hex>` in a heading is its
    own token type, which `renderInlineAsText` ignores — the opaque hash never reaches the contents.
  - Slug: lowercase, non-letters/digits → `-`, capped at 60, `md-` prefix, `-2`/`-3` on collision.
    Cyrillic survives (`\p{L}`), so ids read like `md-итог-разбора`; lookups go through `CSS.escape`.
    The prefix keeps generated ids out of the page's own namespace, guarantees they never start with
    a digit, and the dash makes them unusable as JS identifiers — a heading cannot clobber a global.
  - `id` added to the DOMPurify allowlist (the parser emits no raw HTML, and `SANITIZE_DOM` still
    guards clobbering).
- **`MarkdownRenderer`** emits `headings`; `ResearchBody` forwards it; `ResearchView` keeps it in a
  ref. An emit rather than `defineExpose` — the consumer wants the finished list, not a handle into
  the renderer.
- **`SectionNav`** grew `depth` on `NavSection`: nested items are indented under the parent's marker
  lane, one step smaller, muted, and clipped to one line with an ellipsis (a three-line wrap in a
  326px column would eat the whole panel). The card also got `max-height: calc(100vh - 132px)` with
  the list scrolling inside — a long document's contents no longer runs off the bottom of the screen.
- **Only h1–h2** go into the nav (`NAV_HEADING_MAX_LEVEL`). Measured on real bodies: h2 gives 10–16
  entries, adding h3 pushes it to 20–33 — past the point where a table of contents is still glanceable.
  One constant to change if h3 is wanted.
- Empty body → no renderer → no event, so the view clears the list on a falsy `body`; otherwise the
  previous research's contents would linger.

Live: `RESEARCH@123aba…` shows 10 nested items under «Основной документ» with ids like
`md-итог-разбора`; clicking «Итог разбора» lands it at offset 0; scrolling walks the highlight
through Описание → Итог разбора → Уточнение… → Источники. `RESEARCH@7a9d38…` (16 h2) fits at 900px
and the list starts scrolling inside the card at 600px. Switching to a body-less research drops the
list to the 5 sections and back again on return. The design-system markdown page renders 3 bodies /
10 headings with 0 duplicate ids. Console clean, `vue-tsc` 0, `web/dist` rebuilt, suite **612 passed**.

⚠ Ids are unique per render, not per page: two markdown bodies on one page could repeat a slug.
Harmless today (the nav queries inside the scroll container and takes the first match, and no page
shows two bodies), but worth knowing before deep links to headings are added.

## Follow-up 12: global search over the research + a tools card

«Над навигацией блок с поиском и действиями (пока — скопировать код). Текстовый поиск по всем
источникам, заметкам, зонам — со скрытием того, где текста нет, и счётчиками в навигации».

The user's own read was right — this needed the stores reworked, because the data was split:
areas and notes sat in `research-detail.store`, while **sources were loaded and owned by
`DocumentsTable` itself**. One query cannot filter three collections from two owners.

**Ownership moved to the stores; the table became presentational.**

- `research-detail.store` now loads sources alongside the research (`Promise.all`), and
  `area-detail.store` does the same for its own — so `DocumentsTable` no longer fetches anything.
  Its props are `items` + `loading`; its own status/relevance/text filters stay inside it, applied
  on top of whatever list it is handed.
- That also removed the component's `scope`/`code` props, its `onActivated` reload and its private
  `SectionError` — one page, one load.

**Search lives in the store** (`search`, `searching`, `filteredAreas/Notes/Sources`, `matchCount`),
with the matching rule extracted to `features/research/search.ts`. Empty query matches everything,
so no consumer needs an "is the filter on" branch.

- Fields searched: area title+description, note title+description, source title+url+**summary+note**.
  The source's summary and note are not in the table, and that is deliberate: the global search
  answers «где в исследовании про X», and the review text is exactly where that lives. The table's
  own filter keeps searching only what its rows show — the two have different jobs, noted in both.
- The body itself is not filtered: hiding parts of a document you are reading is not search.
- Query survives a refresh of the same research but is cleared when the code changes — a query
  carried into another research would be searching foreign data.

**UI** — a card above the nav in the left column: search field, «Скопировать код» (the prefixed
`RESEARCH@…`, same `useClipboard`), and a «Найдено элементов: N» line that only appears while
searching. The **whole left column is sticky now**, not just the nav — otherwise the tools card
would scroll away and leave the contents behind it. `SectionNav` gave its `position`/`max-height`
back to the page: the component cannot know what stands next to it in the column.

**Hiding + counts**: with a query active, a section with zero matches disappears from the page *and*
from the nav; without a query, an empty section keeps its honest «пока нет…» card. Section counters
and nav counters both show the filtered number.

Live (via the dev Vite server on :22041 — see the caveat below): «давность» narrows
6/11/180 → 1/3/1 with «Найдено элементов: 5» and exactly 1 area row, 3 note cards, 1 source row;
«ежевика» leaves only Описание + Основной документ in both the page and the nav with
«Найдено элементов: 0»; clearing restores 6/11/180 and drops the summary line. Copy captures
`RESEARCH@123aba…`. The rail sticks (top 86 → 24 on scroll) with the tools card still on screen.
The area page still shows its 70 sources and 12 searches through the new store path. Console clean,
`vue-tsc` 0, suite **612 passed**.

⚠ For most of this the repo would not build: the user was mid-rename of
`ResearchesTable.vue` → `ResearchesList.vue` and two views still imported the old path, so
`vue-tsc` failed on **their** two files (mine were clean throughout). I verified against the running
Vite dev server instead of a rebuilt `web/dist`, and rebuilt `dist` once their rename landed.

## Follow-up 13: search covers the research itself, nav toggle, 48px scroll gap

1. **The research is a document too.** `briefMatches` (title + description) and `bodyMatches` (the
   main document) joined the store's search, count into «Найдено элементов», and obey the same
   hide rule as the other sections — that is the rule as stated («скрытие документов где этого
   текста нет»), now applied to all five instead of three. The body text is still not filtered
   *inside* — a document either matches or is hidden, but it is never shown with holes in it.
   The nav drops the hidden sections too, and the document's own contents go with the body.
2. **Setting** `app.nav.document` (`settings.ui.documentNav`, default on) + a `VSwitch` on
   `/settings/interface`: turns the document's headings off in the nav while leaving the page's
   own sections. Client-side and persisted like the rest of that page; a value equal to the
   default is not written to storage.
3. **48px above the target on jump.** `SCROLL_OFFSET` in `SectionNav`; the active-line threshold is
   derived from it (`SCROLL_OFFSET + 48`), so a section that has just been scrolled to is
   immediately the highlighted one instead of lighting up a moment later.

Live on `RESEARCH@123aba…`: «271-ФЗ» → 6 matches, «Описание» hidden (the phrase is only below);
«капремонт» → 82 with «Описание» back; «Оренбург» → 34 with «Описание» *and* «Зоны» gone. Clearing
restores all five. Jump lands the section at exactly 48px with the right item active. The switch
flips `app.nav.document` to `0`, the nav drops from 15 items to 5 (heading ids stay in the HTML —
only the contents list goes), and removing the key restores 15. Console clean, `vue-tsc` 0,
`web/dist` rebuilt, suite **618 passed**.

⚠ Mid-check the page threw `Cannot read properties of undefined (reading 'refetchingAll')` — the
user's in-flight `useSourcesRefetch` wiring in `ResearchView`, not this work; a reload after their
save cleared it.

## Follow-up 14: hybrid search — instant scan layer + a server pass over the bodies

The audit answer («поиск не максимальный») turned into the hybrid the user picked.

**What was missing and why it could not be done on the client.** The detail endpoint returns nested
entities as the scan layer, so bodies never reach the browser. Measured in the dev DB: area bodies
2.7 MB, note bodies 0.5 MB, page material **16.8 MB** — and on the biggest single research the
material alone is 15.7 MB. Shipping that per page load is out of the question.

**Backend.** `services/search.py::search_bodies(research_code, query)` → codes of areas / notes /
sources whose **body** matches, behind `GET /internal/research/{code}/search?q=`. New CRUD reads
select two columns only (`area_bodies_by_research`, `note_bodies_by_research`,
`source_material_by_research` — the last joins `web_search_page`).

- **The match runs in Python, not SQL, and that is the load-bearing decision.** SQLite's `LIKE` is
  case-insensitive for ASCII only, and `lower()` does not touch Cyrillic at all — verified:
  `lower('Ж') == 'Ж'`, and `'ОРЕНБУРГ' LIKE '%оренбург%'` is false. A SQL search would silently
  miss Russian text in the wrong case. Cost measured on the 15.7 MB research: **99 ms** in Python
  vs 35 ms for the wrong SQL answer. Provider-agnostic as a bonus.
- Queries shorter than 2 chars return empty instead of reading every body for a junk answer.

**Frontend.** The store keeps the instant half exactly as it was and adds a catching-up half:
debounce 350 ms, `AbortController` per run, stale runs dropped, `report: false` (a failure of the
second half must not toast over results already on screen — it silently degrades to the instant
ones). `filtered*` is now «instant match **or** in the deep set».

**UI.** «Найдено элементов: N» gains a spinner + «ищу в текстах…» while the server half is in
flight, so fragments appearing a moment later read as the search completing rather than as the page
rearranging itself. Sections and note cards moved into `TransitionGroup name="fragment"`: enter
220 ms, leave 130 ms (leaving is an answer to a keystroke already made; entering has to be caught by
the eye), `fragment-move` so the survivors slide instead of jumping, and the whole thing is off
under `prefers-reduced-motion`.

Item 3 of the request — «Основной документ и описание тоже должны пропадать» — was already done in
follow-up 13 and is confirmed working below.

Live on `RESEARCH@c16b0e…` (753 pages / 15.7 MB), query «налоговая»: at 120 ms the page shows
**15** matches with «ищу в текстах…» and only «Основной документ / Источники 14»; once the server
answers it settles at **157** — «Зоны 7 / Заметки 6 / Источники 143». Backend tests +6 (deep match
across all three kinds, Cyrillic case folding, non-match, too-short query, staying inside its own
research, 404). `vue-tsc` 0, `web/dist` rebuilt, suite **638 passed**.

⚠ Two things to know:
- The dev backend on :22040 is serving a **stale app** — its log ends with «Stopping reloader
  process», and it answers 404 on the new route while the same route is present in the module and
  green in tests (and worked in the browser earlier through this very backend). It needs a restart;
  I did not restart it while you are working in it.
- While diagnosing that 404 I fired `POST …/documents/refetch` on that research to check whether a
  recently-added route was live. It is a **mutating** call and it started a real refetch against the
  down scraper daemon; I killed the client after ~2 min. Only sources already in `error` are touched
  by the research-level verb, so their status does not change — but that request was a mistake.

### Follow-up 14a: copy moved to the header

«Скопировать код переносим в шапку, после кнопки обновления».

Moved out of the tools card into `PageHeader`'s actions, right after «Обновить», at the header's
own button size (16px icons instead of the card's 15px `size="small"`). The card is now just search
+ the «найдено» line, so `.rail-tools__actions` and its negative-margin rule went with it.

Live: header reads «Обновить / Скопировать код», the rail has zero buttons, the copy captures
`RESEARCH@123aba…` and flips to «Код скопирован». Console clean, `vue-tsc` 0, `web/dist` rebuilt.

Sibling finding while looking for the formatter (not acted on): the donor also has
`formatDistanceShort` («7 мес.», abbreviated, single largest unit — written for a caption under a
date) and a shared `DateCell.vue` component; neither was carried over. Here the date+relative pair
is copy-pasted inline in `QueriesView` / `PagesView`.
