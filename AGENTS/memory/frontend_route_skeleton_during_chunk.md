---
name: frontend_route_skeleton_during_chunk
description: show a page skeleton while a code-split route chunk downloads (boot splash vs skeleton)
metadata: 
  node_type: memory
  type: project
  originSessionId: a20674d1-5f64-4059-a5ac-2238c9d395b8
---

A skeleton living **inside** a lazy `() => import()` route component can't render during
the chunk download — `main.ts` mounts only after `router.isReady()`, which **waits for the
lazy route component** to resolve, so the global boot splash (`index.html#app-splash`)
covers the whole download and the skeleton only flashes during the post-mount API fetch.

Fix: extract the skeleton to its own eager component and wrap the route loader in
`defineAsyncComponent({ loader, loadingComponent: Skeleton, delay: 0 })`. The route
component becomes a resolved object → `isReady()` no longer blocks on the chunk → skeleton
shows while the chunk downloads (full load + SPA nav). Reuse the same skeleton for the
in-view API-load state. Done for conversations detail (2026-06-18).

GOTCHA: the page `<Transition mode="out-in" appear>` in `App.vue` animates only a **single**
root. A routed view whose template root is a bare `v-if/else-if/else` chain becomes a
multi-root fragment → enter transition sticks (`*-enter-from` never clears, page frozen at
`opacity:0`). Keep one stable wrapper element as the view's root. See
[[frontend_keepalive_double_load]], [[frontend_pagelayout_meta_snapshot]].
