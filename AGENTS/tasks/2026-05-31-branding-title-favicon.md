---
title: Branding — app title, favicon, default language
date: 2026-05-31
status: completed
description: "Rename remaining 'Uroboros Second Brain' strings to Semaphore.Core; add a favicon set from assets/app.ico; large language switcher on the home page; default locale → English."
tags: [frontend, branding, build]
---

## Task

Follow-ups after the home landing page: replace the old "Uroboros Second Brain"
title strings with "Semaphore.Core", add a large language switcher under the
welcome hero, make English the default language, and use `assets/app.ico` as the
website favicon (converting if needed).

## What was done

- Title rename "Uroboros Second Brain" → "Semaphore.Core" in the 4 places that
  still carried the old name: `web/index.html` `<title>`, `src/core/app_factory.py`
  FastAPI `title`, `src/apps/app/gui.py` `setApplicationName`, `app_build.py`
  `.desktop` `Name=`. (`src/gui/gui_window.py` `_WINDOW_TITLE` was already correct.)
- Home page language switcher: large `VBtnToggle` (`mandatory` / `outlined` /
  `divided`, `size="large"` per `VBtn`) under the hero lead in `views/HomeView.vue`,
  bound to the shared `setLocale`. Verified live-switching in the browser.
- Fixed an i18n key-path bug: global `web/src/locales/*.json` is mounted under the
  `common` namespace, so HomeView keys are `common.home.*` (not `home.*`) — page
  had been rendering raw keys.
- Default locale → English: `web/src/plugins/i18n.ts` `initialLocale` fallback and
  `fallbackLocale` both `ru` → `en` (only affects clients with no stored choice).
- Favicon: generated `web/public/{favicon.ico, favicon-32.png, apple-touch-icon.png}`
  from `assets/app.ico` (extract 256px PNG via `icotool`, downscale via ImageMagick
  `convert`; ico slimmed to 16/32/48 entries → 15 KB vs the source 370 KB). Linked
  in `web/index.html`. Verified the icon serves at `/favicon.ico` and renders.

## Result

UI, browser tab, Qt app, Swagger and the built `.desktop` entry all read
"Semaphore.Core"; the home page favicon is the teal semaphore icon; English is the
out-of-the-box language. Changed: the files listed above + new `web/public/` assets.
