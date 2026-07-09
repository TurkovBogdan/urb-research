---
title: Frontend fixes + profile «Язык и регион» section
date: 2026-06-06
status: completed
description: "Locale/timezone/date-format prefs (localStorage) moved into a new profile «Язык и регион» card with a live date/time hero; plus a batch of sidebar/profile polish — avatar→person icon (rounded-square), collapse-toggle hover/width/centering, persisted collapse state, adaptive two-column profile grid."
tags: [frontend, i18n, dates, profile, sidebar]
---

## Task

In the template there is a clock showing the user's timezone and a language switcher. Add a timezone picker AND a date-format picker, stored locally (localStorage), alongside the language choice. Wire the timezone into the handler of all dates.

## Context

- Clock lives inline in `web/src/layout/components/AppSidebar.vue` — uses Luxon `DateTime.now()` (browser zone), format `'ZZZZ HH:mm'`, ticks every 10s.
- Language: single entry point `setLocale()` in `web/src/plugins/i18n.ts`, persisted to localStorage key `app.locale`. Two switchers (sidebar + Settings).
- Dates: single chokepoint `web/src/shared/utils/date.ts` (Luxon). `_parse` does `DateTime.fromSQL(s,{zone:'utc'}).toLocal()`; date part is locale-derived (`_datePart`: ru `dd.MM.yyyy` / en `dd/MM/yyyy`). 30+ views call `fmtDate*`/`fmtTime*`/`fmtRelative*` — reactivity comes from reading `i18n.global.locale.value` during render.
- `fmtDateUtc` intentionally stays UTC (day-aligned report bounds) — must NOT take the timezone.
- No user-timezone anywhere today (not in `UserView`, not in profile). Backend storage explicitly out of scope (localStorage only).

## Plan (pending go-ahead)

- New reactive prefs module (e.g. `web/src/plugins/preferences.ts` or extend i18n): `currentZone` + `currentDateFormat` refs, `setTimezone()` / `setDateFormat()` setters persisting to `app.timezone` / `app.dateFormat`. Default = auto (browser zone / locale-derived format).
- `date.ts`: `_parse` → `.setZone(currentZone.value)` instead of `.toLocal()`; `_datePart` reads `currentDateFormat`. Reactivity preserved (refs read during render). `fmtDateUtc` untouched.
- Clock in `AppSidebar`: `DateTime.now().setZone(currentZone.value)`.
- Pickers next to the language toggle (sidebar + Settings). Timezone source TBD (core_geo `GET /timezones` vs `Intl.supportedValuesOf('timeZone')`).

Confirmed with user: both pickers default to **«Авто»** (tz = browser zone, format = locale-derived); date-format options = Авто + `DD.MM.YYYY` / `DD/MM/YYYY` / `YYYY-MM-DD` / `MM/DD/YYYY`; tz list = full IANA from `Intl.supportedValuesOf('timeZone')` (DST-correct; fixed `UTC±X` rejected — frozen, no summer/winter), shown as `HH:mm · Zone` (no offset/UTC text); 24h time kept (no 12/24h toggle).

**Iteration (2026-06-06): pickers MOVED out of the sidebar into the user-profile page.** A new «Язык и регион» card sits in the column right of the profile card (two-column `.profile-grid`).

**Iteration 2 (2026-06-06): sidebar footer stripped entirely** — both the RU/EN language toggle AND the clock removed from the nav (only `ProfileNavCard` remains at the bottom). Sidebar no longer imports luxon / preferences / `setLocale`. In their place the profile region card grew a **live current-date/time hero** (`.region-clock`): weekday + big ticking `HH:mm:ss` + `date · ZZZZ`, all rendered through the user's prefs (chosen timezone, date format, locale), ticking every 1s. Language/timezone/date-format dropdowns stay in the region card.

## What was done

- New `web/src/plugins/preferences.ts`: reactive `currentZone` / `currentDateFormat` refs (seed from localStorage `app.timezone` / `app.dateFormat`, default `AUTO`) + `setTimezone` / `setDateFormat` (persist; `AUTO` removes the key) + `DATE_FORMATS` (Luxon tokens) + `timezoneOptions()` (`Intl.supportedValuesOf`, empty-safe).
- `web/src/shared/utils/date.ts`: `_datePart` reads `currentDateFormat` (falls back to locale separator on `AUTO`); new `_zoned()` applies `currentZone` via `.setZone()` (or `.toLocal()` on `AUTO` / invalid zone), used by `_parse`. `fmtDateUtc` left UTC (day-aligned bounds), unchanged. Reactivity preserved (refs read during render).
- `web/src/features/user-profile/views/ProfileView.vue`: new «Язык и регион» `.region-card` (globe icon + title/desc), placed beside the profile card in a wrap-capable two-column `.profile-grid`. Layout inside (final): **language → live date/time example → timezone → date format**. Owns the `languageItems`/`timezoneItems`/`dateFormatItems` builders (moved here from the sidebar). Timezone uses the design-system **`VSelectSearch`** (`@/components/VSelectSearch.vue`, drop-in VSelect with an in-menu search row) instead of `VAutocomplete`; language + date format are plain `VSelect`. New locale keys `user-profile.region.{title,description}` + `common.prefs.{search,not_found}` (ru/en).
- `web/src/layout/components/AppSidebar.vue`: footer cleared — removed the RU/EN `VBtnToggle`, the clock (`now`/`clock`/10s timer), `.locale-switcher`/`.sidebar-clock` styles, and the now-unused luxon/preferences/`setLocale`/`locale` imports + `onMounted`/`onUnmounted`. Only `ProfileNavCard` remains pinned at the bottom.
- `ProfileView.vue` live hero: `now` ref ticking every 1s (`onMounted`/`onUnmounted`) → `nowZoned` (applies `currentZone`) → `liveTime` (`HH:mm:ss`), `liveDate` (chosen format / locale-derived), `liveZone` (`ZZZZ`). Rendered in a centered `.region-clock` accent-soft panel; final card order **language → example → timezone → date format** (weekday dropped from the example per user). Time font dialed down to `1.75rem`.
- Adaptive layout (2026-06-06): wrapped the two cards in `.profile-page` (max-width 1080, flex column — **future full-width blocks like access-tokens stack below the card row**) + `.profile-grid` = CSS `grid-template-columns: repeat(auto-fit, minmax(320px, 1fr))`. Two equal columns when ≥~664px content width, one column below; dropped the old flex-basis/max-width per card.
- **Browser-verified** (Chrome, `localhost:12100/profile`): grid measured `528+528` (2-col) at 1080, collapses to single column at 640/460 (JS-probed); stacked cleanly at ~820px window; no console errors; live clock ticks; `VSelectSearch` opens with pinned search row, filters `lond` → `Europe/London`, and selecting it recomputed the hero to `21:42 · 05.06.2026 · GMT+1` (DST + day-rollover correct).
- Timezone options shown as **`HH:mm · Zone`** (live current time in that zone + IANA name for search), **sorted by offset**. Built off a shared ticking `now` ref (hoisted above the pickers, reused by the clock; +10s tick) so each option's time stays current; invalid zones filtered out. **Kept the full IANA list (not fixed `UTC±X` offsets)** — fixed offsets are frozen and drop DST (summer/winter time would be off by an hour half the year); real IANA zones carry the DST rules. Offset (`±hh:mm`) and the literal `UTC` were dropped from the label per user request — only the in-zone time + name remain.
- Locales: `common.prefs.{auto,language,timezone,date_format,search,not_found}` in `web/src/locales/{ru,en}.json`.

### Sidebar + profile polish (batch, 2026-06-06, all browser-verified)

- **Avatar → person icon**, rounded-square (like the «Язык и регион» globe), in BOTH places: `ProfileView.profile-card__avatar` (52px, `border-radius: var(--radius)`) and `ProfileNavCard.profile-nav__avatar` (30px, `var(--radius-sm)`); dropped the letter-`initial` computeds. Collapsed avatar button additionally reset (`appearance:none; padding:0; font:inherit`) so the glyph centers like the `<span>` version.
- **Collapse toggle** (`main.scss .collapse-btn`): square footprint (34×34 expanded, 33×36 collapsed) + `radius-sm` + nav-style `surface-hi` hover (own overlay hidden) in BOTH states — was a narrow icon button.
- **Collapsed-rail centering**: the scrolling nav list reserved a 10px scrollbar gutter, pushing icons + toggle ~5px left of the rail centre. Added `app-sidebar--collapsed` on the drawer → `scrollbar-width:none` (+ `::-webkit-scrollbar{width:0}`) for its content in collapsed mode → icons + toggle now centre at x=28 (true rail centre); toggle reverted to `justify-content:center`.
- **Persisted collapse state**: `layout/store.ts` seeds `collapsed` from `localStorage['app.sidebar_collapsed']` and `watch`-persists it (`'1'` = collapsed, key absent = expanded) — same `app.*` localStorage namespace as the display prefs.
- **Time hero font** dialed to `1.75rem`; bio textarea `rows="5"`.

## Result

- New: `web/src/plugins/preferences.ts`.
- Changed: `web/src/shared/utils/date.ts`, `web/src/layout/components/AppSidebar.vue`, `web/src/layout/store.ts`, `web/src/styles/main.scss`, `web/src/features/user-profile/views/ProfileView.vue`, `web/src/features/user-profile/components/ProfileNavCard.vue`, `web/src/features/user-profile/locales/{ru,en}.json`, `web/src/locales/{ru,en}.json`.
- FE-only (no backend, no tests); `vue-tsc --noEmit` clean; verified live in Chrome. Open (deferred, user's call): label style in the tz/format selects (mock showed `GMT+5 · cities` / `ДД.ММ.ГГГГ · example`, current is `time · zone` / format example); mirroring the prefs into Settings.
