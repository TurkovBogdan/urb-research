---
title: Researches list — table / cards layout as a setting
date: 2026-08-27
status: completed
description: "Added a client-side 'research list layout' setting (table by default), a cards layout next to the table, and a toggle on the researches page that writes the same key."
tags: [frontend, research, settings]
---

## Task

«В настройки добавляем настройку отображения списка исследований, таблица или карточки. Таблица
по умолчанию. После делаем в Исследованиях второй вариант отображения. Переключатель должен быть
и на странице исследований, он меняет те же параметры.»

## Context

Two settings surfaces exist and they are not interchangeable: `/settings/modules` is the backend
runtime store, `/settings/interface` is the client-side `stores/settings.ts` (localStorage, applies
as picked, no save button). A layout preference is per-person and per-browser, so it belongs to the
second — and it joins that store's existing shape: a typed value plus a codec, with a value equal
to the default **removing** the key rather than writing it.

## What was done

### The setting

- `constants/lists.ts` — `ResearchListView` (`table` | `cards`), `DEFAULT_RESEARCH_LIST_VIEW =
  'table'`, the option table (i18n key + icon) shared by both switches, and
  `resolveResearchListView()`.
- `stores/settings.ts` — `lists.researchView`. The repair goes in the **codec**, not at the point
  of use: a hand-edited or stale storage value is fixed once on read instead of every consumer
  having to guard itself.
- `/settings/interface` — one more `VSelect` in the same card, named in full («Таблица» / «Плитки»)
  with a hint that says the page has its own switch.

### The two layouts

`ResearchesTable.vue` → **`ResearchesList.vue`** (`mv`): it is no longer only a table. The two
layouts differ in exactly one thing — how a row is drawn — while content, actions, filters,
pagination and dialogs are shared, so the choice is made inside the one card rather than by two
sibling components that would drift apart at the first new action.

- `ResearchRowActions.vue` — the kebab + copy button, extracted because a table cell and a card
  header need the identical set. It only **asks**: the dialogs stay in the list (one pair per list,
  not per row), and it receives `detaching` as a plain flag.
- Cards: a `repeat(auto-fill, minmax(300px, 1fr))` grid; the tile is a flex column so the footer
  (group chip + date) is pinned to the bottom and a row of tiles doesn't ripple with description
  length. Counters are stacked value-over-label — the labels have different lengths, and inline
  they would not line up into the columns people compare tiles by. The grid gets its own loading /
  empty states: `VDataTable` supplied those for the table, and a plain grid has nowhere to put them.

### The switch on the page

A `VBtnToggle` (`mandatory` — a layout always exists) at the end of the filter row, bound straight
to `settings.lists.researchView`, so it is the same key and not a per-visit override. It sits last
and slightly apart: it does not narrow the list, it redraws it.

The group page (`GroupView`) follows the setting too — it shows the same registry list — but has no
switch of its own, matching how it also has no filters.

## Verification

`vue-tsc` 0; `pnpm --dir web build` ok; `uv run pytest -q` 611 passed (no backend change).

Live on :22040 in an isolated browser context: default really is the table; the page toggle flips to
42 tiles and writes `app.list.research_view=cards`; the tile kebab opens with the full menu and does
**not** fall through to the research card; `/settings/interface` shows «Плитки» selected; switching
back to «Таблица» there **removes** the key (the store's equal-to-default rule) and the page renders
the table with the left toggle button active; the group page renders tiles as well. Console clean;
throwaway group + research removed and verified gone.

## Cards sit on the page, not inside the list card (same day)

Follow-up from the user: «если мы показываем карточки, они размещаются на сером фоне — сверху
панель поиска и сортировки, ниже карточки».

The first cut reused the table's shell for both layouts, so tiles rendered inside the outlined list
card — a border inside a border, and the card's padding ate a whole grid column (two columns where
three fit). The shell is now chosen by layout, because the two layouts want opposite things:

- **tiles** — the tile is its own frame, so the grid lies directly on the page canvas and the
  filters get their **own** `filter-panel mb-3` card above it (otherwise they'd have nothing to live
  in). Pagination follows on the canvas with `:divider="false"` — there is nothing above it to be
  separated from. Loading / empty states get a card of their own: `VDataTable` supplied those for
  the table, and on bare canvas a message would float without support.
- **table** — rows have no frames, so filters, rows and pagination stay in one card with rules
  between them, exactly as before.

Side effect worth noting: this also settles the tension with `feedback_filters_in_vcard` flagged in
`2026-08-27-researches-list-match-sources-table.md` — in the tile layout the filters are back in
their own `filter-panel mb-3` card, which is what that rule describes.

Verified live: three columns instead of two, panel above, pagination on the canvas, table untouched,
the group page renders tiles straight under its header (no empty panel — it has no filters).
`vue-tsc` 0, `web/dist` rebuilt, console clean.

## Tile content: counters out, group mark in (same day)

Follow-up: «Убирай в карточках информацию про зоны, поиски и остальное. Добавляй иконку и цвет
иконки из группы в карточку.» Tiles only — the table keeps its counters (and they are still what
four of the seven sort keys order by).

- The counters block and `cardCounters()` are gone from the tile. What is left is what a tile is
  for: name, description, and where it is filed.
- The footer's plain group chip became the same mark the group's own card uses — a tinted plate
  with the group icon in the group colour (`.color-tones` + `groupColorVars`, falling back to the
  accent) plus the name. The colour is carried by the **icon only**: on the name it would read as
  emphasis, and a plate across the whole name would fight the tile's own border.
- No group → the footer carries just the date. An explicit «без группы» mark is not drawn: its
  absence is already the answer.

Backend: `ResearchListRow` gained `group_icon` / `group_color`, filled by a new
`group_style_fields()` **next to** `group_fields()` rather than inside it — the MCP contracts share
*identifying* a shelf (code + name) with the interface, but not its looks. Shipping the look with
the row is what spares every list consumer from also holding the group registry.

Tests +2 (`test_list_carries_the_group_look`, `..._is_empty_without_a_group`).

Verified live: 0 counter blocks in tiles, the mark renders `tabler-icon-flask` in
`rgb(89,222,101)` = `green.light` on its 14% tint (exactly what the registry defines for dark), the
table still shows all four counter columns. `vue-tsc` 0, full suite **638 passed**, `web/dist`
rebuilt, console clean, temporary group + research removed.

## Problems

- No frontend test runner, so the layout switch is pinned by the live walk-through only.
- The group chip in a tile footer is redundant on the group page itself (you are already inside that
  group), but it is what makes a tile self-describing in the registry; left as is.

## Result

One preference, two switches, two layouts, one component. `ResearchRowActions` is now the single
home for what can be done to a research from a list.

Not done:

- `DocumentsTable` (sources) keeps its single layout — the setting is named for the research list
  only, and a sources tile has no counters to justify one.
