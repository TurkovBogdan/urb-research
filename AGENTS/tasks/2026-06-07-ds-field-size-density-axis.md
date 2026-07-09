---
title: Design-system — field size via density axis (global heights)
date: 2026-06-07
status: completed
description: "Make Vuetify's native density actually drive field height (it was flattened by a hardcoded min-height: 36px), globally for all v-field inputs, and surface it as the 'Sizes' section on /design-system/selects."
tags: [frontend, design-system, vuetify, scss]
---

## Task

«http://localhost:12100/design-system/selects — нужно добавить и проработать размеры»

Clarified via AskUserQuestion:
- **Approach** = "Чинить density" — make native `density` (default/comfortable/compact)
  genuinely change height, rather than inventing a custom size scale or width axis.
- **Scope** = "Глобально для всех полей" — apply to every `v-field` (select/text/number/date),
  not just a scoped demo on the selects page.

## Context

Vuetify inputs have **no `size` prop** (unlike VBtn) — height is meant to come from
`density`. But `main.scss` hardcoded `.v-field__input { min-height: 36px }`, so all three
densities rendered at the same 36px — the Density section on `/design-system/selects` showed
no visible height difference.

## What was done

- `web/src/styles/main.scss` (Inputs block):
  - Kept the base `.v-field__input` (36px + 8/8 padding) as **density="default"** (tallest —
    Vuetify semantics: default > comfortable > compact).
  - Added density steps **after** the `.v-field {}` block (equal specificity → source order wins):
    - `.v-input--density-comfortable .v-field__input` → 32px, padding-bottom 6px
    - `.v-input--density-compact .v-field__input` → 28px, padding-bottom 4px
    - top padding reduced (6/4px) only for outlined/plain (center-affix); filled/underlined
      keep their reserved top padding (`padding-top: var(--v-field-input-padding-top)` for the
      floating label) — density rules touch only their padding-bottom.
- `web/src/views/design-system/controls/SelectsView.vue`: renamed the "Density" section to
  "Sizes" (`section.selects.sizes`), specs now show the px height (36/32/28), added a `ds-note`
  explaining size = density axis, no `size` prop, global heights.
- `web/src/locales/design-system/{en,ru}.json`: added `section.selects.sizes` (Sizes / Размеры);
  selects page description "density"→"sizes" / «плотность»→«размеры».
- `AGENTS/docs/frontend/design-system.md`: documented the field-size-via-density override.

## Verification (browser, Vite :12100)

- `/design-system/selects` → measured `.v-field` heights: default **36px**, comfortable **32px**,
  compact **28px** (was uniformly 36px). Screenshot confirms the "Размеры" section + note render.

## Notes / loose ends

- **Global side effect (intended):** every existing `density="compact|comfortable"` field across
  the app (report filter bars, login, profile, VDateInput default=compact → 28px) now genuinely
  shrinks; before they were all flattened to 36px. User opted into global scope. Worth a visual
  pass over the conversation_insights report filter rows where compact selects sit next to 36px
  controls.

## Follow-up (2026-06-07) — harmonize control-bar heights

The new real heights exposed mismatched rows. Two fixes:
- **Processed-chats top control row** (`ProcessedConversationsView.vue` `.view-controls`): search field
  + sort `VSelect` were converged to `density="comfortable"` (32px); I brought the two `VBtnToggle`
  (view-format + sort-direction) from `compact` → `comfortable` to match. Note: `VBtnToggle`/`VBtn`
  height is **size-driven** (`--v-btn-height` from the size class, forced via `.v-btn-group .v-btn`
  `!important` in main.scss), so toggle density is effectively a no-op for height — the toggle's
  *outer bordered box* already measured 32px (30px button + 2px group border), flush with the
  32px fields. Changed density purely for code uniformity. Verified all four controls top=98.9/h=32.
- **`TablePaginationBar.vue`** (shared footer for every list view): page-size `VSelect` was
  `density="compact"` (28px) — the odd small one next to the 30px pager buttons. Bumped to
  `density="comfortable"` (32px). Verified in browser on the processed table (select 32 / pager 30,
  reads aligned). `vue-tsc` clean.
