---
title: design-system — dissolve the feature into root template files
date: 2026-06-04
status: completed
description: "design-system is template chrome, not a domain feature. Move it out of web/src/features/ into root homes (views/router/locales), mirroring the auth lift-out."
tags: [frontend, design-system, refactor, template]
---

## Task

User: «design-system — это вообще не модуль, а часть шаблона по сути. Нужно раскидать фичу на
отдельные файлы в корне; по вьюхам это `web/src/views/design-system`».

## Context

`web/src/features/design-system/` held `views/` (26 showcase pages) + `routes.ts` + `nav.ts` +
`locales/`. Since it is template chrome (not a domain module), it shouldn't live under `features/`.
`auth` is the precedent: lifted out of `features/`, locales at `@/locales/auth/` wired explicitly in
`plugins/i18n.ts` under the stable `auth` namespace, views at `@/views/auth/`.

## What was done

- Moved (`git mv`) the 26 views → `web/src/views/design-system/`. The views use NO relative imports
  (only `@/...`), so nothing inside them changed.
- `routes.ts` → `web/src/router/design-system.ts` (root router home); rewrote the 26 lazy imports
  `./views/X` → `@/views/design-system/X`. Export `designSystemRoutes` unchanged.
- `router/index.ts`: import path `../features/design-system/routes` → `./design-system`.
- `locales/` → `web/src/locales/design-system/{ru,en}.json`; wired explicitly in `plugins/i18n.ts`
  (import + add `'design-system'` key to the `ru`/`en` message trees, like `auth`). Namespace
  `design-system` (and all `$t('design-system.*')`) stays stable — it's no longer picked by the
  `@/features/*/locales/*.json` glob.
- `nav.ts` deleted; the single nav link inlined into `AppSidebar.vue` `navBottom` (like `/settings`),
  + `IconPalette` import. Dropped the `designSystemNav` import.
- Deleted the now-empty `web/src/features/design-system/`.

## Result

- New layout: `views/design-system/*.vue` (26), `router/design-system.ts`, `locales/design-system/`.
- No leftover refs to `features/design-system` / `designSystemNav`; `vue-tsc` clean. URLs (`/design-system/*`)
  and the i18n namespace unchanged — pure relocation.

### Follow-up (2026-06-04) — views grouped by purpose

User: index page stays at the root of `views/design-system/`, the rest into subfolders by purpose. Used the
index catalog's own 7 groups as the folder names: `basics/` (tokens/typography/layout), `controls/` (buttons/
button-group/selects/inputs/numbers/toggle/sliders/date-pickers), `data/` (tables/pagination/world-map),
`charts/` (line/bar/pie), `feedback/` (loaders/skeleton/status-badge/dialogs/tooltips), `content/` (code-block/
markdown), `structure/` (dividers). `DesignSystemIndexView.vue` kept at root. `git mv`'d the 25 views; views
use only `@/...` imports so nothing inside changed; updated the 25 lazy imports in `router/design-system.ts`
(`@/views/design-system/<group>/X.vue`), index import untouched. All 26 routed imports resolve; `vue-tsc` clean.

### Follow-up (2026-06-04) — admin-only

User: «раздел дизайн-системы для админов». FE-only gate (no backend routes — pure showcase). Added
`action: 'manage'/subject: 'admin'` to all 26 routes (single `replace_all` on the uniform
`meta: { scroll: 'y' }`) and to the inlined nav entry in `AppSidebar`. Router guard `canNavigate` → non-admin
to `/403`; sidebar `visibleNavBottom` hides the link via `can('manage','admin')` (same pair as
`administration`/`core_monitoring`). `vue-tsc` clean.
