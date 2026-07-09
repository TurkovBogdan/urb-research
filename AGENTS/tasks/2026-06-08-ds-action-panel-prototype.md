---
title: Design-system "Action panel" prototype
date: 2026-06-08
status: in-work  # in-work | completed | deferred
description: "New design-system page /design-system/action-panel — interactive prototype for marking a page's actions (refresh button, filter panel, …) and relocating the marked ones into a bottom action panel on mobile. Prototype lives only in the DS for now; not wired into real pages."
tags: [web, design-system, responsive, mobile, prototype]
---

## Task

User: «Изучи дизайн систему, добавь рядом с брейкпоинтами страницу Панель
действий.» Then the direction: there are various page elements (e.g. a refresh
button, a filter panel); we will build functionality that lets us **mark**
(«разметить») them and **relocate** them into a bottom action panel on mobile.
For now the prototype lives only in the design system.

This is the successor to the reverted cross-page action-sheet experiment
(`2026-06-06-mobile-filter-slot-experiment`) — re-prototyped in the DS first, as
the user said it would be.

## Context

The DS has a «Адаптация» (responsive) group with one page so far,
`/design-system/breakpoints`. We add a second page next to it. The new page is a
self-contained interactive demo — it does NOT touch `App.vue`, the layout store,
or any real page. The mobile viewport is **simulated** with a fixed-width frame +
a Desktop/Mobile toggle, so both layouts are inspectable without resizing the
browser (the pain documented in `responsive-testing-process`).

## What was done

- **`web/src/views/design-system/responsive/ActionPanelView.vue`** (new) — the
  prototype. Pieces:
  - A **marking config**: a list of demo actions (Фильтры `panel`, Обновить
    `button`, Создать `button`), each with a `VBtnToggle` to set its placement
    `inline` (toolbar) vs `bottom` (bottom panel). A grip icon hints future
    drag-reorder.
  - A **viewport toggle** (Desktop / Mobile) driving a simulated `previewMobile`
    ref — independent of the real window.
  - A **preview frame** (`position:relative`, fixed height, `max-width:380px`
    when mobile): page toolbar (title + inline actions), inline-expanded filter
    panel on desktop, fake content rows, a **bottom action panel** (mobile only)
    holding the `bottom`-marked actions, and a **slide-up sheet** that a `panel`
    action (filters) opens inside the frame.
  - Computeds: `inlineActions` / `bottomActions` / `inlinePanels` split by
    placement and `previewMobile`; `activate()` opens/closes a panel's sheet.
- **`web/src/router/design-system.ts`** — added route
  `/design-system/action-panel`.
- **`web/src/views/design-system/DesignSystemIndexView.vue`** — added the card to
  the `responsive` group (icon `IconLayoutBottombarExpand`).
- **i18n** `web/src/locales/design-system/{ru,en}.json` — `index.page` card,
  `page.action-panel` title/description, and `section.action-panel` (intro,
  marking, viewport, placement, action labels, filter field labels).

No automated tests (DS-only FE wiring / responsive CSS); verified in browser.

## Result

`vue-tsc --noEmit` clean. Browser-verified at default width via the in-frame
toggle:
- **Mobile**: toolbar keeps only Создать; bottom panel shows Фильтры + Обновить;
  tapping Фильтры slides up a sheet with Статус/Канал/Поиск; sheet geometry
  192px, fully inside the 460px frame.
- **Desktop**: all three actions inline in the toolbar + the filter panel
  expanded inline below; no bottom panel, no sheet.
No console errors.

## Open / next

- This is a v1 prototype to iterate on with the user. Marking is per-session
  (not persisted); drag-reorder is only a visual grip hint so far.
- Switching to Desktop while a sheet is open keeps `openPanelKey` set (re-shows
  on returning to Mobile) — intentional state-preservation; revisit if it reads
  oddly.
- Eventual goal: promote the proven shape into a real cross-page mechanism (see
  the retained Teleport finding in `mobile-action-sheet-pattern` — use component
  registration, never Teleport out of a KeepAlive + out-in page).
