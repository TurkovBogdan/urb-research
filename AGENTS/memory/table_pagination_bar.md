---
name: table_pagination_bar
description: "TablePaginationBar — standardized responsive table footer used by all 13 list views; global i18n lives under `common.` namespace"
metadata: 
  node_type: memory
  type: project
  originSessionId: 144279a2-bbde-4ada-ac7b-4165cbb590d9
---

`web/src/components/TablePaginationBar.vue` is the **standard table footer** for
every paginated list view — use it, do NOT hand-roll a `.pagination-bar` block.
Props `page`/`pageSize`/`total`/`pageCount` (+ optional `pageSizes` default
`[25,50,100,200]`, `divider` default true → owns its leading `VDivider`); emits
`update:page`/`update:pageSize` (drop-in for the old `onPageChange`/
`onPageSizeChange` handlers). Responsive (all in `@media max-width:599px`):
desktop = one row (range left via `margin-inline-end:auto`, selector+pager
right); below sm reflows via flex `order` → **pager on top → inner divider
(`.pagination-bar__split`, hidden on desktop) → range (left) | per-page selector
(right)**, and `VPagination total-visible` 5→3 (`useDisplay().smAndDown`).

Standard footer for every paginated list view. Showcased in design-system
`data/PaginationView.vue`. A view may override the page-size options.

**i18n gotcha (cost a bug):** global locales `locales/{en,ru}.json` are merged
under the **`common`** namespace in `plugins/i18n.ts` (`common: commonEn`), NOT
at the root. A shared/global component must call `$t('common.<key>')` — bare
`$t('<key>')` renders the raw key. The footer uses
`common.pagination.{of,per_page}`. Same bug had silently hit the mobile-FAB
aria-label (`action.actions` → `common.action.actions`). Feature dictionaries
are different — they merge under their feature-dir namespace
(`t('conversations.*')`). Related: [[i18n_frontend_setup]].
