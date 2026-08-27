---
title: /settings/interface — groups, descriptions, switch panel
date: 2026-08-27
status: completed
description: "Rebuild the client-settings page in the anatomy of /settings/modules: two groups with descriptions, a description line under each field, and SwitchPanel instead of a bare VSwitch."
tags: [frontend, settings]
---

## Task

«Тут нужно применить компонент switch-panel и логику настроек из /settings/modules (группы настроек
с описанием). У нас есть интерфейс, оформление документа».

## Context

`/settings/interface` was one undivided card of seven controls, each carrying its text as a Vuetify
`persistent-hint`. `/settings/modules` shows the same kind of thing differently: a card per group
with a caption and a description, the field with `hide-details="auto"`, and its description as a
separate muted line under it (`SettingField.vue`), with bool fields drawn as `SwitchPanel`
(`SettingFieldBool.vue`). Two pages, two dialects for one concept.

## What was done

- **`components/settings/SettingsGroup.vue`** (new) — the card shell: title, description, divider,
  slot with a 24px field rhythm. Description is a plain string, not markdown: client-side settings
  own their text, unlike schema fields whose description comes from the backend and may carry links.
- **`InterfaceView.vue`** — split into two groups laid out on the same grid as the module cards
  (`repeat(auto-fill, minmax(320px, 440px))`, `align-items: start`):
  - **Интерфейс** — тема, шрифт интерфейса, раскладка реестра, оглавление документа в навигации.
  - **Оформление документа** — шрифт текста, размер, ширина параграфов.
  The split is by what the setting acts on, not by control type: everything in the second group is a
  typography knob of the reading zone, so `documentNav` — a navigation element — stays in the first.
- Hints replaced by the modules idiom: `variant="outlined" density="comfortable" hide-details="auto"`
  plus a `.setting__desc` line under the field; `documentNav` became a `SwitchPanel` with title and
  description, the same component the schema-driven bool field uses.
- The preview card moved out of the grid to full width — it is not a setting but what the settings
  apply to, and a 440px column is already narrower than the measure being previewed.
- Locale: new `settings.interface.group.{app,document}.{title,description}`.

The two cards are written as markup rather than looped over a descriptor list: the field set is known
here and heterogeneous, and a schema exists on `/settings/modules` only because those fields arrive
from the backend.

## Result

Added: `web/src/components/settings/SettingsGroup.vue`.
Changed: `web/src/features/settings/views/InterfaceView.vue`,
`web/src/features/settings/locales/ru.json`, `web/dist/` (rebuilt).

`vue-tsc` 0, build ok, live check on :22040 in the isolated browser — both groups render, the switch
toggles and persists (`app.nav.document` removed at the default, `"0"` when off), console clean.
No frontend test framework in the project, so the behaviour is pinned by the live run.
