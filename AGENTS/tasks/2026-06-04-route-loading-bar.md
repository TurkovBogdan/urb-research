---
title: Route navigation loading bar
date: 2026-06-04
status: completed
description: "Add an animated loading bar at the top of the content zone shown while a route navigation has to wait (auth bootstrap or lazy-chunk import)."
tags: [frontend, router, ux]
---

## Task

User: "Изучи фронт и маршрутизатор. Мне не хватает отображения процесса перехода если страница требует загрузки, хочу полосу загрузчик с анимацией в верхней части контентной зоны."

## Context

Routes are lazy-loaded (`() => import(...)`) and the `beforeEach` guard awaits `auth.ensureReady()` (one `/me`) — so a navigation can visibly stall with no feedback. No app-level progress indicator existed; only per-view skeletons.

## What was done

- New `web/src/router/progress.ts` — module-level reactive `navigationLoading` (readonly) + `startNavigationProgress`/`stopNavigationProgress`. A `SHOW_DELAY=140ms` timer guards against flashing the bar on instant (cached) navigations.
- `web/src/router/guards.ts` — `beforeEach` arms the bar at the top; added `router.afterEach` (destination resolved, incl. lazy chunk loaded) and `router.onError` (aborted/failed nav) to clear it. A redirect re-enters `beforeEach` and re-arms, so the bar spans the whole hop.
- `web/src/App.vue` — render an indeterminate `VProgressLinear` (`color=primary`, `height=3`) absolutely pinned to the top of `VMain` (`inset:0 0 auto 0`, above the route `<Transition>`, outside it so it doesn't animate with the page). Own fade via a `route-progress` `<Transition>`.

No tests (pure FE wiring); verified `vue-tsc --noEmit` clean.

## Result

- Created: `web/src/router/progress.ts`
- Changed: `web/src/router/guards.ts`, `web/src/App.vue`
