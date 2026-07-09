---
title: DS — rename Tables→Data table, add plain VTable page styled to match
date: 2026-06-11
status: completed
description: "Rename the design-system Tables page to Data table, add a sibling Table page demoing plain VTable, and add global default styles so a bare VTable looks like VDataTable."
tags: [frontend, design-system]
---

## Task

«Переименуй страницу в DataTable, создай рядом аналогичную для обычной таблицы. Открывай браузер и прорабатывай стили по умолчанию, чтобы обычная таблица выглядела как data table.»

## Context

`/design-system/tables` (`data/TablesView.vue`) demoed only `VDataTable`. There was no showcase for the plain `VTable`, and a bare `VTable` rendered with Vuetify's default look (no uppercase grey header, no soft row borders) — visually inconsistent with our data tables.

## What was done

- Renamed `data/TablesView.vue` → `data/DataTableView.vue` (`git mv`); repointed its `PageHeader` i18n key `tables`→`data-table`.
- New `data/TableView.vue` — mirrors the data-table demo (basic / density / states / custom cells / pagination) using native `thead`/`tbody` markup inside `VTable`. Loading/empty states composed by hand (VTable has no built-in props).
- Router `router/design-system.ts`: `/design-system/tables`→`/design-system/data-table` + new `/design-system/table`.
- `DesignSystemIndexView.vue`: `data` group slug `tables`→`data-table` + new `table` (icon `IconTableRow`, imported).
- i18n `locales/design-system/{en,ru}.json`: `index.page` + `page` blocks — `tables`→`data-table`, added `table`.
- **Styling (the point):** `styles/main.scss` new block `.v-table:not(.v-data-table)` (`:not` excludes the VDataTable root which carries both classes) — replicates the `.v-data-table` header (uppercase, `--text-faint`, `--surface-hi` bg, 36px, bottom border) + soft row borders + `--hover` tint, so a plain `VTable` matches the data table by default.
- Verified in browser (Chrome MCP): basic/density sections of the two pages render pixel-identical; index `Data` group shows both cards. `vue-tsc --noEmit` clean.

## Problems

- Dev login flakiness: the Chrome MCP `fill_form` didn't reliably sync Vuetify's `v-model` (login 401 with correct creds). Fixed by setting input values via the native value setter + dispatching `input`/`change` events. Working dev creds live in the local password manager/`.env` (the dev DB `admin@semaphore.local` hash didn't match `semaphore` despite `.env`).

## Result

- Renamed: `web/src/views/design-system/data/DataTableView.vue`
- Added: `web/src/views/design-system/data/TableView.vue`
- Changed: `web/src/router/design-system.ts`, `web/src/views/design-system/DesignSystemIndexView.vue`, `web/src/locales/design-system/{en,ru}.json`, `web/src/styles/main.scss`
