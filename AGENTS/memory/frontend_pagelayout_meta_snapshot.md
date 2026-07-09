---
name: frontend_pagelayout_meta_snapshot
description: PageLayout snapshots route.meta scroll/padding non-reactively to avoid a transition jerk under <Transition mode=out-in>
metadata:
  type: project
---

`PageLayout` reads `route.meta.scroll`/`padding` **once, non-reactively** — snapshotted into a
`contentClass` ref by `syncLayoutMeta()` on `onMounted` + `onActivated`, NOT via a `computed` on
`route`.

Why: `PageLayout` renders inside the content `<Transition mode="out-in">` in `App.vue`. With
`out-in`, the global router route flips to the destination *immediately* (after guards), while the
leaving page stays mounted to play its fade-out. A reactive `computed(() => route.meta.padding…)`
therefore re-evaluates on the still-visible leaving page → its `pa-6` / `scroll-*` classes snap to
the *incoming* route's values mid-animation = a visible jerk (e.g. padded page → `/agents/chat`
`padding:false`: content jumps 24px while fading). Snapshotting freezes each page's own values
until it re-becomes current.

Consequence: changing `scroll`/`padding` meta for the *current* route at runtime won't re-apply
until the page re-activates — fine, route meta is static. The earlier (wrong) hypotheses were the
`translateY` rise and the padding itself; the real cause is the reactive `route` read inside the
out-in transition zone. Rejected alternative: push `pa-6` into every page (churn + leaves the same
`scroll` jerk). See [[frontend_auth_bootstrap]] for the App.vue transition setup and
[[feedback_pagelayout_scroll]] for the don't-double-wrap rule.
