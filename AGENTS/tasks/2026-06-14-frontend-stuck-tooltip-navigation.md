---
title: Stuck hover-tooltip after route navigation
date: 2026-06-14
status: completed
description: "Hover tooltips (mail threads/messages subject) stayed orphaned on screen after clicking a row to navigate. Caused by KeepAlive deactivating the page before the activator's mouseleave fires; fixed by closing open tooltips in router.beforeEach."
tags: [frontend, router, vuetify, tooltip]
---

## Task

User reported: "Иногда на фронте при переходе подвисает вот такая штука из тултипов" — a dark tooltip (showing an email subject `DEC-PO…/IN-JGO`) stuck floating in the top-left corner after navigation. Find the cause and fix it.

## Context

`VTooltip` (open-on-hover) teleports its content to `<body>` via `VOverlay` and closes on the activator's `mouseleave`. The app wraps routed views in a single global `<KeepAlive>` (`App.vue`). Offending tooltips sit on **click-navigating rows** — subject tooltips in `ThreadsView.vue:350` / `MessagesView.vue:383` (`activator="parent"`, the row has `@click:row` → `router.push`).

Sequence that breaks: hover a subject → tooltip opens (teleported to body) → click the same row → `router.push`. `<KeepAlive>` **deactivates** the leaving page (does not unmount it) before `mouseleave` ever fires, so the tooltip's internal `isActive` stays `true` and its body-level overlay lingers. Browser-reproduced: after navigating to `/mail-sync/threads/5677` the overlay stayed `v-overlay--active` indefinitely (still present at 2.4 s), positioned at the top-left because there is no live activator to anchor to.

## What was done

Verified the whole thing live in the isolated browser (dev `:12100`):
- Reproduced the persistent orphan (1 active `.v-overlay.v-tooltip` after nav, never clears).
- Rejected DOM removal of the overlay — it does not reset Vuetify's `isActive`, leaving that tooltip instance permanently unable to reopen.
- Confirmed dispatching `pointerleave`+`mouseleave` on the **activator** closes the tooltip through Vuetify's own state (reopens cleanly afterward, no console errors).
- Found the deterministic activator link: the open overlay root carries `id="v-tooltip-v-N"`, the activator carries `aria-describedby="v-tooltip-v-N"` — no `:hover` guessing needed.

Implementation:
- New `web/src/router/overlays.ts` — `dismissHoverTooltips()`: for each `.v-overlay--active.v-tooltip`, find its activator via `[aria-describedby="<overlay.id>"]` and dispatch `pointerleave`+`mouseleave`.
- `web/src/router/guards.ts` — call `dismissHoverTooltips()` at the very start of `router.beforeEach`, while the leaving page (and its activator) is still in the DOM, before `<KeepAlive>` detaches it.

End-to-end verified: open tooltip → run fix → navigate → 0 orphaned overlays (immediately and after 1.5 s); tooltips still open/close normally; no errors.

## Result

- `web/src/router/overlays.ts` (new)
- `web/src/router/guards.ts` (one call added in `beforeEach`)
