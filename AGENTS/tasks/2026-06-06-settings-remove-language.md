---
title: Remove language picker from Settings + hide Settings from nav
date: 2026-06-06
status: completed
description: "Drop the language-switch card from /settings and remove the Settings entry from the sidebar navigation."
tags: [frontend, settings, navigation]
---

## Task

«Давай уберём из раздела выбор языка и скроем этот раздел вообще из навигации» (re `/settings`).

## Context

The Settings page (`/settings`) carried a standalone language-switch card at the top.
Language/region prefs now live on the profile «Язык и регион» card (see
`2026-06-06-frontend-datetime-prefs`), so the Settings copy is redundant. The user also
wants the whole Settings section hidden from the sidebar (route kept, just unlinked).

## What was done

- `web/src/features/settings/views/SettingsView.vue`: removed the language `VCard`
  (title/description + `VBtnToggle` of `LOCALES`) and its now-dead code — `LOCALES`
  const, `setLocale`/`AppLocale` import, and `locale` from `useI18n()`.
- `web/src/layout/components/AppSidebar.vue`: emptied `navBottom` (was the single
  `/settings` link), removed the unused `IconSettings` import, and wrapped the `#append`
  bottom `VList` (+ its divider) in `v-if="visibleNavBottom.length"` so no dangling
  divider renders. `ProfileNavCard` stays pinned at the bottom.

Route `/settings` itself is untouched — page still reachable by URL, just absent from nav.

No tests (FE template/wiring only). `vue-tsc --noEmit` clean.

## Result

Changed: `web/src/features/settings/views/SettingsView.vue`,
`web/src/layout/components/AppSidebar.vue`.
