---
title: Sidebar — hide header divider when collapsed
date: 2026-05-31
status: completed
description: "In collapsed (rail) mode the header divider read as a top border on the first nav item; hide it when collapsed, keep it expanded."
tags: [frontend, layout, sidebar]
---

## Task

In the collapsed navigation the first item appears to have a top border, which is
actually the nav header divider. Look in the browser and fix it.

## Context

In rail (collapsed) mode the full-width `.sidebar-divider` in the drawer `#prepend`
sat roughly midway between the centered collapse toggle and the first nav icon
(measured: divider bottom y=53, first item top y=61, 8px gap, no actual border on the
item). With no logo text or group label in collapsed mode to anchor the line to the
header, the full-bleed divider read as a top border on the first navigation item.

## What was done

- Gated the `#prepend` (header) divider with `v-if="!layout.collapsed"`:

  ```
  - <VDivider class="sidebar-divider" />
  + <VDivider v-if="!layout.collapsed" class="sidebar-divider" />
  ```

- Only the header divider is affected; the `#append` divider above the
  settings/locale block is untouched.

## Problems

- The `<VDivider class="sidebar-divider" />` string matches twice (`#prepend` and
  `#append`); scoped the edit with surrounding context to hit only the header one.

## Result

- Changed: `web/src/layout/components/AppSidebar.vue`.
- Verified in-browser: collapsed → header divider absent (no line above the first
  icon); expanded → divider present, bottom still y=53 (aligned with the content-header
  divider, per the header-divider 1px gotcha in memory).
