---
name: vuetify_switch_color_override
description: Vuetify VSwitch color prop was globally overridden — colored switches rendered teal/green
metadata: 
  node_type: memory
  type: project
  originSessionId: f2509464-218c-423e-9f56-63ee19f7f8b4
---

`styles/main.scss` enhances the switch ON-track with the oklch `--accent` (brighter than Vuetify's sRGB
primary). The rule must be scoped to `.v-switch:has(input:checked) .v-switch__track.bg-primary` — NOT the
bare `.v-switch__track`. Unscoped, it out-specifies Vuetify's own `.v-switch__track.bg-<color>` and clobbers
EVERY `color="success|warning|error"` switch to `--accent` (teal). Vuetify applies switch color via a
`bg-<color>` class on `.v-switch__track` (+ `text-<color>` on `.v-selection-control__wrapper`), no modifier
class on the `.v-switch` root.

The yellow «Отключить безопасный просмотр» switch (`color="warning"` = `#D88000`) needed this fix to show.
Related: [[vuetify_select_chips_default]], [[vuetify_field_size_density]].
