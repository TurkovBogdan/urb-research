---
title: Sidebar — separate «Мониторинг» section above «Настройки»
date: 2026-07-04
status: completed
description: "Add a «Мониторинг» sidebar section above «Настройки» and move the tasks-monitoring link into it (renamed «Мониторинг задач» → «Задачи» to avoid redundancy under the new section)."
tags: [frontend, core_monitoring, layout]
---

## Task

На фронте добавить раздел «Мониторинг» выше «Настройки», перенести в него мониторинг задач.

## What was done

- `web/src/layout/components/AppSidebar.vue` — в `nav`: новая секция
  `{ kind: 'section', label: 'Мониторинг' }` перед секцией «Настройки»; пункт
  `/tasks` перенесён из-под «Настройки» в неё, ярлык fallback `Мониторинг задач`
  → `Задачи`.
- `web/src/features/core_monitoring/locales/ru.json` — `nav`: «Мониторинг задач» →
  «Задачи» (ключ `core_monitoring.nav` используется только этим пунктом; секция уже
  даёт слово «Мониторинг», иначе читалось бы «Мониторинг → Мониторинг задач»).

Секция захардкожена строкой как соседние «Данные»/«Настройки» (не labelKey).

## Result

Порядок в сайдбаре: Данные → Мониторинг (Задачи) → Настройки (Настройки/Сервер) →
Разработка. vue-tsc clean; `web/dist` пересобран. Изменены `AppSidebar.vue` +
`core_monitoring/locales/ru.json`.
