---
name: frontend_keepalive_orphaned_tooltip
description: Hover VTooltip stays stuck on screen after a navigating row-click; KeepAlive deactivation skips mouseleave
metadata:
  type: project
---

Hover `VTooltip` teleports content to `<body>` and closes on the activator's `mouseleave`. On a click that navigates (e.g. `@click:row` → `router.push` with the tooltip open), the global `<KeepAlive>` ([[frontend_keepalive_double_load]]) **deactivates** the leaving page before `mouseleave` fires → `isActive` stays true → the overlay lingers (lands top-left, no live activator to anchor).

**Why:** seen as a dark pill stuck in the corner showing stale content (e.g. an email subject) after navigation.

**How to apply:** fixed globally in `router/guards.ts` `beforeEach` → `dismissHoverTooltips()` (`router/overlays.ts`): for each `.v-overlay--active.v-tooltip`, find activator via `[aria-describedby="<overlay.id>"]` (open overlay root has `id`, activator has matching `aria-describedby`) and dispatch `pointerleave`+`mouseleave`. Must run in `beforeEach` (activator still in DOM). Do NOT `.remove()` the overlay node — it does not reset Vuetify `isActive`, leaving that tooltip permanently unable to reopen.
