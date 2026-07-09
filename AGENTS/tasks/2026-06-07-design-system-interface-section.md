---
date: 2026-06-07
status: completed
---

# Design system — «Интерфейс» section (composed interfaces)

## Goal

New design-system group **«Интерфейс»** holding ready-made complex interface compositions (not single components). First page: a **kanban board** — cards laid out in columns with horizontal scroll.

## What was done

- New group `interface` in `DesignSystemIndexView.vue` (icon `IconLayoutKanban`).
- Page slug `kanban` → route `/design-system/kanban` (`interface/KanbanView.vue`). Slug `board` reserved for a future different layout per user.
- **`EdgeScroller`** `web/src/layout/components/EdgeScroller.vue` — generic horizontal-scroll wrapper extracted from the kanban work (reusable for any wide content: kanban track, tables, …). Slot = content; `.edge-scroller__content` is `width:max-content` (overflow + observable). Scroll state via `@scroll` + one `ResizeObserver` (viewport + content).
  - **Edge shadows**: `::before`/`::after` thin casters parked just OUTSIDE each edge (`left`/`right:-10px`, `width:10px`) throwing `box-shadow: 0 0 14px 0 rgba(0,0,0,.45)` inward (soft/light); `.edge-scroller` `overflow:hidden` clips the caster + outer half so only the inward blur shows; `top:5px`/`bottom:15px` insets feather the ends + clear the bottom scrollbar. No `mask`. The shadow rendered harder when a sidebar shifted the content vs softer at the screen edge — a **subpixel/devicePixelRatio rasterization** artifact (urb-research confirmed); fixed by promoting each pseudo to its own compositing layer (`transform: translateZ(0)` + `backface-visibility:hidden`). `z-index:1` (above content), `pointer-events:none`, fade by `.show-left`/`.show-right` (= `!atStart`/`!atEnd`, 2px tol). See memory [[box-shadow-subpixel-offset]].
  - **`bleed` prop**: full-bleed to screen edges — `margin-inline: calc(-1 * var(--page-layout-pad))` (mirrors layout 24/16) + `padding-inline` on the content so the first item stays aligned with the page header at rest. Unscoped `:has(.edge-scroller--bleed)` drops `.scroll-y`'s `scrollbar-gutter: stable` so the right edge reaches the true screen edge (global `stable` kept — decided).
- **Kanban components** `web/src/components/kanban/`:
  - `KanbanBoard.vue` — now a thin wrapper: `<EdgeScroller bleed><div class="kanban-track">…</div></EdgeScroller>` (flex + gap track only).
  - `KanbanColumn.vue` — props `title`/`count`/`tone`/`addLabel`; header dot+title+count + `#actions` slot; default slot = cards; optional dashed footer emits `add`. **White tray** (`--surface` + `--border-soft`). Fixed 340px (wide enough for text blocks), and `@media (max-width: 599px)` widens it to `calc(100vw - 48px)` (≈312px @360) so phones get one near-full-width column + a peek.
  - `KanbanCard.vue` — props `title`/`tags` (tone accent/neutral/warn/ok)/`comments`/`attachments`/`assignee`/`menu` (default true → top-right three-dots; `:menu="false"` hides); slots `#menu` (replaces the dots) + default (body). Footer auto-hides when no comments/attachments/assignee. `VCard variant="outlined" link`. **Light-grey card** (`--surface-hi` + `--border-soft`); bg needs `!important` to beat the global `.v-card { background: var(--surface) !important }` in main.scss. [Color scheme: white columns / light-grey cards.]
- **New design tokens** in `main.scss`: `--surface-sunken` #DCDDDF + `--border-sunken` #CFD1D3; both in the `TokensView` showcase grid.
- **Scrollbar unify** (`main.scss`): a bled scroller left a ~2px gap next to the page's vertical scrollbar — `* { scrollbar-width: thin }` was set unconditionally, which on Chromium **disables** the `::-webkit-scrollbar` styling and reserves a wider gutter with an inset thumb. Moved `scrollbar-width: thin` under `@supports not selector(::-webkit-scrollbar)` (Firefox-only); Chromium now uses the intended flush 5px webkit scrollbar, so full-bleed content sits flush against it.
- **Showcase pages** (`interface/`): `KanbanView.vue` (board) + `EdgeScrollerView.vue` (EdgeScroller wrapping a wide `<table>` to prove genericity). Routes `/design-system/{kanban,edge-scroller}`, both in the `interface` index group; i18n en/ru.

## Result

Done. New «Интерфейс» group (pages `/design-system/{kanban,edge-scroller}`). The scroll/bleed/edge-shadow shell lives in the reusable **`EdgeScroller`** (`layout/components/`); `KanbanBoard` is a thin consumer, a wide table is the second. White columns / grey cards. `vue-tsc --noEmit` clean; both pages verified in the browser.
