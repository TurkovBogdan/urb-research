---
title: design-system i18n — translate catalog, page headers, section headings
date: 2026-05-31
status: completed
description: "Add ru/en i18n to the design-system showcase feature: translate the index catalog (groups + page labels + descriptive tags), each page's title/description, and the in-example section headings — while converting all in-card demo content to static English. Second per-feature i18n migration after core_geo."
tags: [frontend, i18n, design-system]
---

## Task

> Add language support to the design-system feature. Translate: the catalog list, each page's title + description, and the section headings inside examples (the cards like Variants/States/With icons). Do NOT i18n the example content — everything inside the cards is plain English.

User-confirmed boundaries (AskUserQuestion):
- **In-card content** (button labels, spec/caption text, demo strings, descriptive `ds-label` captions) → rewrite to **static English** (no i18n); identifiers / component names / prop names / CSS classes stay literal.
- **Index tags** → translate descriptive ones ("Color palette"), keep component/identifier names literal (`VBtn`, `:prepend-icon`).

## What was done

- **Locale dictionaries** `features/design-system/locales/{ru,en}.json`, namespace `design-system` (hyphen in the namespace resolves fine through `t()`/`tm()` — vue-i18n treats `-` as a literal path-segment char). Buckets:
  - `nav` — sidebar label (wired via `nav.ts` `labelKey: 'design-system.nav'`).
  - `index.title`/`index.description`, `index.group.<key>` (7 groups), `index.page.<slug>.{label,tags[]}` (23 pages). Tags are arrays — rendered with `tm()` + `rt()` in the index view.
  - `page.<slug>.{title,description}` — the 23 detail pages' `PageHeader`.
  - `section.<slug>.<key>` — the in-example section/card headings, for the 20 pages that have categorical `<h6>` headings. Component-name prefixes are baked into the value (e.g. `"VBtnToggle — single select"`), so the whole heading text is one key.
- **Index view** `DesignSystemIndexView.vue` rewritten: `groups` now hold `{ key, pages:[{ slug, icon }] }`; labels/tags/group-names come from i18n; card route is `/design-system/${slug}`.
- **23 detail views** wired (`useI18n` + `t()`): `PageHeader` title/description → `t('design-system.page.<slug>.…')`; categorical section headings → `t('design-system.section.<slug>.…')`. All remaining Russian inside example cards (button labels, `ds-spec`/`ds-label` captions, demo sample text, paragraphs, and Russian HTML/CSS comments) converted to **static English**. Identifiers, component names, prop names, CSS class/token names, code snippets, and already-English mono tags left untouched.
- **Three caption-only pages** (`tables`, `line-chart`, `world-map`) have no `section.*` keys — their `ds-label` strings are descriptive example captions and became static English; only title/description are i18n.

Delegated the 23 view edits to parallel sub-agents (one file each, reading the shared locale for exact keys, never editing it) after authoring the locale centrally.

## Result

design-system feature is bilingual exactly per the requested split. `vue-tsc --noEmit` clean. Verified in-browser: index catalog (groups/labels/tags) switches ru↔en with no raw keys leaking; `/design-system/buttons` in RU shows translated title ("Кнопки") + section headings ("Варианты", "С иконками", …) while in-card content stays English ("Primary", "primary action", "neutral / destructive"). Memory: [[i18n_frontend_setup]]. Doc: `AGENTS/docs/i18n.md`.
