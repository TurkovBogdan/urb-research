---
title: Settings pages — cards in columns with capped width
date: 2026-08-27
status: completed
description: "«Настройка сервера» (/settings/core) and «Настройка модулей» (/settings/modules) laid their cards out as one full-width stack. Both switched to a capped-width grid of columns with content-height cards."
tags: [frontend, core_setup, settings]
---

## Task

«Раздел настроек, давай ограничим ширину карточек и настроим их отображение колонками. Так-же
подгоним их по высоте автоматически.»

## Context

`features/setup/views/SetupView.vue` rendered the ENV groups as `d-flex flex-column ga-4` — every
card stretched to the full content width (~930px at the default window), so a label sat at the far
left of a line whose input ended at the far right, with nothing in between.

## What was done

Replaced the stack with a grid in the view's own scoped styles (no markup logic changed beyond the
wrapper class):

```css
grid-template-columns: repeat(auto-fill, minmax(320px, 440px));
align-items: start;
justify-content: start;
gap: 16px;
```

- **440px column cap** — an input wider than that gets harder to scan, not easier, so surplus width
  goes to a neighbouring column instead of stretching the card. The number is chosen so **two**
  columns fit the typical ~930px content width: 460 would need 936px for a pair and collapse the
  layout back into a stack.
- **`align-items: start`** — each card is as tall as its own content. Without it the grid stretches
  every card in a row to the tallest one and leaves empty floor under the short ones.
- **One column under 700px** — below that two columns squeeze the fields past readability.

## Result

Changed: `web/src/features/setup/views/SetupView.vue` (wrapper class + scoped styles), `web/dist`
rebuilt.

Checked in an isolated browser at three widths: 1233px → 2 columns, 1800px → 3 columns, 640px → a
single column with the mobile app-bar. `vue-tsc` 0, `uv run pytest --all` 558 passed, 3 skipped
(the page has no tests of its own — it is markup only).

**Trade-off left in place:** cards keep their natural height, so when a row's cards differ in height
the shorter one leaves a gap before the next row starts. Packing them tightly would need a masonry
flow (`column-count`), which changes the reading order to top-to-bottom-per-column and lets columns
stretch past the 440px cap. Say the word and I'll switch.

## Second page — /settings/modules

Same treatment on `features/settings/views/SettingsView.vue` (`.modules-grid`, identical rules).
The height difference is starker here: «Сервисы» carries nine connector keys while «Веб-поиск» has
five fields, and the old stack made the short card no shorter — now it ends where its content does.

Checked at 1233 / 1800 / 640px. Only two modules currently expose settings, so even a 1800px window
shows two columns — the grid will use more as modules gain settings. `vue-tsc` 0,
`uv run pytest --all` 562 passed, 3 skipped, `web/dist` rebuilt, console clean.
