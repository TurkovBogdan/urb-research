# frontend-route-meta.md — route `meta` parameters

Every route's layout behaviour is driven by `route.meta`. The type is declared in
`web/src/router/meta.ts` (`declare module 'vue-router' { interface RouteMeta }`); this file
is the human reference for what each key does and who reads it.

This is a local site with **no authentication** — `router/guards.ts` only arms the navigation
progress bar, dismisses orphaned hover tooltips, and records navigation history. There is no
access-control meta and no `/me` round-trip.

## Layout

| Key | Type | Default | Read by | Effect |
|---|---|---|---|---|
| `scroll` | `'y' \| 'x' \| 'both' \| 'none'` | `'y'` | `PageLayout` (`scrollClass`) | Which axis the content zone scrolls. Maps to a `scroll-*` CSS class (`styles/main.scss`). |
| `padding` | `boolean` | `true` | `PageLayout` | Content padding. `false` drops the `pa-6` wrapper (full-bleed pages). |
| `fullscreen` | `boolean` | `false` | `App.vue` | `true` hides the app chrome (`AppSidebar`) — standalone full-bleed screens. |
| `transition` | `string` | `'page'` | `App.vue` | Name of the content-zone `<Transition>`. The sidebar is outside `RouterView`, so only the body animates. |

Notes:
- `scroll`/`padding` are consumed by `PageLayout`, so they only apply to pages rendered through
  it. A page that places its own scroll/`h-100` wrapper while also setting `meta.scroll` will
  double up — see `feedback_pagelayout_scroll.md`.
- `PageLayout` snapshots `scroll`/`padding` **non-reactively** at mount / KeepAlive activate, not
  live from `route`. It sits inside the content `<Transition mode="out-in">`, so a reactive read
  would flip the leaving page's padding/scroll to the incoming route's values mid-animation (a
  visible jerk). Consequence: changing these meta values for the *current* route at runtime won't
  re-apply until the page is re-activated — fine, since route meta is static.
- `transition` selects a CSS transition by name (the `<Transition :name>`). The names are plain CSS
  classes in `web/src/styles/transitions.scss` (imported in `main.ts` **after** `main.scss`) — they
  are **not** in `App.vue` and there is **no** TS enum; `meta.transition` is a free string Vue
  matches to class names (`transitionName = route.meta.transition ?? 'page'`). Built-in names:
  `page` (fade + slight `translateY` rise, default; `@media (prefers-reduced-motion)` drops the
  movement) and `fade` (pure opacity). The transition uses `mode="out-in"` + `appear` (animates on
  first paint too). A name with **no** matching CSS — e.g. `transition: 'none'` — renders instantly
  (disables the animation for that route). Bound to the **destination** route's meta, so leave +
  enter share the incoming name. Add a new option by defining `.<name>-enter-*`/`.<name>-leave-*`
  classes in `transitions.scss`. Enter/leave convention: for a transition `x`,
  `.x-enter-from`/`.x-leave-to` hold the hidden state and `.x-enter-active`/`.x-leave-active` carry
  the `transition:` (duration + easing); animate **only** opacity/transform, never
  width/height/top/left.

## Adding a route

- Standard page → no meta needed (defaults: scroll `y`, padded, chrome shown, `page` transition).
- Full-bleed page with no sidebar → `fullscreen: true` (+ `padding: false`/`scroll: 'none'` as needed).
