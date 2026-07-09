---
title: Design-system — multi-select chips styled + chips as global default
date: 2026-06-07
status: completed
description: "Style multi-value VSelect/VAutocomplete selection chips per the design system and make chips the global Vuetify default (chips/closableChips), neutralizing single-select chips back to plain text and opting compact filters out."
tags: [frontend, design-system, vuetify]
---

## Task

«Выпадающие списки с выбором нескольких значений, поправь оформление под нашу дизайн систему и стили. И выстави их по умолчанию» (на `/design-system/selects`).

User chose **global Vuetify defaults** for "выстави их по умолчанию" (AskUserQuestion).

## Context

Multi-selects previously rendered default Material-grey chips and required explicit `chips closable-chips` props per usage. Vuetify has **no conditional default** — `chips: true` in `defaults` applies to single selects too, where it (a) wraps the single value in a pill and (b) with `closableChips` adds a removable × that deletes a (possibly required) value. Also, when `chips` is true Vuetify **ignores the `#selection` slot** (chips branch wins), which would break the compact "+N" filters on the processed-chats page.

## What was done

- `web/src/plugins/vuetify.ts`: added `chips: true, closableChips: true` to `VSelect` / `VAutocomplete` / `VCombobox` defaults (alongside `variant: 'outlined'`).
- `web/src/styles/main.scss` (Chips block):
  - global: kill `.v-chip__underlay` (selected-state tint) alongside the existing `.v-chip__overlay` reset — we paint the background ourselves.
  - `.v-select--single, .v-autocomplete--single, .v-combobox--single .v-chip` → transparent bg, no border, no padding, 13px/400 (matches `.v-select__selection-text`), `.v-chip__close { display: none }` → single select looks like plain text again.
  - `.v-select--multiple, .v-autocomplete--multiple, .v-combobox--multiple .v-chip` → `--surface-hi` bg, `1px solid --border`, `--text`; muted `.v-chip__close` (`--text-muted` → `--text` on hover).
- `web/src/features/conversation_insights/views/ProcessedConversationsView.vue`: added `:chips="false"` to the two compact filters (is_commercial `VSelect`, tags `VAutocomplete`) so their `#selection` "+N" slots take effect again (chips would otherwise override the slot).
- `web/src/views/design-system/controls/SelectsView.vue`: simplified the "multiple" demo to just `multiple` (chips now default), spec label → "chips by default", added a `ds-note` documenting the global default + `:chips="false"` opt-out.

## Follow-up — dropdown selected-item styling

User feedback on the open menu: selected options highlighted **grey** (Vuetify's dark `.v-list-item__overlay` selected-tint at 0.08) and items "слипались" (no vertical gap). Fixed in `main.scss` dropdown `.v-list` block (scoped to menu/select/combobox/autocomplete overlays):
- `.v-list-item + .v-list-item { margin-top: 3px }` — breathing room.
- `.v-list-item--active` → `background: var(--accent-soft)`, kill the grey overlay (`opacity:0`), title + prepend checkbox icon → `var(--accent)`.

Verified via computed styles: active item bg `rgb(224,246,247)`=`--accent-soft`, icon/title `rgb(0,136,144)`=`--accent`, margin-top `3px`; visually the checked option shows the brand teal.

## Follow-up — double border-radius on the menu

User noticed "двойное скругление" on the open menu. Cause: the menu wrapper (`.v-overlay__content` + inner `.v-sheet`) carries its own 4px radius + white background, which pokes out from behind the `.v-list` rounded at 10px — two concentric radii at each corner. Fix in `main.scss`: `.v-select__content` / `.v-combobox__content` / `.v-autocomplete__content` / `.v-menu > .v-overlay__content` (and descendant `.v-sheet`) → `background: transparent`, `border-radius: var(--radius)`, `box-shadow: none` so only the list paints the rounded surface. Verified: single clean radius on all four corners.

## Follow-up — tighter dropdown items

User: reduce left padding before the checkbox / make items a bit narrower — **only in the checkbox (multiple) scenario**; a blanket reduction made single-select dropdowns too tight. Final: `.v-list-item:has(.v-list-item__prepend .v-checkbox-btn) { padding-inline-start: 8px }` (scoped to dropdown `.v-list`). Checkbox items → 8px left; single-select items keep the default 16px. (`:has()` already used elsewhere — `safe_email_body_sizing`.)

## Follow-up — TablePaginationBar warn + "select clicks every other time"

- **Vue warn (Extraneous class on `TablePaginationBar`)**: the component had two root nodes (`<VDivider>` + `.pagination-bar` div) → fragment root, so the parent's `class="mt-3"` couldn't inherit (silently dropped + warned). Wrapped in a single root `<div class="pagination-bar-root">`. Verified: no more warning across view switches; `mt-3` now actually applies. (Unrelated to the chips work — surfaced by the user from the processed page console.)
- **"Селект через раз кликается" — REAL chips regression, fixed.** Root cause: in a single select the value now renders as a `VChip`; clicking **on the value text** hit the chip, whose click didn't propagate to the field activator → menu didn't open. Clicking the empty field area worked → "every other click". Fix: `pointer-events: none` on the single-select neutralized chip (it's purely decorative — × already hidden, value shown as text), so clicks pass through to the field. Verified: clicking directly on the "Moscow" value text now opens the menu (`v-select--active-menu` → true). Multiple-select chips keep pointer events (need the × to remove). (The earlier "page mid-load" theory was a secondary factor, not the main cause.)

## Verification (browser, Vite :12100)

- DS page: single select → plain "Moscow" text (no pill, no ×); multiple → styled chips "Moscow ⊗ / Saint Petersburg ⊗", × removes a chip; `multiple` alone (no explicit chips) renders styled chips.
- Processed page: DOM check — single selects `v-select--chips` true (neutralized), `Коммерческий`/`Теги` `chips:false` (compact `#selection` preserved). `multiple="range"` on `VDateInput` (reports) unaffected.
- No new console warnings from the change (pre-existing `TablePaginationBar` extraneous-class warning unrelated).

## Notes / loose ends

- Pattern going forward: multi-selects get chips for free; a multi-select wanting custom/compact selection display must pass `:chips="false"` (then use `#selection`).
- Unrelated: `/internal/conversation-insights/processed` returns **500** (no filter params) — backend error, not from this change; surfaced to user.
