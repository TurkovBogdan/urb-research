---
title: InlineEdit — content-width field that grows as you type
date: 2026-08-27
status: completed
description: "Entering title edit no longer shifts anything horizontally, and the field now sizes itself to its own text instead of taking the whole free row."
tags: [frontend, research, design-system]
---

## Task

«Компонент смены названия не должен скакать при нажатии редактирования (если влезает по ширине), и
должен автоматически расширяться при вводе.» — `web/src/components/InlineEdit.vue`, used through
`features/research/components/TitleEditor.vue` on the research / area / note pages.

## Baseline (measured live, :22040)

The component already guaranteed a stable **height** (single `--ile-height` token across rest, edit
and read-only). Width had no such guarantee: the resting text and the input were both
`flex: 1 1 auto`, i.e. the whole free row, and the pencil was pinned right by `margin-left: auto`.

Measured on the research page (title «Python: работа с базой данных»):

- rest — value 265px, pencil at x=595
- edit — input 253px, save at x=583, cancel at x=613

So entering edit moved the button 12px left and widened the row by 18px: the cancel button has to
come from somewhere, and it took it out of the field. The `grow` prop existed to soften exactly
this (animate the input from text width to full width) but was dead in practice — with the value
already spanning the row, `to <= from` and `grow()` returned early on the first line.

## What was done

`web/src/components/InlineEdit.vue`:

- **Content width in both states.** `.ile__value` and the new field wrapper are `flex: 0 1 auto`, and
  `margin-left: auto` is gone from the buttons — text, then buttons, immediately after it. The field
  opens exactly as wide as the text was, so the save button lands on the pencil's pixel.
- **Auto-grow with no JS.** The input sits in an `inline-grid` wrapper together with a hidden
  `::after` carrying `content: attr(data-value)` (`sizerText` = draft, or the placeholder when the
  draft is empty). The copy sizes the grid cell, the input follows it, so the width tracks typing.
  `min-width: 0` on both cell items is load-bearing: without it the cell cannot shrink below the
  string and a long title would overflow the buttons instead of clamping and scrolling internally.
- **`size="1"` on the input.** Found while testing: an `<input>` asks for ~20 characters of
  intrinsic width, and since the grid track is `auto`, that intrinsic width — not the text — governed
  the cell for anything shorter. An empty field measured 253px. With `size="1"` the floor drops to
  ~54px and the sizer governs everything above it.
- **`--ile-caret` (2px)** carried by *both* the resting text and the field: the field needs room for
  the caret past the last character, and the resting text needs the same allowance or the field would
  open those pixels wider. This was a residual 4px jump before the token.
- **Removed the dead `grow` machinery** — prop, `GROW_MS`, `growTimer`, `grow()`, the pre-measure in
  `start()` and the `onBeforeUnmount` cleanup. Content sizing makes the animation pointless.
- `features/research/components/TitleEditor.vue` — dropped the now-removed `grow` prop.

## Verification

`vue-tsc --noEmit` exit 0; `pnpm --dir web build` ok, `web/dist` rebuilt. Measured live on the Vite
dev server (:22041) in an isolated browser context, on all three call sites:

| page | jump on open | notes |
|------|--------------|-------|
| research (`variant="title"`, h1) | **0px** | 265 → 265 |
| note (`variant="field"` + status badge) | **0px** | badge did not move either |
| area (`variant="field"` in a card) | **0px** | left edge also unmoved |

Auto-grow: 265 → 698px while typing, buttons following. 128 `X` characters clamp at the row edge —
the cancel button stays inside the row and the input scrolls internally rather than overflowing.
Escape closes and leaves the stored title untouched.

## Problems

🔴 **A probe wrote to the dev DB.** The first measurement script left the field in edit mode; the
next script opened with `.ile__btn.click()`, which by then was the **save** button, not the pencil —
so the typed test string was persisted as the title of `RESEARCH@ac7bcfb520ca700afb1fea`. Restored
via `research_update` (MCP) to «Python: работа с базой данных»; verified in the DB. Every later probe
ends with an explicit Escape and asserts the field is closed.

Lesson for browser probes: a script that opens a stateful control must close it in the same script —
the next script inherits the page mid-state, and index-based selectors then hit a different button.

## Result

Entering edit is now motionless on all three pages, and the field tracks the text while typing. The
"if it fits by width" caveat is honoured literally: past the row width the field clamps and scrolls
inside itself instead of pushing the buttons out.

Known, accepted: a draft shorter than ~5 characters sits at the ~54px `size="1"` floor rather than
hugging the text. Titles are never that short, and the save button is disabled on an empty draft.
