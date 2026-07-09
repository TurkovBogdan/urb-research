---
title: Interface responsive adaptation
date: 2026-06-06
status: in-work
description: "Make page interiors (not just navigation) responsive. First step: a design-system 'Responsive' section documenting breakpoints with a live current-breakpoint indicator. Per-view adaptation follows via browser debugging at fixed widths."
tags: [web, design-system, responsive]
---

## Task

Start adapting the interfaces (page content, after the navigation work in
`2026-06-06-mobile-navigation`). User will open 4 browser tabs at fixed widths
for debugging. Before that: add a "Responsive" (Адаптация) section to the design
system right after colors — a page listing the breakpoints + a live panel that
shows the current breakpoint with distinct colors.

## Context

Navigation is already responsive (`mobileBreakpoint: 'md'`, overlay drawer + top
bar below 960px). Page interiors are not yet adapted. A breakpoints reference
page gives a shared vocabulary and a live indicator for the per-view tuning that
follows. Design-system catalog lives in `web/src/views/design-system/`, grouped
in `DesignSystemIndexView.vue`, routed in `router/design-system.ts`, i18n in
`locales/design-system/{ru,en}.json`.

## What was done

- New group `responsive` in `DesignSystemIndexView.vue`, placed right after
  `basics` (where the colour tokens live), with one page `breakpoints`
  (icon `IconDeviceMobile`).
- New page `views/design-system/responsive/BreakpointsView.vue`:
  - **Live indicator** — `useDisplay()` (`name`/`width`/`mobile`/`mobileBreakpoint`),
    a colour-coded badge that recolours per active breakpoint, current width in
    px, and a mobile/desktop chrome pill.
  - **Reference scale** — all six Vuetify breakpoints (xs…xxl) with ranges,
    device labels and per-breakpoint colours; the active one is highlighted; a
    dashed marker sits on the `md` boundary (the mobile-chrome threshold).
- Route `/design-system/breakpoints` (admin-gated like the rest of the DS).
- i18n ru + en: group `responsive`, index page `breakpoints`, page
  title/description, section keys (`current`/`scale`/`mobileChrome`/
  `desktopChrome`/`mobileThreshold`/`note` + `device.{xs..xxl}`).

### conversation_insights reports (browser-debugged at 360 / 600 / 960 / 1280px)

- **Reports index** (`ReportsIndexView.vue`) — grid was hard-wired
  `repeat(3, minmax(0,1fr))`, so on phones the cards crushed to ~110px and text
  wrapped one word per line. Made it collapse by Vuetify breakpoints: 3 cols →
  2 (`@media max-width:959px`) → 1 (`@media max-width:599px`).
- **PieChart** (`components/chart/PieChart.vue`) — the side legend was clipped by
  the card edge on narrow containers (visible even at md=4 / 960px: only the
  colour dot showed, names + percentages ran off-card). Added a `narrow` state
  (wrapper width `< height + 160`, measured by the existing ResizeObserver):
  the chart stacks vertically and the legend becomes a centred wrapped row
  underneath. Fixed height drops to `min-height` so the wrapper grows for the
  legend. Shared component — also improves the design-system donut showcase.
- **Volume report** — only needed the PieChart fix; KPI grid (`auto-fit`),
  filter bar (`flex-wrap`), bar charts (responsive SVG) and the VRow/VCol
  distribution + donut layouts already adapt.
- **Countries report** — world map + per-continent maps scale fine; the data
  table fits whole at ≥600px and **horizontally scrolls** at 360px (Vuetify
  `.v-table__wrapper` default). Left as-is for now per the user — a sticky
  country column / card layout is a possible later refinement.

### PageLayout BEM block + container padding (mobile)

- The global content padding was a hard-wired `pa-6` (24px all sides) in
  `PageLayout.vue` — too large on phones, and the component carried its structure
  as inline utility classes with no SCSS home. Created a proper BEM block in
  `web/src/styles/layout.scss` — `.page-layout` with `&__top`/`&__bottom`
  (`flex-shrink:0`), `&__content` (`flex-grow:1`) and the padding modifier
  `&__content--padded`: `padding: var(--page-layout-pad, 24px)`, dropping to
  `16px` below `md` (≤959px, the mobile-chrome cutoff). One knob — a page
  overrides by setting `--page-layout-pad` in its own scope (wins over both
  fallbacks). `PageLayout.vue` now uses the BEM classes (utilities `d-flex/
  flex-column/h-100/overflow-hidden/flex-shrink-0/flex-grow-1` removed from the
  template); `layout.scss` imported in `main.ts` after `main.scss`. The
  design-system `LayoutView.vue` doc snippet updated to the new class names.

### conversations list (observed)

- Filter panel adapts fine (`2fr+5×1fr` → 3 cols <1200px → 2 cols <720px,
  search full-width). Table keeps all 8 columns in the DOM (~1410px wide) and
  horizontally scrolls on narrow widths (Vuetify default) — showing a column
  prefix per width. Subject cell `width:360` overflow at 360px noted; table
  treatment still TBD (the filter moved into the action sheet, below).

### Mobile action sheet — cross-page FAB + bottom sheet (killer feature)

A reusable mobile pattern: a page registers a panel; on mobile a FAB appears
bottom-right and slides up a bottom sheet holding that panel. First consumer:
the conversations filter panel.

- **`layout/store.ts`** — `mobileActions*` state: `Active` (FAB visible),
  `Open` (sheet up), `Icon` (FAB glyph, `shallowRef`), `Component` (panel to
  render, `shallowRef`), `Count` (badge). `registerMobileActions(icon, component)`
  / `clearMobileActions()`.
- **`layout/useMobileActions.ts`** (new) — `useMobileActions({ icon?, component,
  count? })`. Registers on `onMounted`+`onActivated`, clears on
  `onDeactivated`+`onUnmounted` (KeepAlive-aware; `out-in` guarantees no owner
  overlap). `count` is a `MaybeRefOrGetter` kept in sync via a watch.
- **`App.vue`** — hand-rolled slide-up sheet (scrim + panel + grip) gated on
  `mobile && !fullscreen`, rendering `<component :is="mobileActionsComponent">`;
  FAB = `VBadge`(count) wrapping a circular `VBtn icon` with the registered glyph.
- **`features/conversations/components/ConversationsFilters.vue`** (new) — the
  filter panel extracted from the view (reads the list+dicts stores directly, no
  props). Owns the search debounce + a watch resyncing the input when
  `store.search` is set elsewhere (author-link / clearFilters). Grid: 6-per-row
  (≥1200) → 3 (md..lg) → **1 column below md** (≤959px), so in the mobile sheet
  every field sits on its own line (inline panel renders only ≥960, so the 1-col
  rule only affects the sheet).
- **`ConversationsView.vue`** — registers `useMobileActions({ icon: IconFilter,
  component: ConversationsFilters, count: () => store.activeFilterCount })`;
  renders `<ConversationsFilters v-if="!mobile">` inline on desktop. `filterByAuthor`
  now writes `store.search` (the filters component resyncs). `list.store.ts` got
  an `activeFilterCount` getter for the badge.

**Key gotcha (cost two failed attempts):** the first design used
`<Teleport :disabled="!mobile">` from the page into a sheet target. Teleporting
out of a `KeepAlive` + `<Transition mode="out-in">` page corrupts Vue's block
patch → `TypeError: Cannot read properties of null (reading 'emitsOptions')` in
`shouldUpdateComponent` (185+ errors, FAB/badge never patch in), plus
`Invalid Teleport target on mount: null` (the target sat after `<VMain>` in
App's template, so it didn't exist when the page mounted). Fix = **don't
teleport**: register a COMPONENT and render it with `<component :is>` in App.
See memory [[mobile-action-sheet-pattern]].

### Standardized table footer — `TablePaginationBar` (responsive)

The table footer (`"{range} of {total}"` + per-page `VSelect` + `VPagination`)
was hand-copied **identically** into ~14 list views (conversations, participants,
mail_sync ×2, twenty ×3, intercom ×2, agents ×2, conversation_insights processed,
core_monitoring task-runs) — same markup, same `.pagination-bar`/`.pagination-count`
CSS, differing only by the i18n namespace of `of`/`per_page`. Extracted into a
single component:

- **`web/src/components/TablePaginationBar.vue`** (new) — props `page` /
  `pageSize` / `total` / `pageCount` (+ optional `pageSizes` default
  `[25,50,100,200]`, `divider` default true); emits `update:page` /
  `update:pageSize` (drop-in for the old explicit handlers — the view keeps its
  `onPageChange`/`onPageSizeChange` that call `store.load()`). Owns the leading
  `VDivider`. **Responsive** (all in `@media max-width:599px`, desktop untouched):
  - desktop = one row, range left (pushed apart by `margin-inline-end:auto`,
    replacing the old `<VSpacer/>`), selector + pager right;
  - below **sm (<600)** the row reflows via flex `order`: **pager on top** →
    **inner `VDivider`** (`.pagination-bar__split`, `display:none` on desktop) →
    **one row: range (left corner) | per-page selector (right corner)** (the
    range keeps `margin-inline-end:auto` to push the selector to the opposite
    corner). Everything left-aligned (user: centred looked bad, corners for the
    range|selector row). `VPagination total-visible` drops 5→3 via
    `useDisplay().smAndDown`.
  Verified in-browser @360 (pager/divider/corners, no overflow, 3 page buttons)
  and @1280 (single row, 5 buttons).
- i18n moved to a **global** namespace: `common.pagination.of` /
  `common.pagination.per_page` (global locales merge under `common`, see
  `plugins/i18n.ts` — NOT the root; this is why the first attempt rendered raw
  keys). Added to `locales/{en,ru}.json`.
- Migrated as canonical consumers: `conversations/views/ParticipantsView.vue` +
  `conversations/views/ConversationsView.vue` (import + `<TablePaginationBar>` +
  removed the local `.pagination-bar`/`.pagination-count` CSS).
- Drive-by: fixed the mobile action-sheet FAB aria-label in `App.vue`
  (`action.actions` → `common.action.actions`; same global-namespace bug, was an
  invisible aria-label so it slipped through).

- **Design-system showcase**: added a "TablePaginationBar — standardized footer"
  section to `views/design-system/data/PaginationView.vue` (live interactive
  component in a card + usage snippet via the `CodeBlock` component (`lang="vue"`,
  NOT a raw `<pre>`) + a note that it reflows below 600px); i18n
  `section.pagination.component`/`componentNote`, index tag. Verified.
  Drive-by on the same page: the pre-existing "custom arrow icons" example used
  `prev-icon="mdi-arrow-left"`/`mdi-arrow-right` — mdi names don't resolve in this
  Tabler-icon project, so they rendered as raw text. Switched to bound Tabler
  components (`:prev-icon="IconArrowLeft"`/`IconArrowRight`).
- **Rollout — all remaining list views migrated** (drop the inline bar → import +
  `<TablePaginationBar>` wired to the same fields/handlers, remove local
  `.pagination-bar`/`.pagination-count` CSS):
  - `twenty/{Companies,Opportunities,People}View.vue` — store-based, standard.
  - `mail_sync/{Messages,Threads}View.vue`, `intercom/{Contacts,Conversations}View.vue` — store-based, standard.
  - `conversation_insights/ProcessedConversationsView.vue` — store-based.
  - `core_monitoring/TaskRunsView.vue` — local refs; kept its
    `PAGE_SIZES=[10,25,50,100,200]` via `:page-sizes`.
  - `agents/AgentSessionsView.vue` — local refs + inline handlers
    (`@update:page="page=$event"`, `@update:page-size="pageSize=$event; page=1"`),
    `:total="sessions.length"` / `:page-count="totalPages"`, kept `v-if` guard;
    removed the now-unused `rangeLabel` computed.
  - `agents/ModelsView.vue` — same inline pattern, `:page-sizes="[50,100,200]"`,
    `:total="filtered.length"`, kept `v-if` guard.
  `vue-tsc` clean; zero `pagination-bar`/`pagination-count` left in `features/`.
  Spot-checked in-browser: ModelsView @960, MessagesView @600 (desktop branch,
  split divider hidden), keys resolve, no overflow.

**Gotcha recorded:** global locales (`locales/{en,ru}.json`) merge under the
**`common`** namespace in `plugins/i18n.ts` — a shared component must use
`$t('common.<key>')`, NOT `$t('<key>')` (the latter renders the raw key). This
bit both the footer and the earlier mobile-FAB aria-label.

### mail_sync SafeEmailBody — anti-tracking bar → `VAlert`

The "images & links hidden for tracking protection" + "show content" bar in
`features/mail_sync/components/SafeEmailBody.vue` was the one bespoke notice in
the app: a hand-rolled `.remote-bar` flex block with **hardcoded** warning hex
(`#8a6d12` / `rgba(255,193,7,.10)` / `rgb(245,166,35)` / `rgb(217,145,20)`),
while every other inline notice uses Vuetify `VAlert` (75 uses / 42 files).
Standardized it: `<VAlert color="warning" variant="tonal" density="compact"
:icon="IconAlertTriangle">` — colour now comes from the theme `warning` token
(`#D88000`, dark-correct). Kept the triangle glyph via explicit `:icon` (the
Vuetify `warning` type-icon alias is `IconAlertCircle`; mdi default would render
raw text in this Tabler project). Text + button live in a `.remote-bar__row`
flex (`flex-wrap`, button `margin-left:auto`) so on narrow widths (≤360) the
button drops to its own line under the wrapped text instead of cramping. CSS
reduced to layout only. Verified @600 + @360; vue-tsc clean.

### Design-system — new `Alerts` showcase page

`VAlert` is the de-facto inline-notice standard (75 uses / 42 files) but had **no
DS page** — which is why the mail bar was hand-rolled off-standard in the first
place. Added `views/design-system/feedback/AlertsView.vue` (`/design-system/alerts`,
first page in the **feedback** group, icon `IconAlertTriangle`):
- **Types** — success/info/warning/error (`type=`, theme tokens + Tabler type-icon
  aliases resolve correctly) + note that `:icon` overrides the glyph (default
  warning/error icon = `IconAlertCircle`).
- **Variants** — tonal (default) / outlined / flat / text.
- **Density & title** — default / compact / with `title`.
- **Closable** — `closable` + `@click:close` (ref toggle + reset).
- **With action** — the canonical mail anti-tracking pattern (`.alert-action`
  flex row: text + button, `flex-wrap` so the button drops below on narrow) +
  a `CodeBlock` (`lang="vue"`) usage snippet.
Wired: index group entry + import, router route, i18n ru+en
(`index.page.alerts` / `page.alerts` / `section.alerts.*` incl. `sample.*`).
Verified in-browser @1280 (all sections render, tokens + icons correct).

### user-profile TokensCard — narrow-width head/row reflow

The access-tokens block (`features/user-profile/components/TokensCard.vue`) kept
its head (`.tokens-card__head`) as a single flex row — icon + title/desc + the
"Создать токен" button — at every width. At 360px the button held horizontal
space, so the title "Токены доступа" wrapped to two lines and the description
crushed into a thin column; the button text itself wrapped. Fix:
- `.tokens-card__id` got `flex: 1 1 auto` so the title/desc take the row width
  (base rule, harmless on desktop where the button's `margin-left:auto` still
  pins it right).
- Below **md (959px)**: head `flex-wrap:wrap`; `.tokens-card__add` →
  `flex:1 0 100%`, `margin-left:0` (full-width on its own row under the title).

**Consistency correction** (first pass was off): the reflow now mirrors the
canonical `PageHeader` actions-slot pattern exactly — same 959px breakpoint (the
app-wide mobile-chrome cutoff, `mobileBreakpoint: 'md'`) and same `width:100%`
action. The first attempt used an arbitrary 560px AND shrank card padding 24→16px
+ forced the grid to one column + reflowed the per-token revoke button — which
made the tokens card adapt differently from the identical-looking sibling cards
stacked above it (Пароль / Язык и регион, untouched at 24px). Dropped the
padding/grid/row overrides; only the head reflows now.
Verified in-browser @360 + @600 (button full-width, padding matches the Пароль
card) and @1280 (unchanged desktop single inline row). `vue-tsc` clean.

**Per-token plate restyle** (same file): the revoke button moved out of the row
head down to a dedicated `.token-row__foot` (flex, `justify-content:flex-end`) so
the head is just name + scope chip. Meta labels/values inverted to
label-emphasis: `<b>` now wraps the *label* (Создан / Использован) — bold + text
colour — and the value (date / relative time) inherits the muted `.token-row__meta`
colour (was the reverse). i18n `tokens.last_used` shortened «Последнее
использование» → «Использован» (en «Last used» → «Used»). `.token-row__name` got
`min-width:0` so a long name truncates with the chip staying put. Gotcha: a first
attempt pulled the button flush-right with `margin-right:-8px`, but VCard's
default `overflow:hidden` clipped the trailing «ь» of «Отозвать» at the card edge
— dropped it. `vue-tsc` clean.

## Result

`vue-tsc --noEmit` clean. Files:
- `web/src/features/mail_sync/components/SafeEmailBody.vue` (anti-tracking bar → `VAlert`)
- `web/src/views/design-system/feedback/AlertsView.vue` (new — `VAlert` showcase)
- `web/src/views/design-system/DesignSystemIndexView.vue` (feedback group += `alerts`)
- `web/src/router/design-system.ts` (route `/design-system/alerts`)
- `web/src/locales/design-system/{ru,en}.json` (alerts i18n)
- `web/src/views/design-system/responsive/BreakpointsView.vue` (new)
- `web/src/router/design-system.ts` (route)
- `web/src/views/design-system/DesignSystemIndexView.vue` (group + icon import)
- `web/src/locales/design-system/ru.json`, `.../en.json` (i18n)
- `web/src/features/conversation_insights/views/ReportsIndexView.vue` (responsive grid)
- `web/src/components/chart/PieChart.vue` (legend stacks below on narrow)
- `web/src/styles/layout.scss` (new — `.page-layout` BEM block + responsive padding)
- `web/src/main.ts` (import layout.scss)
- `web/src/layout/templates/PageLayout.vue` (BEM classes, utilities → SCSS)
- `web/src/views/design-system/basics/LayoutView.vue` (doc snippet updated)
- `web/src/layout/store.ts` (mobileActions state)
- `web/src/layout/useMobileActions.ts` (new — registration composable)
- `web/src/App.vue` (mobile action sheet + FAB; aria-label i18n key fix)
- `web/src/components/TablePaginationBar.vue` (new — standardized responsive footer)
- `web/src/locales/{ru,en}.json` (`common.pagination.{of,per_page}`)
- `web/src/views/design-system/data/PaginationView.vue` (showcase section)
- `web/src/locales/design-system/{ru,en}.json` (showcase i18n + index tag)
- 13 list views migrated to `<TablePaginationBar>`:
  `conversations/{Conversations,Participants}View`, `twenty/{Companies,Opportunities,People}View`,
  `mail_sync/{Messages,Threads}View`, `intercom/{Contacts,Conversations}View`,
  `conversation_insights/ProcessedConversationsView`, `core_monitoring/TaskRunsView`,
  `agents/{AgentSessions,Models}View`
- `web/src/features/conversations/components/ConversationsFilters.vue` (new — extracted panel)
- `web/src/features/conversations/views/ConversationsView.vue` (register + inline-on-desktop)
- `web/src/features/conversations/stores/list.store.ts` (`activeFilterCount`)
- `web/src/locales/{ru,en}.json` (`action.actions`)
- `web/src/features/user-profile/components/TokensCard.vue` (narrow-width head/row reflow)

Next: continue per-view adaptation of other sections (conversations table
treatment pending a decision); revisit the 360px countries table if a non-scroll
treatment is wanted.
