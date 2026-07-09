---
name: frontend_auth_bootstrap
description: Frontend mounts only after router.isReady() so the app chrome never flashes before /me resolves; static boot splash in index.html
metadata:
  type: project
---

The SPA must not paint the app chrome (sidebar + menu) before the session is known.
`main.ts` gates mount on the initial navigation:

```ts
void router.isReady().then(() => app.mount('#app'))
```

Why this works: the route guard (`router/guards.ts`) awaits `auth.ensureReady()` (one
memoized `/me`) and applies any redirect (guest → `/login`, which is `fullscreen`). So when
`router.isReady()` resolves, `route.meta.fullscreen` is already correct → `App.vue`'s
`<AppSidebar v-if="!fullscreen">` decision is right at first paint. Guards never reject
(`ensureReady` catches → guest state), so the app always mounts.

The wait (~2 s on remote SSL DB) is covered by a **static** boot splash baked into
`index.html` (`#app-splash`, a CSS spinner in brand colours `#008890` / bg `#F4F6F8`).
Vue replaces `#app` on mount, so the splash needs no JS teardown.

Do NOT gate only on `auth.ensureReady()` directly — that still leaves a one-frame flash of
`START_LOCATION` (empty meta → `fullscreen` false → sidebar) before the redirect resolves.
`router.isReady()` already encompasses the `/me` wait via the guard.

Pre-existing flash cause (the bug this fixed): `App.vue` renders the sidebar gated only on
`route.meta.fullscreen`, independent of auth; mounting synchronously painted the full shell
for ~2 s until `/me` returned. Compounded by nav entries declaring no `action`/`subject`, so
`can(undefined, undefined)` is `true` → every menu item showed regardless of ability (the
permission filter in [[frontend_auth_permissions]] is currently a pass-through). See also
[[project_test_runtime_dev_leak]] for the remote-DB latency context.
