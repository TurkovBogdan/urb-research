---
title: Rename web_content menu section to "Веб-документы"
date: 2026-07-02
status: completed
description: "Rename the web_content sidebar section label from 'Web Content' to 'Веб-документы'."
tags: [frontend, web_content, i18n, nav]
---

## Task

Переименовать раздел меню (web_content) в «Веб-документы».

## What was done

- `web/src/features/web_content/locales/ru.json`: `nav` `"Web Content"` → `"Веб-документы"` (источник названия раздела через `labelKey: 'web_content.nav'`).
- `web/src/layout/components/AppSidebar.vue`: hardcoded fallback `label` тоже → `'Веб-документы'` для консистентности.

Дочерние пункты («Запросы»/«Страницы») не менялись.

## Result

Раздел sidebar называется «Веб-документы». Изменены 2 файла (i18n + fallback-лейбл), логики не тронуто.
