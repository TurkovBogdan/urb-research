# Frontend conventions

Read this before writing or editing Vue components — Vuetify 4 component choices and `PageLayout` scroll structure. Code-shape gotchas the user enforces.

## Use VDateInput (labs), never VTextField type=date

Never use `VTextField type="date"` in Vuetify 4.

**Why:** Vuetify 4 attaches an internal click handler to the `$calendar` icon alias on date inputs. Clicking the field starts an async flow that never resolves → permanent loading spinner visible to the user.

**How to apply:** use `VDateInput` from `vuetify/labs/VDateInput` instead. It wraps `VTextField` + `VMenu` + `VDatePicker` and works correctly.

Setup in `plugins/vuetify.ts`:
```ts
import { VDateInput } from 'vuetify/labs/VDateInput'
import { ru } from 'vuetify/locale'

createVuetify({
  components: { ...components, VDateInput },
  locale: { locale: 'ru', messages: { ru } },
  defaults: {
    VDateInput: { variant: 'outlined', density: 'compact', hideDetails: true, color: 'primary' },
  },
})
```

`v-model` emits `Date` objects (not strings). Convert with local-time helpers — do NOT use `toISOString()` (UTC shift):
```ts
function parseDate(iso: string | null): Date | null {
  if (!iso) return null
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d, 12)  // noon = no UTC rollback
}
function formatDate(d: Date | null): string | null {
  if (!d) return null
  return [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-')
}
```

## Inputs inside dialogs use default density (full size)

In a `VDialog`, leave input fields and dropdowns at **default density** (full 36px height) — do not set `density="compact"/"comfortable"` on `VTextField` / `VTextarea` / `VSelect` / `VCombobox` / `VNumberInput`. Dialogs are roomy; compact fields look cramped there. Reduced density is for dense list/filter bars on a page, not for modal forms.

**Why:** density now genuinely drives field height (see task `2026-06-07-ds-field-size-density-axis`). Dialogs written before that fix carried `density="compact"` that was a visual no-op; once density became real they rendered visibly small.

**Gotcha:** `ProviderModelSelect` defaults its own `density` to `compact` via `withDefaults`. Dropping the prop at the call site does NOT restore full size — pass `density="default"` explicitly.

Checkboxes, switches, `VBtn`/`VBtnToggle`, `VAlert`, and `VList` may stay compact inside a dialog — this rule is about text inputs and dropdowns only.

## VBtnToggle for small enums (≤4 options)

For small closed enums (≤4 options) inside dialogs, use `VBtnToggle` instead of `VSelect`.

**Why:** in Vuetify 4, a `VSelect` with `variant="outlined"` inside a narrow flex row renders with a visible extra border-box around the component — it looks like a VCard nested inside the field, not a clean input. Replacing with `VBtnToggle` eliminates the artifact and looks better for small option sets.

**How to apply:** any time you have a form field with 2–4 fixed options (type selector, status, category) inside a `VDialog` or narrow layout, reach for `VBtnToggle`:

```vue
<VBtnToggle v-model="type" mandatory density="default" variant="tonal" class="type-toggle">
  <VBtn v-for="item in TYPE_ITEMS" :key="item.value" :value="item.value">
    {{ item.title }}
  </VBtn>
</VBtnToggle>
```

```css
.type-toggle { width: 100%; }
.type-toggle :deep(.v-btn) { flex: 1; height: 40px; font-size: 0.875rem; }
```

Use `mandatory` so there's always a selected value. `density="default"` + explicit `height: 40px` makes buttons the same height as other outlined fields in the form.

## VBtnGroup / VBtnToggle size is not inherited

The `size` prop set on `VBtnGroup` or `VBtnToggle` does NOT propagate to child `VBtn` components. It must be set explicitly on every `<VBtn>` inside the group.

**Why:** Vuetify 4 docs confirm only `color`, `density`, `variant`, and `height` are shared by the group context. `size` is absent from that list (verified via urb-research, May 2025).

**How to apply:** whenever writing `VBtnGroup` / `VBtnToggle` with a non-default size, add `size="..."` to every child `<VBtn>`, not to the wrapper.

## List views: filter panel, chips, sort, switch labels

**Mandatory for every list page with a filter panel, project-wide.** When you build or edit a paginated list view with filters, all four rules below are the standard; follow them unless the user explicitly overrides.

**Active-filter chips show the value only — never the field name.** Every applied filter renders a closable `VChip` on a separate `.chip-row` line under the filter grid; the chip text is the bare value (status name, mailbox, provider), not `"Field: value"`. Last in the row is a `reset_all` `VBtn`.
```vue
<div v-if="hasActiveFilters" class="chip-row">
  <VChip v-if="store.type" closable color="primary" variant="tonal" size="small" @click:close="clearType">
    {{ $t(`...type.${store.type}`) }}   <!-- value only, no "Type:" prefix -->
  </VChip>
  <!-- the blacklist / exclude switch chip uses color="error" to match its switch tone -->
  <VChip v-if="store.excludedByUser" closable color="error" variant="tonal" size="small" @click:close="store.excludedByUser = false; onFilterChange()">
    {{ $t('...filter.excluded') }}
  </VChip>
  <VBtn variant="text" size="small" :prepend-icon="IconX" @click="clearAll">{{ $t('administration.action.reset_all') }}</VBtn>
</div>
```

**Sort defaults to newest-first.** The store seeds `sortBy = <primary date column>` and `sortDir = 'desc'` so the freshest rows lead. A persisted `localStorage` filter overrides the seed — to force a reset for existing users, bump the store's `STORAGE_KEY`.

**Search scope toggles default ON.** Scope flags (`searchBody` / `searchEmail` / `searchContacts`) default to `true` in the store *and* `clearFilters()` resets them to `true`, so search covers every scope out of the box. Same `localStorage` caveat as sort.

**A filter switch label is muted when OFF.** A filter `VSwitch` (e.g. the blacklist/exclude toggle) reads full-emphasis only when ON; when OFF its label drops to medium-emphasis to match the inactive field labels (which sit at `--v-medium-emphasis-opacity`). Vuetify marks the checked state with `.v-selection-control--dirty`, so:
```css
.excluded-switch :deep(.v-selection-control:not(.v-selection-control--dirty) .v-label) {
  opacity: var(--v-medium-emphasis-opacity);
}
```

**The filter bar stays on one line — the search field is the elastic column.** The `.filter-grid` is a CSS grid where the **search input is `1fr`** (absorbs leftover width) and every other control gets a fixed `minmax(0, <px>)` track. The bar then fills the row exactly and never wraps on desktop. Do **not** give the selects fractional (`1fr`) tracks — that lets them grow and pushes the bar to a second line. Collapse to fewer columns only at width breakpoints (the search spans `grid-column: 1 / -1` there):
```css
.filter-grid {
  display: grid;
  /* search · select · select · select — search absorbs leftover space */
  grid-template-columns: 1fr minmax(0, 150px) minmax(0, 160px) minmax(0, 190px);
  gap: 12px;
  align-items: center;
}
@media (max-width: 1200px) {
  .filter-grid { grid-template-columns: 1fr 1fr 1fr; }
  .search-input { grid-column: 1 / -1; }
}
```

**Date cells never wrap — a date renders on one line.** Any table cell showing a formatted date (`fmtDateTime` over a `fmtRelative` caption) carries `white-space: nowrap` so the date stays whole and never breaks mid-value. Wrap the cell in a `.date-cell` and nowrap it:
```css
.date-cell { white-space: nowrap; }
```

## PageLayout owns scroll

When a route declares `meta.scroll: 'y'` (or `'x'`), `PageLayout` already provides the scroll container via `scrollClass(route.meta.scroll)` on `.page-layout__content`. Do not wrap the slot content in `d-flex flex-column h-100 overflow-hidden` and do not add a nested `flex: 1 1 0; overflow: auto; min-height: 0` list — it creates a competing scroll context and breaks page-level scroll.

**Why:** `McpView.vue` had this nested pattern. Inside the inner flex column children inherit `flex-shrink: 1`, so when expanded card content exceeded the inner viewport, VCards shrank vertically and their `overflow: hidden` clipped the body (tools list / dates). Removing the wrapper (let `PageLayout` scroll the whole page) is what other pages already do — Models, Agents, Tasks.

**How to apply:** in views that use `PageLayout` + `meta.scroll: 'y'`, render the content as plain block-level children of the slot. Use the header / filter bar / list as siblings — no `h-100`, no `overflow: auto` on the list wrapper. Only when a page needs to keep a fixed header with an independently scrolling area (e.g. ChatView with `scroll: 'none'`) should you build your own scroll container.
