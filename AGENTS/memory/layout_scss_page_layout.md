---
name: layout-scss-page-layout
description: .page-layout BEM block in styles/layout.scss owns PageLayout structure + responsive container padding
metadata: 
  node_type: memory
  type: project
  originSessionId: 144279a2-bbde-4ada-ac7b-4165cbb590d9
---

`web/src/styles/layout.scss` (imported in `main.ts` after `main.scss`) holds the
`.page-layout` BEM block — the structure of `layout/templates/PageLayout.vue`:
`&__top`/`&__bottom` (`flex-shrink:0`), `&__content` (`flex-grow:1`), and the
padding modifier `&__content--padded`.

Container padding (was a hard-wired `pa-6`): `&__content--padded { padding:
var(--page-layout-pad, 24px) }`, dropping to **16px below md (≤959px**, the mobile
chrome cutoff = Vuetify `mobileBreakpoint: 'md'`). One knob — a page tightens or
removes it by setting `--page-layout-pad` in its own scope (wins over both
fallbacks). `PageLayout.vue` applies `page-layout__content--padded` unless
`route.meta.padding === false`; the structural utility classes
(`d-flex/flex-column/h-100/overflow-hidden/flex-shrink-0/flex-grow-1`) moved out
of the template into this block. The design-system `LayoutView.vue` doc snippet
mirrors the class names.

Related: [[frontend_pagelayout_meta_snapshot]], [[mobile-action-sheet-pattern]].
