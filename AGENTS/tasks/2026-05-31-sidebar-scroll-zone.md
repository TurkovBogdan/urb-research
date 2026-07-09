---
title: Sidebar scroll confined to nav-items zone
date: 2026-05-31
status: completed
description: "When nav groups are expanded and the sidebar overflows, only the nav-items list should scroll; the logo header and the bottom append (locale switcher + bottom links) stay fixed."
tags: [frontend, layout, sidebar]
---

## Task

Make the sidebar scroll only inside the nav-items zone — the fixed bottom and the top logo zone must not move when the menu is expanded and a scrollbar appears.

## Context

In `AppSidebar.vue` the logo header + its divider were rendered in the drawer's default slot,
i.e. inside `.v-navigation-drawer__content` — the scrollable middle area — together with the
nav `VList`. So when expanded groups overflowed, the logo scrolled away too. The bottom block
was already in the `#append` slot (fixed).

## What was done

- Moved the `.sidebar-logo` block + its `VDivider` into the `#prepend` slot of
  `VNavigationDrawer`. Vuetify renders `#prepend` into `.v-navigation-drawer__prepend`
  (fixed, non-scrolling), leaving only the nav `VList` in `.v-navigation-drawer__content`,
  which is the only area that scrolls. `#append` (locale switcher + bottom links) already fixed.

## Result

- Changed: `web/src/layout/components/AppSidebar.vue` — logo header relocated to `#prepend`.
  No style changes needed (`.sidebar-logo` selector unchanged).
