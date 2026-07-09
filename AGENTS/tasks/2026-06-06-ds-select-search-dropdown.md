---
title: Design-system — search-inside-dropdown select variant
date: 2026-06-06
status: completed
description: "Add a showcase variant to the Dropdowns DS page demonstrating an explicit search row pinned atop an open VSelect menu (not a built-in component — a pattern), with a source code block."
tags: [frontend, design-system]
---

## Task

«Добавь в design-system выпадающих списков вариант с явным поиском сверху выпадающего списка, проверь в браузере, с иконкой поиска, и блок кода (это не типовой компонент)».

## Context

`controls/SelectsView.vue` covered VSelect variants/states/icons/objects/density + a VAutocomplete row. Autocomplete merges the query into the field; the user wanted the field display kept intact with a search row at the top of the open menu — Vuetify has no built-in for this, it's a `#prepend-item` pattern, so it warrants a code block.

## What was done

Follow-up: the user asked for a **reusable component** (`VSelectSearch`) + a *usage* example, not the inline implementation. Refactored accordingly.

- `web/src/components/VSelectSearch.vue` (new): drop-in wrapper over `VSelect`. Owns the search row (`#prepend-item`: `VTextField` + `IconSearch`, `autofocus`, `@keydown.stop`), in-place filtering (`computed`, by `itemTitle` for object items), `#no-data` empty state, `@update:menu` query reset. `inheritAttrs: false` + `v-bind="$attrs"` pass all VSelect props through; consumer slots forwarded except the two it owns. Props: `items`, `itemTitle` (default `title`), `searchPlaceholder`, `noDataText`; `defineModel` v-model.
- `web/src/views/design-system/controls/SelectsView.vue`: "Search inside dropdown" section now renders `<VSelectSearch>` and the `CodeBlock` shows the **connection** snippet (import + `<VSelectSearch v-model :items label variant />`), not the implementation. Removed the inline filtering logic + `.dropdown-*` styles (moved into the component).
- `web/src/composables/useHighlighter.ts`: added `vue` to the shiki language list so the snippet highlights.
- `web/src/locales/design-system/{en,ru}.json`: key `section.selects.searchInDropdown` (EN "Search inside dropdown" / RU "Поиск внутри списка").

Verified in browser (Vite :12100): dropdown opens with the search row + icon, typing filters live ("vor" → Voronezh), selection binds, query resets on reopen. `vue-tsc --noEmit` clean; 0 Vue warnings / 0 console errors.

## Result

New reusable `VSelectSearch` component + DS page showing its usage. 4 files (1 new component, 3 edited); no backend, no migration.
