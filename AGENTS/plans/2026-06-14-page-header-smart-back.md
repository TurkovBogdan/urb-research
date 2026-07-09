---
title: PageHeader smart back navigation
date: 2026-06-14
status: completed  # in-work | completed | deferred
description: "Back button in PageHeader returns to the actual previous in-app page (router.back) and falls back to the declared backTo only on a direct/deep-link entry."
tags: [frontend, navigation, layout]
---

## Goal

The back arrow in `PageHeader` returns the user to the page they actually came from, not a hard-coded parent. When a detail page is reached by in-app navigation, "back" lands on the real previous route (with its scroll position and KeepAlive state restored). When the page was opened directly (deep link, F5, new tab), "back" falls back to the page's declared default parent.

## Context

- The back button lives in a single component: `web/src/layout/components/PageHeader.vue:5-26`. It takes `backTo?: RouteLocationRaw` and on click does a hard `router.push(backTo!)`. The destination is fixed per call site.
- Problem: the same detail page is reachable from multiple parents (e.g. `MessageView` from the messages list, from a thread, from insights, from search). Users expect "back" to return where they came from, but `backTo` is a single fixed route.
- Call sites that pass a fixed `back-to` (would become fallback-only): `features/mail_sync/views/MessageView.vue:84` (`/mail-sync/messages`), `features/agents/views/AgentSessionDetailView.vue:195`, `features/agents/views/AgentSessionsView.vue`, `features/administration/views/UserDetailView.vue:174` (`/administration/users`), `features/intercom/views/ContactView.vue:67` (`/intercom/contacts`), `features/core_geo/views/{Countries,Continents,Languages,Timezones}View.vue` (`/core-geo`), `features/core_monitoring/views/{TaskRuns,TaskRequests}View.vue` (`/tasks`), plus ~30 design-system demo pages (`back-to="/design-system"`).
- A hand-rolled "smart back" already exists but bypasses `PageHeader` and uses an unreliable signal: `features/mail_sync/views/ThreadView.vue:110-113`, `features/conversations/views/ConversationView.vue:89`, `features/intercom/views/ConversationView.vue:161` — all `if (window.history.length > 1) router.back() else router.push(<fallback>)`. `window.history.length` never decreases and counts pre-app history, so it can send the user out of the SPA.
- The router has no navigation-history tracking. Guards (`web/src/router/guards.ts`) currently handle only auth, the progress bar, and tooltip dismissal; `afterEach` is free to extend (`guards.ts:45`).

## Scope

**In scope:**
- A small navigation-history tracker (composable or pinia store) updated from `router.afterEach`, exposing the previous in-app route and a `goBack(fallback)` action.
- `PageHeader.vue`: keep the `backTo` prop but treat it as the **fallback**; route the click through the shared `goBack`.
- Unify the existing ad-hoc `goBack()` in `mail_sync/ThreadView.vue` + both `ConversationView.vue` onto the shared tracker (drop `window.history.length`).

**Out of scope:**
- Full breadcrumb trails / multi-step history UI.
- Changing any call site's `backTo` value (they keep working unchanged, just as fallback).
- Per-route scroll-restoration config beyond what `router.back()` already gives.

## Approach

Track the immediate previous in-app route in `router.afterEach((to, from) => …)`. vue-router's initial entry has `from.matched.length === 0` (START_LOCATION); any real previous page has `matched.length > 0`. Store that `from` (or null) in a tracker. The back action:

- previous in-app route present → `router.back()` — stays in the SPA (the previous history entry is a real in-app route) and restores the list's scroll + KeepAlive state for free;
- otherwise (direct/deep-link entry) → `router.push(fallback)` using the page's declared `backTo`.

`backTo` thus changes meaning from "always go here" to "default parent when there's no history" — no call site needs editing, and the ~50 existing usages get the new behavior automatically.

**Alternatives considered:**
- `router.push(savedPreviousPath)` instead of `router.back()` — robust on *where* it lands but loses scroll/KeepAlive restoration of the list. Rejected as the default (worse UX for the common list→detail→back loop). Easy to switch to if desired.
- `?from=<path>` query param set by every list — most explicit, but requires editing every source call site and pollutes URLs. Rejected for cost/clutter.
- Keep `window.history.length` — unreliable (monotonic, counts pre-app entries, can exit the SPA). Rejected; this plan removes it.

## Steps

1. Add navigation tracker — files touched: `web/src/composables/useNavigationHistory.ts` (new) or `web/src/stores/navigation.ts`. Holds `previousRoute: RouteLocationNormalized | null`; exposes `goBack(fallback: RouteLocationRaw, router)` implementing the back()/push(fallback) decision.
2. Wire it into the router — files touched: `web/src/router/guards.ts` (extend `afterEach` to record `from` when `from.matched.length > 0`, else null).
3. Route PageHeader through the tracker — files touched: `web/src/layout/components/PageHeader.vue` (keep `backTo` prop; change `@click` to call shared `goBack(backTo, router)`; keep the button hidden when no `backTo` and no `before` slot, matching current `v-if`).
4. Unify ad-hoc goBack — files touched: `web/src/features/mail_sync/views/ThreadView.vue`, `web/src/features/conversations/views/ConversationView.vue`, `web/src/features/intercom/views/ConversationView.vue` (replace local `goBack()`/`window.history.length` with the shared action + their existing fallback path).

## Tests

- Unit (vitest, if FE unit harness present): tracker records `from` only when `matched.length > 0`; `goBack` calls `router.back()` when a previous route exists and `router.push(fallback)` otherwise. Covers the direct-entry vs in-app-entry split.
- Manual / E2E (Chrome MCP): list → detail → back returns to the list with scroll preserved; thread → message → back returns to the thread (not the messages list); open a detail URL directly (F5) → back goes to the declared fallback parent; design-system page → back to `/design-system`.

## Validation

- From the messages list, open a message, click back → land on the list at the prior scroll position.
- From a thread, open one of its messages, click back → land on the thread, not `/mail-sync/messages`.
- Hard-reload a `/mail-sync/messages/:id` URL, click back → land on `/mail-sync/messages` (fallback fires, never leaves the SPA).
- vue-tsc clean (`pnpm --dir web build`).

## Risks / open questions

- Risk: `router.back()` after a forward/back dance could feel ambiguous — mitigation: the tracker records the immediate `from` per navigation, which is exactly "where we came from to reach this page"; previous-entry is always a real in-app route, so back() never exits the SPA.
- Open question (Q1, default chosen): `router.back()` vs `router.push(savedPath)` — plan defaults to `back()` for scroll/KeepAlive restoration; switchable in step 1 if the user prefers deterministic destination over restored state.
- Open question (Q2, default chosen): unify the 3 ad-hoc `goBack()` views — plan defaults to yes (step 4); can be dropped to a PageHeader-only change if a smaller diff is preferred.

## References

- Related tasks: `AGENTS/tasks/2026-06-14-page-header-smart-back.md`
- Key files: `web/src/layout/components/PageHeader.vue`, `web/src/router/guards.ts`
- Existing pattern to replace: `web/src/features/mail_sync/views/ThreadView.vue:110-113`
