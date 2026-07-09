---
title: Mobile navigation adaptation
date: 2026-06-06
status: completed
description: "Make the sidebar responsive — on mobile turn the permanent rail into an overlay (temporary) drawer toggled from a new top app-bar (hamburger + brand + profile avatar). Reference screenshots provided by the user."
tags: [web, layout, navigation, responsive]
---

## Task

Add mobile adaptation for navigation. Reference (mobile mockups) provided: an overlay drawer with a brand header + close (X), and a top app-bar with hamburger, brand, and a profile avatar on the right.

## Context

Current shell (`web/src/App.vue`): `VApp` → `AppSidebar` (`VNavigationDrawer permanent`, desktop rail with collapse) + `VMain`. No top bar. On narrow screens the permanent rail eats horizontal space and there is no way to reach the nav as an overlay.

## What was done

- Vuetify `display.mobileBreakpoint = 'md'` (mobile when width < 960 — matches the existing `PageHeader` 959px breakpoint).
- `layout/store.ts`: added non-persisted `mobileOpen` state for the overlay drawer.
- `App.vue`: added a mobile-only `VAppBar` (hamburger → toggles drawer, brand, avatar → `/profile`).
- `AppSidebar.vue`: drawer is `temporary` + `v-model` on mobile / `permanent` on desktop; collapse rail disabled on mobile (always full width); logo header shows a close (X) on mobile instead of the collapse chevron; navigation closes the drawer on mobile (route watcher).

## Problems

- `mcp__claude-in-chrome__resize_window` / `window.resizeTo` / F11 do not change the viewport on this Linux box (tiling WM caps every window at ~788px wide; `screen.width=1920` but `innerWidth` stays put). So a true ≥960 desktop viewport could not be exercised in-browser. Desktop was instead verified on a tab whose `AppSidebar.vue` had HMR-updated but whose `vuetify.ts` (the `mobileBreakpoint`) had NOT reloaded → `mobile=false` → the refactored desktop branch rendered correctly (permanent rail, collapse chevron, full nav, ProfileNavCard).

## Result

Mobile chrome verified at 333px and 788px (overlay drawer + top bar), desktop branch verified via the stale-plugin tab. No console errors; `vue-tsc --noEmit` clean.

Files changed:
- `web/src/plugins/vuetify.ts` — `display: { mobileBreakpoint: 'md' }` (mobile < 960px).
- `web/src/layout/store.ts` — added non-persisted `mobileOpen`.
- `web/src/App.vue` — mobile-only `VAppBar` (hamburger → `layout.mobileOpen`, brand → `/home`, avatar → `/profile`) + scoped styles. The hamburger glyph flips to a close-X while the drawer is open (`layout.mobileOpen ? IconX : IconMenu2`).
- `web/src/layout/components/AppSidebar.vue` — `useDisplay().mobile`; drawer `:permanent="!mobile"` / `:temporary="mobile"` + `v-model="drawerOpen"`; `collapsed = !mobile && layout.collapsed` (rail disabled on mobile); the logo header (brand + collapse-chevron) is **desktop-only** (`#prepend` gated `v-if="!mobile"`) — on mobile the brand already lives in the top bar, so the drawer opens straight to the nav list (no duplicate name, no in-drawer X); route watcher closes the overlay on navigation.

Open tuning point: the `md` (960px) breakpoint is a one-liner in `vuetify.ts` if the boundary should differ.
