---
name: mobile-action-sheet-pattern
description: EXPERIMENT — cross-page mobile FAB + bottom sheet via component registration (NOT Teleport — that crashes under KeepAlive)
metadata: 
  node_type: memory
  type: project
  originSessionId: 144279a2-bbde-4ada-ac7b-4165cbb590d9
---

**Status: REVERTED (2026-06-08).** The experiment was removed from the live
conversations page (task `2026-06-06-mobile-filter-slot-experiment`, status
`reverted`): `useMobileActions.ts` deleted, `mobileActions*` stripped from
`layout/store.ts`, FAB+sheet removed from `App.vue`; `ConversationsFilters` is
now a plain inline responsive panel (6→3→1 col grid). The action-sheet idea will
be re-prototyped on the design-system page before any real page adopts it. The
description below is HISTORY — the code no longer exists. **The Teleport gotcha
at the bottom is the one firm, still-valid finding.**

Cross-page mobile "action sheet": a page registers a panel; on mobile a FAB
(bottom-right) slides up a bottom sheet holding it. Built 2026-06-06; first
consumer = conversations filter panel.

**Pieces:**
- `layout/store.ts` — `mobileActions*` state: `Active`/`Open`/`Count` (refs) +
  `Icon`/`Component` (`shallowRef`, they're component objects) +
  `registerMobileActions(icon, component)` / `clearMobileActions()`.
- `layout/useMobileActions.ts` — `useMobileActions({ icon?, component, count? })`.
  Registers on `onMounted`+`onActivated`, clears on `onDeactivated`+`onUnmounted`
  (KeepAlive-aware; the content `<Transition mode="out-in">` guarantees the
  leaving page deactivates before the entering one activates → no owner overlap).
  `count` is a `MaybeRefOrGetter`, kept in sync by a watch.
- `App.vue` — hand-rolled slide-up sheet (scrim + panel + grip, own CSS, NOT
  VBottomSheet) gated on `mobile && !fullscreen`, body = `<component :is=
  "layout.mobileActionsComponent">`; FAB = `VBadge`(count) → circular `VBtn icon`
  with the glyph rendered as `<component :is>` inside (passing a generic
  `Component` to VBtn's `:icon` fails type-check — `icon` wants `IconValue`).
- A page provides a STANDALONE panel component that reads the shared stores
  directly (no props), and renders it inline on desktop (`v-if="!mobile"`) so only
  one instance exists. The mobile sheet renders the same component (own instance,
  same Pinia store → state in sync).

**Why component-registration, NOT `<Teleport>` (cost two failed attempts):**
teleporting a page's panel out of a `KeepAlive` + `<Transition mode="out-in">`
page corrupts Vue's block patch → `TypeError: Cannot read properties of null
(reading 'emitsOptions')` in `shouldUpdateComponent` (render loop, hundreds of
errors; FAB/badge never patch in). Teleporting INTO a Vuetify overlay
(VBottomSheet, itself teleporting to `<body>`) makes it worse, and the target
"must exist before the component mounts" — a target after `<VMain>` in App's
template doesn't exist when the page mounts (`Invalid Teleport target on mount:
null`). Rendering a registered component sidesteps all of it.

Related: [[frontend_pagelayout_meta_snapshot]] (the same KeepAlive + out-in
transition constraints), mobile nav (`mobileBreakpoint: 'md'`, <960px).
