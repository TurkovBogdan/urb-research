---
title: Add "Настройки" link to the sidebar Settings section
date: 2026-07-02
status: completed
description: "Add a sidebar link to the runtime settings page (/settings) in the «Настройки» section, labeled «Настройки»."
tags: [frontend, nav, settings]
---

## Task

В раздел «Настройки» сайдбара добавить ссылку на страницу настроек (`/settings`), подпись «Настройки».

## What was done

- `web/src/layout/components/AppSidebar.vue`: в секцию `{ kind: 'section', label: 'Настройки' }` добавлен пункт `{ path: '/settings', label: 'Настройки', icon: IconAdjustments }` (над `/setup` «Сервер»); импортирован `IconAdjustments`.

Маршрут `/settings` (`features/settings/SettingsView.vue`) уже был зарегистрирован в роутере.

## Result

Пункт «Настройки» ведёт на страницу runtime-настроек. `vue-tsc` чист. Для применения — ребилд `web/dist`.
