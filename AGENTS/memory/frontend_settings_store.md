---
name: frontend_settings_store
description: Centralized local user-settings Pinia store on the frontend (web/src/stores/settings.ts)
metadata: 
  node_type: memory
  type: project
  originSessionId: e5e49e6f-b028-40c6-92bc-14b8a44da493
---

All client-side user settings live in one Pinia store `web/src/stores/settings.ts` (`useSettingsStore`), grouped: `locale` (`language` — façade over i18n `setLocale`/`i18n.global`, `timezone`, `dateFormat`), `ui` (`sidebarCollapsed`), `message` (`mode` `'html'|'text'`, `safe` bool — true = security filter on / remote content blocked). State holds NORMAL typed values; a `persisted(key, def, codec)` helper syncs each to localStorage (bool↔'1'/'0'), and a value equal to its default removes the key. `reactive` wrappers per group auto-unwrap the refs so `settings.message.safe` reads a real boolean.

Replaced the old scattered prefs: `plugins/preferences.ts` (deleted), the persisted `collapsed` in `layout/store.ts` (now only ephemeral `showTopBar`/`showBottomBar`/`mobileOpen`), and direct `setLocale` calls. `shared/utils/date.ts` reads `useSettingsStore().locale.*` inside formatters. localStorage keys: `app.locale` (i18n-owned), `app.timezone`, `app.date_format`, `app.sidebar_collapsed`, `app.message.mode`, `app.message.safe`.

The `message` group (`mode`/`safe`) drove email-body rendering in the now-removed `mail_sync`/`content_processors` modules; the shared `web/src/components/MessageContent.vue` + `SafeEmailBody.vue` and the `/design-system/message` demo remain.
