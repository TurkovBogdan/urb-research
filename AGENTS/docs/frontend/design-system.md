# design-system.md — showcase pages, coverage, custom styling

Status of the `/design-system/` showcase: page inventory, component coverage matrix, and the non-obvious `main.scss` overrides the demos depend on.

## Design system pages (`/design-system/`)

37 showcase pages (+ index) registered in `routes.ts` + `nav.ts`, grouped by section:
- **basics**: tokens, typography, layout
- **controls**: buttons, button-group, selects, inputs, numbers, toggle, sliders, date-pickers
- **feedback**: loaders, status-badge, dialogs, tooltips, skeleton, alerts, chips, switch-panel
- **data**: pagination, table, data-table, task-status, world-map
- **content**: code-block, markdown
- **charts**: line-chart, bar-chart, pie-chart
- **structure**: cards, dividers, file-cards, spoiler
- **interface**: kanban, edge-scroller
- **responsive**: action-panel, breakpoints

`date-pickers` covers all 4 scenarios: single date (VDateInput),
time (VTextField+VMenu→VTimePicker), datetime (VDateInput+VTimePicker),
range (VDateInput multiple="range" + paired VDateInput with :min/:max).

## Design system patterns

- `plain` variant — always `placeholder`, never `label` (label drifts sideways)
- `underlined` variant — `background: transparent`, needs `padding-top: var(--v-field-input-padding-top)`
- Pages use grid `.ds-row { grid-template-columns: 100px 1fr 200px }` — tag/control/spec
- All fields: `variant="outlined"` as primary, `hide-details` by default (except error/hint rows)
- VNumberInput: `control-variant="stacked"` + `inset` for compact fields (salary, budget)

## Vuetify defaults (vuetify.ts)

VDateInput, VDatePicker, VTimePicker all default to `color: 'primary'`.
VTimePicker default `format: '24hr'`. VDatePicker default `showAdjacentMonths: true`.
Without these, selected day cells get `--selected` class but no accent fill —
must be styled directly.

## Custom styling — non-obvious overrides in main.scss

- **Field size = `density` axis**: Vuetify inputs have no `size` prop (unlike VBtn),
  so height is driven by `density`. `main.scss` sets `.v-field__input` min-height +
  vertical padding per density class, globally for ALL fields (select/text/number/date):
  `default` 36px · `comfortable` 32px · `compact` 28px (Vuetify semantics: default is
  the tallest, steps shrink down). Base block = default; `.v-input--density-comfortable`
  / `.v-input--density-compact` override below it (placed AFTER the `.v-field` block so
  equal-specificity rules win by source order). filled/underlined keep their reserved
  top padding (floating label) — density rules touch only their padding-bottom. Demo:
  `/design-system/selects` → "Sizes" section.
- **Date picker selection**: `.v-date-picker-month__day--selected .v-btn` gets
  `--accent` background directly (Vuetify doesn't add `bg-primary` class).
  Range "bridge" between adjacent selected days drawn via `::before` with
  `--accent-soft`; a `:has(--selected + --selected)` selector disables the
  bridge for single-date selection. No "today" outline (was visually noisy).
- **Time picker accent**: clock hand, active hour/minute number, active time
  field — all need explicit `--accent` overrides.
- **Default tooltip**: Vuetify's default `.v-tooltip > .v-overlay__content`
  is white-on-white invisible. Overridden to dark `--legacy-tooltip-bg`,
  white text, shadow `0 6px 20px rgba(0,0,0,.18)`, max-width 320px.
  `.sidebar-tooltip` (with arrow) still works separately for collapsed sidebar.

## Next candidates

- Snackbar / Alert (toast notifications)
- Tabs (VTabs)
- Chips (VChip) — tags/filters
- Menu / Dropdown (VMenu)
