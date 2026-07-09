---
title: Design-system Spoiler component + showcase page
date: 2026-06-17
status: completed
description: "Build a reusable collapsible Spoiler component with styling variants (default / minimal / card) and a /design-system/spoiler showcase page. Becomes the shared basis for the mail history spoiler."
tags: [frontend, design-system]
---

## Task

«Давай проработаем компонент спойлеров, создавай отдельную страницу. Учитываем что у спойлера будут темы оформления, например минимальная.»

## Context

Collapsible sections are currently done ad-hoc with Vuetify `VExpansionPanels` + per-view CSS overrides (ConversationView, MessageView, McpView). No reusable Spoiler exists. The in-work task `2026-06-17-mail-sync-body-history-spoiler` needs a collapsible to hold quoted history — this component is its shared basis. Requirement: multiple styling themes (e.g. a minimal one).

## What was done

- New reusable `web/src/components/Spoiler.vue` — clickable header (chevron + title) over `VExpandTransition` body; optional `v-model:boolean` (default closed); `title`/`#title`/`#actions` slots; `disabled`. Three styling themes via `variant`: `default` (bordered surface panel), `minimal` (borderless uppercase label), `card` (filled `surface-hi` header + border-bottom when open). Chevron rotates 90° on open. All colors from design tokens.
- New showcase page `web/src/views/design-system/structure/SpoilerView.vue` (`/design-system/spoiler`): Basic, Themes, Title & actions slots, States (disabled), Import & usage sections. Independent reactive state per demo.
- Registered: route in `web/src/router/design-system.ts`; index card (group `structure`, `IconChevronDown`) in `DesignSystemIndexView.vue`; locale keys in `locales/design-system/{en,ru}.json` (index.page / page / section blocks).
- Doc `AGENTS/docs/frontend/design-system.md` updated (37 pages; spoiler added to structure group).

No tests (frontend showcase only). `vue-tsc --noEmit` exits 0; verified live at `/design-system/spoiler` (all 3 themes render, expand/collapse + chevron rotation work, demo states independent).

## Result

- Created: `web/src/components/Spoiler.vue`, `web/src/views/design-system/structure/SpoilerView.vue`.
- Edited: `web/src/router/design-system.ts`, `web/src/views/design-system/DesignSystemIndexView.vue`, `web/src/locales/design-system/{en,ru}.json`, `AGENTS/docs/frontend/design-system.md`.

Reusable basis for the in-work `2026-06-17-mail-sync-body-history-spoiler` (quoted-history collapsible) — use `variant="minimal"`.
