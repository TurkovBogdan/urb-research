---
title: Researches list — same anatomy as the sources table
date: 2026-08-27
status: completed
description: "Moved the researches-list filters into the table card (divider between them) and added the row-actions column (kebab + copy code), so the registry list reads identically to the sources table on a research page."
tags: [frontend, research]
---

## Task

«Список исследований. Посмотри деталку с таблицей источников и её оформление + кнопки. Нужно
сделать идентично на странице списка исследований.» Reference given:
`/research/researches/RESEARCH@69a6859a09e878772e28b6`.

## Context

Two list surfaces had drifted apart:

- `DocumentsTable.vue` (sources): filters live **inside** the table card, a `VDivider` under them,
  an active-filter chip row, and a first column of row actions (kebab menu + copy code, 84px).
- `ResearchesTable.vue` + `ResearchesView.vue` (registry): filters in a **separate** `filter-panel`
  card above the table with `mb-3`, and no actions column at all.

`ResearchesTable` is shared with the shelf page (`GroupView`), which has no filters — the shelf
*is* the filter — so the fix could not simply move the filter markup into the table component.

## What was done

- `ResearchesTable.vue` renders a `filters` slot inside its own `VCard`, followed by a `VDivider`;
  both are skipped when the slot is absent, so `GroupView` is untouched (verified live).
- `ResearchesView.vue` passes its existing filter grid + chip row through that slot. The separate
  `filter-panel` card is gone; `.filter-grid` now carries the 12px padding itself and the chips
  carry `0 12px 12px` — the same metric as `.doc-filters` / `.doc-filters__chips`.
- Row actions column, ported 1:1 from `DocumentsTable` (markup, classes, 26px hand-sized icon
  buttons, `--v-list-prepend-gap` on the menu):
  - kebab → **Открыть карточку** (the research) + **Открыть полку** (its group), the second
    disabled when the research is unshelved — mirrors «Открыть источник» being disabled without a url;
  - copy-code button with the self-clearing «скопировано» check (`useClipboard`).
- One `researchesPath(code)` helper serves both menu items and the row click: research and shelf
  deliberately share the `/research/researches/:code` segment and are told apart by the code
  prefix (`routes.ts`).
- Locales: `research.research.action.{actions,open_card,open_group,copy,copied}`.

## Verification

- `vue-tsc --noEmit` 0; `pnpm --dir web build` ok, `web/dist` rebuilt; `uv run pytest -q` 599 passed
  (no backend change — listed as a regression guard).
- Live on :22040 in an isolated browser context: filters sit in the card above the divider, the
  kebab opens with both items, the shelf item is disabled on an unshelved research and navigates
  correctly on a shelved one (checked on a throwaway group + research created and deleted through
  the MCP server), copy sets the check mark, the shelf page still renders without filters, console
  clean.

## Problems

- Tension with the standing rule `feedback_filters_in_vcard` («filter bars on list pages ALWAYS
  wrapped in a VCard `variant="outlined" rounded="lg" class="filter-panel mb-3"`»). The filters are
  still inside a VCard — the table's own — but no longer in a separate `filter-panel` card. The
  explicit "make it identical to the sources table" instruction wins; the memory entry now
  describes only one of the two list surfaces and should be reworded to «фильтры всегда в карточке
  (собственной панели либо карточки таблицы), не голыми».

## Result

Both list surfaces now have one anatomy: filters → chips → divider → table → pagination, with a
row-actions column in front. The `filters` slot is the seam for any future list built on
`ResearchesTable`.

Not done:

- The kebab has no destructive verb, though `DELETE /internal/research/researches/{code}` exists —
  still the open thread from `2026-08-27-research-user-delete-routes.md`.
- `feedback_filters_in_vcard` not edited (records are the user's call); flagged above.
