---
name: vuetify_select_chips_default
description: VSelect/VAutocomplete/VCombobox render selection chips by default (global Vuetify default); how single-select is neutralized and how to opt out
metadata: 
  node_type: memory
  type: project
  originSessionId: bc4974ae-079c-4b95-91cc-e6503b485e97
---

`vuetify.ts` defaults set `chips:true, closableChips:true` on `VSelect`/`VAutocomplete`/`VCombobox` so **multi-selects render styled selection chips by default** (no per-usage props). Vuetify has **no conditional default**, so two side-effects are handled in `main.scss` (Chips block):

- **Single selects** also get wrapped in a chip → CSS neutralizes `.v-select--single` / `.v-autocomplete--single` / `.v-combobox--single .v-chip` back to plain 13px text (transparent bg, no border/padding, `.v-chip__close{display:none}`, **`pointer-events:none`** so a click on the value text reaches the field and opens the menu — without it the chip swallows the click). Plus `.v-chip__underlay` killed globally (selected-state tint).
- **Multi-select chips** styled via `.v-select--multiple/...--multiple .v-chip` (`--surface-hi` bg, `--border`, muted close).

**Gotcha:** when `chips` is true Vuetify **ignores the `#selection` slot** (chips branch wins). A multi-select wanting custom/compact selection display (e.g. "+N" count) **must pass `:chips="false"`** — see the compact filters in `ProcessedConversationsView` (is_commercial, tags).

DS reference page: `/design-system/selects`. Task: `[[2026-06-07-ds-multiselect-chips-default]]`.
