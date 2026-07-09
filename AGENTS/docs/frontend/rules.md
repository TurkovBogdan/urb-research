# frontend-rules.md — stack, layout, theme, Vuetify gotchas

One-stop reference for working on `web/src/`: structure, design tokens, page layout, Vue lifecycle, Vuetify 4 CSS caveats. Source of truth for the patterns; deeper Vuetify-CSS recipes live in [`vuetify-css-patterns.md`](vuetify-css-patterns.md).

## Date formatting

See [`dates.md`](../platform/dates.md) — full reference for `@/shared/utils/date` functions and the standard table date cell pattern.

## Stack

- Vuetify **4.x** (not 3.x — `VMain` behaviour differs)
- Vue 3.5, Vue Router 4.5, Vite 6, TypeScript 5.8
- `@tabler/icons-vue` 3.x (MDI removed)
- pnpm workspace; `web/` is the only frontend package

## `web/src/` layout

```
src/
  App.vue              ← 10 lines: VApp + AppSidebar + VMain
  layout/              ← base app shell
    store.ts           ← Pinia: collapsed, showTopBar, showBottomBar
    components/
      AppSidebar.vue   ← sidebar nav with tooltips
      PageHeader.vue   ← title + description + #actions slot
    templates/
      PageLayout.vue   ← toolbar/content/footer slots
  shared/
    nav.ts             ← TablerIcon type, NavLink, NavGroup, NavEntry
  features/<name>/
    nav.ts             ← NavGroup/NavLink with Tabler icons
    routes.ts
    views/
  plugins/
    vuetify.ts         ← Tabler icon set + aliases, theme
  styles/
    main.scss          ← design tokens (CSS vars), Vuetify overrides
```

## Page patterns

- Put view content directly inside `<PageLayout>` (like `TasksView`/`HomeView`).
- `PageLayout` already applies `pa-6` to the content `<div>` when `route.meta.padding !== false`. **Do not** wrap view body in another `<div class="d-flex flex-column h-100 pa-6">` — the padding doubles and the page slides off. If you need a `flex-column h-100` wrapper to stretch a table, keep the wrapper but drop `pa-6`. To remove padding entirely: `route.meta.padding = false`.
- `<PageHeader>` on every page:
  ```vue
  <PageHeader title="..." description="...">
    <template #actions><VBtn>...</VBtn></template>
  </PageHeader>
  ```
- `<RouterView>` is wrapped in `<KeepAlive>` in `App.vue` — page components are NOT unmounted between navigations. **Always pair `onMounted` + `onActivated` for data loading.** `onMounted` fires on first render; `onActivated` fires on every subsequent navigation back to the page. Without `onActivated`, the page shows stale data. Intervals/timers — pair `onActivated`/`onDeactivated`; `onUnmounted` rarely fires.

**Standard page data-loading pattern:**
```ts
// initial load with spinner
onMounted(async () => {
  await load()
  loading.value = false
})
// refresh on every navigation back (no spinner, data just updates)
onActivated(load)
```
Shorthand when no separate `loading.value = false` is needed: `onMounted(load); onActivated(load)`.

**A routed view MUST have a single root element.** `App.vue` wraps the content zone as `RouterView → <Transition mode="out-in" appear> → <KeepAlive> → <component :is="Component" class="h-100">`. `<Transition>` can only animate a single root element; a **multi-root** view template (e.g. `<PageLayout>` followed by sibling `<VDialog>`s) is a fragment → Vue warns `Component inside <Transition> renders non-element root node that cannot be animated`, the 1st visit works (`appear` mounts directly) but every **revisit goes blank** (the out-in leave→enter handoff breaks over the cached fragment). Fix = keep one root: put `<VDialog>`s (incl. custom `<VDialog>`-rooted wrapper components) **inside** `<PageLayout>` (they teleport to `<body>`, so DOM position is irrelevant). Swept codebase-wide 2026-06-04; none remain. **Convention gotcha:** PageLayout's direct child is indented at the SAME 2 spaces as `<PageLayout>` itself (not 4), so a sibling root after `</PageLayout>` is the tell, not indentation. When adding a new routed view with dialogs, keep them inside the single root.

## Icons

- Library: `@tabler/icons-vue`
- Type: `FunctionalComponent<SVGAttributes>` = `TablerIcon`
- `markRaw()` not needed — Tabler icons satisfy Vuetify's `JSXComponent`.
- Pass directly to Vuetify props: `:icon="IconArrowLeft"`, `:prepend-icon="IconBriefcase"`.
- **Never use `mdi-*` (or any string icon name)**: MDI is not installed and Tabler icon set is registered without string aliases. `prepend-icon="mdi-magnify"` renders blank. For props that only accept a string, use the `#prepend-inner` / `#prepend` / `#append` slot with a Tabler component instead:
  ```vue
  <VTextField clearable>
    <template #prepend-inner><IconSearch :size="16" /></template>
  </VTextField>
  ```

## Color tokens (single source = hex)

- `web/src/styles/main.scss` `:root` — **all** design tokens (`--bg`, `--surface`, `--surface-hi`, `--input-bg`, `--border`, `--border-soft`, `--sidebar-bg`, `--text*`, `--accent*`, `--warn*`, `--error*`, `--success*`, `--info*`) **in hex**.
- `web/src/plugins/vuetify.ts` `theme.themes.dark.colors` — same values in hex (for Vuetify rgba-overlays and components with a `color` prop). Update both places together.
- **Do not** use `oklch()` for new tokens. Until 2026-05-08 tokens were in `oklch()` and drifted from Vuetify-hex; `oklch(0.13)` reads as "13% gray" but renders ≈ `#05080B` (near-black).
- Legacy block: `:root` has a `// TODO: refactor — extracted oklch literals ...` section with `--legacy-*` vars (light text-on-tint, alpha-tints, `--legacy-info-blue*`, `--legacy-tooltip-bg`, `--legacy-flyout-bg`, `--legacy-scrollbar-thumb-hover`). Used in alert/badge/outlined-error/scrollbar/tooltip/flyout. Pending hex conversion.

### OKLCH → hex utility (Ottosson)

```python
import math
def oklch_to_hex(L, C, h_deg):
    h = math.radians(h_deg); a = C*math.cos(h); b = C*math.sin(h)
    l_ = L + 0.3963377774*a + 0.2158037573*b
    m_ = L - 0.1055613458*a - 0.0638541728*b
    s_ = L - 0.0894841775*a - 1.2914855480*b
    l, m, s = l_**3, m_**3, s_**3
    r  =  4.0767416621*l - 3.3077115913*m + 0.2309699292*s
    g  = -1.2684380046*l + 2.6097574011*m - 0.3413193965*s
    bl = -0.0041960863*l - 0.7034186147*m + 1.7076147010*s
    def srgb(u):
        u = max(0.0, min(1.0, u))
        return 12.92*u if u <= 0.0031308 else 1.055*(u**(1/2.4)) - 0.055
    R, G, B = round(srgb(r)*255), round(srgb(g)*255), round(srgb(bl)*255)
    return f'#{R:02X}{G:02X}{B:02X}'
```

## Theme architecture

### `!important` only for inline styles

Vuetify writes `background` onto `.v-application` and `.v-navigation-drawer` as an inline style via JS — that's the only place `!important` is needed. All other Vuetify styles live in `@layer vuetify-components`; our unlayered CSS beats them WITHOUT `!important`.

### `vuetify.ts` defaults

- `VTextField/VSelect/VAutocomplete/VCombobox/VTextarea/VNumberInput → variant: 'outlined'`
- `VCheckbox/VSwitch/VRadio → color: 'primary'`; `VSwitch → inset: true`
- `theme.variables`: `high-emphasis-opacity: 1`, `medium-emphasis-opacity: 0.6`, `border-opacity: 1`, `field-border-opacity: 1`, `hover/focus/selected/activated/pressed-opacity`
- Theme colors: `primary: #008890` (accent, teal), `success: #4caf50` (green, distinct from primary), `error: #F95053`

### Selection controls (VCheckbox/VSwitch/VRadio)

Do NOT override icon colors via CSS — it breaks the `color` prop. Vuetify drives color via the theme. Only font and opacity on `.v-label`.

### Field height

`--v-input-control-height` on `.v-input` does NOT work — Vuetify also sets this var on `.v-field` (closer to `.v-field__input` in DOM), and the nearest-ancestor variable wins. Solution: `min-height: 36px` directly on `.v-field__input`.

## Vuetify 4 — deprecated props

- **`VRow dense`** → `<VRow density="comfortable">`. The boolean `dense` prop is removed in Vuetify 4; use the `density` prop instead.

## Vuetify 4 / CSS gotchas

- **`@layer` cascade** — Vuetify places ALL its styles in `@layer vuetify-components`. Any unlayered CSS (our `main.scss`) beats layered rules regardless of specificity. Means: our `.v-btn { border-radius }` beats even a more specific `.v-btn-group .v-btn { border-radius: 0 }` from Vuetify. Solution — mirror needed rules outside `@layer`. Details: `AGENTS/docs/vuetify-css-patterns.md`.
- **`VMain` height (Vuetify 4)** — no `.v-main__wrap`. `VMain` has `flex: 1 0 auto` (shrink: 0) and grows past the viewport. Fix: `height: 100%` on `.main-content` (the `VMain` class in `App.vue`). Without it `scroll-y` doesn't work.
- **`VListItem`** — CSS grid, not flex. Centering icon in collapsed mode requires `grid-template-columns: 1fr` + `justify-self: center` on prepend.
- **`VListGroup` in nav mode** — children get `padding-inline-start: calc(16px + 56px)` = 72px. Direct override needed: `.v-list-group__items > .nav-item { padding-inline-start: 24px !important }`.
- **Sidebar nav text color** — `.nav-item` has `color: var(--text-muted) !important`, but Vuetify renders the label inside `.v-list-item-title` which has its own `color: var(--text)`. `!important` only beats specificity on the same element. Result: visible nav text = `--text` (`#D0D3D6`), not `--text-muted`. When styling "like a nav item" — use `--text`.
- **`VField` variants / padding-top** — `outlined` uses `center-affix` (label inside border, affixes centered). `filled` and `underlined` reserve `--v-field-input-padding-top` for the floating label. Our `padding-top: 8px !important` breaks that — restore for filled/underlined: `padding-top: var(--v-field-input-padding-top) !important`. `plain` — only `placeholder`, never `label`.
- **`VTextField` suffix/prefix** — Vuetify (in `@layer`) gives suffix `min-height: 56px` and `padding-bottom: 16px` for the floating label. For `v-field--center-affix` (outlined, `VNumberInput`) that swells the field to 56px. Fix: `padding-top/bottom: 0 !important; min-height: unset !important; align-self: center` on `.v-field--center-affix .v-text-field__suffix, .v-text-field__prefix`.
- **`VNumberInput`** — built-in Vuetify 4 component. `control-variant`: `default` (chevron row, flex-row), `stacked` (chevron column, flex-column-reverse), `split` (± at edges). Buttons render as `v-btn--size-small/default` — our `height: px !important` breaks flex. Fix: `height: unset; min-height: unset; flex: 1 !important` on `.v-number-input .v-number-input__control .v-btn`. Details: `AGENTS/docs/vuetify-css-patterns.md`.
- **`underlined` variant** — `background: transparent !important` (like `plain`). Requires restoring `padding-top: var(--v-field-input-padding-top) !important` analogously to filled.
- **`VSwitch` — three broken SASS variables**: (1) `$switch-thumb-background` — Vuetify 4 hardcodes `rgb(var(--v-theme-surface-bright))` in SASS; (2) `$switch-thumb-offset` — doesn't affect translation; container (ripple zone) stays 40px regardless of thumb size; (3) translation ±12px is compiled from default sizes and not recomputed. Solution — CSS overrides: color via `:has()`, thumb `background: #fff`, translation manually. Formula + details: `AGENTS/docs/vuetify-css-patterns.md`.
