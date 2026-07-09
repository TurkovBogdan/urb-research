---
title: PageHeader smart back navigation
date: 2026-06-14
status: in-work  # in-work | completed | deferred
description: "Make the PageHeader back arrow return to the actual previous in-app page (router.back), with the declared backTo as a deep-link fallback."
tags: [frontend, navigation, layout]
---

## Task

The back arrow in the page-header component has a fixed destination (`backTo` → `router.push`). The same detail page can be opened from several places, and the user expects "back" to return where they came from, not to a hard-coded location.

## Context

- Back button is in one place: `web/src/layout/components/PageHeader.vue` (`backTo` prop → hard `router.push`).
- ~50 call sites pass a fixed `back-to`; an ad-hoc smart-back already exists in `mail_sync/ThreadView.vue` + both `ConversationView.vue` using the unreliable `window.history.length`.
- No navigation-history tracking in `router/guards.ts` yet.
- Research + plan written: `AGENTS/plans/2026-06-14-page-header-smart-back.md`.

## What was done

- Research: explored the header component, all `back-to` call sites, the existing ad-hoc `goBack()` pattern, and router guards. Wrote plan `2026-06-14-page-header-smart-back`.
- Implemented (user chose recommended defaults: `router.back()` + fallback; unify 3 views):
  - New `web/src/composables/useNavigationHistory.ts` — module-level `previousRoute` + `recordNavigation(from)` (real prev = `from.matched.length > 0`, START_LOCATION → null) + `useNavigationHistory().goBack(router, fallback)` (back() when prev exists, else push(fallback)).
  - `web/src/router/guards.ts` — `afterEach((_to, from) => { recordNavigation(from); … })`.
  - `web/src/layout/components/PageHeader.vue` — `backTo` is now the fallback; click → `goBack(router, props.backTo!)` (added `props` ref). ~50 call sites unchanged.
  - Unified ad-hoc `goBack()` (dropped `window.history.length`) in `mail_sync/views/ThreadView.vue`, `conversations/views/ConversationView.vue`, `intercom/views/ConversationView.vue` → local wrapper calling `navBack(router, <fallback>)`.

Tests: no FE unit harness touched; type-checked with `vue-tsc --noEmit` (exit 0).

## Result

- Plan: `AGENTS/plans/2026-06-14-page-header-smart-back.md`.
- Changed: `web/src/composables/useNavigationHistory.ts` (new), `web/src/router/guards.ts`, `web/src/layout/components/PageHeader.vue`, `web/src/features/mail_sync/views/ThreadView.vue`, `web/src/features/conversations/views/ConversationView.vue`, `web/src/features/intercom/views/ConversationView.vue`.
- `vue-tsc` clean. Recommend manual check: list→detail→back (scroll restored), thread→message→back returns to thread, deep-link/F5→back uses fallback.
