---
name: vuetify_field_size_density
description: Field height = density axis globally (default 36 / comfortable 32 / compact 28px); Vuetify inputs have no size prop
metadata: 
  node_type: memory
  type: reference
  originSessionId: bfbd541c-8237-49c3-a4e3-e03080dc70c5
---

Vuetify inputs have **no `size` prop** (unlike VBtn) — field height is the `density`
axis. `main.scss` sets `.v-field__input` min-height + vertical padding per density
class, **globally for every `v-field`** (select/text/number/date): `default` 36px ·
`comfortable` 32px · `compact` 28px (Vuetify semantics: default = tallest, steps shrink).
Previously a hardcoded `min-height: 36px` flattened all three to 36px — removed.

Consequence: any `density="compact|comfortable"` field across the app genuinely shrinks
(e.g. VDateInput default=compact → 28px). Base block = default; density steps sit AFTER
the `.v-field` block (equal specificity → source order wins). Detail + rationale:
[[design-system]] doc `AGENTS/docs/frontend/design-system.md` → Custom styling.
Related: [[vuetify_select_chips_default]].
