---
title: DS code-block page — bring under current styles
date: 2026-07-04
status: completed
description: "Migrate the design-system CodeBlock page to the current DS-page layout (card-per-section), matching MessageContent and the other current pages."
tags: [frontend, design-system]
---

## Task

«http://127.0.0.1:12100/design-system/code-block — посмотри оформление в браузере, поправь под текущие стили».

## Context

`CodeBlockView.vue` (last touched Jun 5) still used the old DS-page pattern: floating uppercase `<h6 class="mb-3">` section headers over bare `.ds-section` blocks, with only the props table sitting in a bordered `.ds-card` div. The current pages (e.g. `MessageContentView.vue`, Jun 24) wrap every section in a padded `VCard class="ds-card"` with an `h6.ds-card__title`, and lay `.ds-page` out as a `flex column; gap: 20px`.

## What was done

- `web/src/views/design-system/content/CodeBlockView.vue`:
  - Every section (props, demo, all-variants, languages) now wrapped in `<VCard class="ds-card">` with `<h6 class="ds-card__title">` instead of `<section class="ds-section"><h6 class="mb-3">`.
  - The props table renamed to a nested `.ds-props` bordered block (was the outer bare `.ds-card` div) so the card border is provided by VCard, not a hand-rolled surface div.
  - `.ds-page` switched to `flex column; gap: 20px` (kept `max-width: 860px`); dropped `.ds-section` margin spacing.
  - `.ds-card` now just `padding: 16px`; added `.ds-card__title { margin: 0 0 12px }` and `.ds-props`; variant labels use flex gap + `display: block` (removed the `mb-2` util on `.ds-tag`).
- `web/src/composables/useHighlighter.ts`: Shiki theme `github-light` → `github-dark` (both the `createHighlighter` themes array and the `codeToHtml` call). The app is dark-only (`vuetify.ts` `defaultTheme: 'dark'`, no light theme), so the light theme rendered near-black tokens on the dark `--surface` — code text was invisible. Affects every CodeBlock across the app, not just the DS page.

## Problems

After the restyle the user pointed out the demo code was unreadable — the highlighter was hardcoded to the light `github-light` theme on the app's dark surface. Fixed by switching to `github-dark`.

## Result

Page now matches the current DS card-per-section layout, and code is readable on the dark theme — both verified in the browser. Changed: `web/src/views/design-system/content/CodeBlockView.vue`, `web/src/composables/useHighlighter.ts`. `web/dist` not rebuilt (no pnpm on PATH; dev via Vite).
