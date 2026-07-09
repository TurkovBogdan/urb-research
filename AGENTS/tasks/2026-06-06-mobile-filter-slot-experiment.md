---
title: Mobile filter-slot / action-sheet experiment
date: 2026-06-06
status: reverted  # experiment removed 2026-06-08; to be reworked on the design-system page
description: "EXPERIMENT — REVERTED 2026-06-08. Cross-page mobile FAB + bottom sheet hosting a page's filter panel via component registration (useMobileActions). Removed from conversations; the conversations filters are now a plain responsive panel. The action-sheet idea will be re-explored on the design-system page first, not wired into real pages yet."
tags: [web, responsive, mobile, experiment]
---

> **Status: REVERTED (2026-06-08).** The experiment was removed from the live
> conversations page per user request — the FAB + bottom-sheet was deemed
> premature for production. The conversations filters are now a plain adaptive
> panel. The action-sheet concept will be prototyped on the design-system page
> before any page adopts it. The Teleport-vs-registration finding (below) stays
> valid.

## Removal (2026-06-08)

User: «Убирай этот функционал, будет его прорабатывать на странице дизайн
системы. Сейчас сделай фильтры просто адаптивной панелью, проверяй в браузере
на отдельной странице.»

Reverted the whole action-sheet machinery; `ConversationsFilters` is kept as a
plain responsive panel rendered inline always.

- **Deleted** `web/src/layout/useMobileActions.ts`.
- **`layout/store.ts`** — dropped all `mobileActions*` state +
  `registerMobileActions`/`clearMobileActions` (back to `collapsed`/`showTopBar`/
  `showBottomBar`/`mobileOpen`).
- **`App.vue`** — removed the slide-up sheet markup, the FAB (`VBadge`+`VBtn`),
  all related CSS, and the now-unused `IconFilter` import.
- **`ConversationsView.vue`** — removed `useMobileActions` call + `useDisplay`/
  `mobile` + `IconFilter`; `<ConversationsFilters>` now renders unconditionally
  (no `v-if="!mobile"`).
- **`ConversationsFilters.vue`** — unchanged behaviour; only comments updated. The
  responsive grid stays: 6-col (>1200) → 3-col (960–1200, search spans row) →
  1-col (≤959).
- **`list.store.ts`** — removed `activeFilterCount` (it only fed the FAB badge);
  `hasActiveFilters` kept (used by the chip row).
- **i18n** — removed `common.action.actions` (ru+en), the FAB aria-label.

`vue-tsc` clean. Browser-verified on a standalone window at three widths:
532px (1-col, mobile drawer, no FAB), 1068px (3-col), 1400px (6-col); no console
errors.

Verification note: this MCP-controlled Chrome can't be resized via the MCP
`resize_window` tool or DevTools shortcuts (keystrokes don't reach Chrome's UI).
Working method on KDE/X11: pop the MCP tab into its own window, find it with
`xdotool search --class google-chrome` (confirm by resizing + reading
`window.innerWidth` via the JS tool), resize with `xdotool windowsize`, and
screenshot the window with `import -window <id>` (Chrome clamps min width ≈532px).

## Task

User: «Теперь, вот эти изменения про слот фильтров добавь в память как
эксперимент, создай отдельную задачу и не закрывай её.» — record the mobile
filter-slot work as an experiment and track it in its own, still-open task.

Originating ask (earlier in the session): «настоящая киллер фича. Компонент
действий на мобильных» — on mobile, move a page's filter panel into a
button-triggered bottom sheet; make the button + sheet cross-cutting for all
pages, shown only when a page contributes content, with a per-page icon.
Follow-ups: FAB bottom-right + badge with the active-filter count; in the sheet,
one field per line.

## Context

Per-view responsive work (parent task
`2026-06-06-interface-responsive-adaptation`). The conversations filter panel is
wide; on a phone it belongs in a bottom sheet behind a FAB rather than inline.
We want this as a reusable mechanism, not a one-off.

## What was done

Implemented and browser-verified @360 (sheet) + @1280 (inline). See the parent
task and memory [[mobile-action-sheet-pattern]] for the full mechanics. In brief:

- **`layout/store.ts`** — `mobileActions*` state (`Active`/`Open`/`Icon`/
  `Component`/`Count`) + `registerMobileActions`/`clearMobileActions`.
- **`layout/useMobileActions.ts`** (new) — `useMobileActions({ icon?, component,
  count? })`; (de)registers on mount/activate ↔ unmount/deactivate (KeepAlive).
- **`App.vue`** — hand-rolled slide-up sheet + circular FAB w/ `VBadge`; renders
  the registered component via `<component :is>` (mobile only).
- **`features/conversations/components/ConversationsFilters.vue`** (new) — filter
  panel extracted from the view (reads stores directly). Grid 1 column below md.
- **`ConversationsView.vue`** — registers the panel; renders it inline only on
  desktop. `list.store.ts` += `activeFilterCount`.
- i18n `action.actions`.

No automated tests (FE wiring / responsive CSS); verified in browser.

## Problems

The first design teleported the page's panel into the sheet
(`<Teleport :disabled="!mobile">`). Teleporting out of a `KeepAlive` +
`<Transition mode="out-in">` page corrupts Vue's block patch →
`TypeError: Cannot read properties of null (reading 'emitsOptions')` (render
loop; FAB/badge never appear) + `Invalid Teleport target on mount: null`.
Resolved by switching to component registration (render in App via
`<component :is>`, no Teleport). Captured in memory
[[mobile-action-sheet-pattern]].

## Result

Files: see the file list in `2026-06-06-interface-responsive-adaptation.md`
(layout store/composable, `App.vue`, `ConversationsFilters.vue`,
`ConversationsView.vue`, `list.store.ts`, locales). `vue-tsc` clean.

## Open / to evaluate

- Live with it across more pages before promoting it from "experiment" to a
  documented convention (or dropping it).
- Candidate second consumers: other list/filter views (mail_sync threads,
  conversation_insights processed/reports).
- Decide the desktop story: today only mobile uses the sheet; is a desktop
  affordance ever wanted?
- Possibly fold the registration into `PageLayout` (a `#mobile-actions`-style
  API) once the shape is proven.
