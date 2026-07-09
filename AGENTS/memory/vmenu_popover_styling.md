---
name: vmenu_popover_styling
description: "Styling a click-popover built on VMenu — teleport, scoped CSS, .v-list card override, arrow overflow"
metadata: 
  node_type: memory
  type: reference
  originSessionId: cfc38f66-48cf-4680-8877-d08592a6bb1c
---

Building an interactive tooltip-style popover on a Vuetify `VMenu` (click, items clickable — unlike non-interactive `VTooltip`):

- Content **teleports out** of the component, BUT scoped CSS still applies to elements written in the template (Vue stamps them with the `data-v-*` scope id). `:deep()` to overlay **internals** (`.v-overlay__content`, etc.) does NOT reach from a scoped block — they aren't descendants of your scoped root. Override those in a **separate non-scoped `<style>` block**, namespaced by the menu's `content-class`.
- A `.v-list` inside a menu **inherits the global dropdown-card styling** (surface bg + border + shadow) → stacks a second panel inside your popover. Flatten it: `.v-menu <content-class> <list-class>.v-list { background/border/border-radius/box-shadow: ... !important }` (the extra `.v-list` qualifier outscores the global `!important`).
- Arrow (rotated-square `::before`) is clipped unless the overlay content allows overflow: `<content-class>.v-overlay__content { overflow: visible }` (global block).
- Bubble look: `border` + `filter: drop-shadow(...)` (NOT box-shadow — drop-shadow wraps the arrow pseudo-element too); `location="bottom start"` + `offset`.

Reusable impl: `web/src/components/MembersCell.vue` (first-member + `+N` popover, `select(index)` event; demo at `/design-system/members-cell`). Used by `/conversations` + `/mail-sync/threads`.
