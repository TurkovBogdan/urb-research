---
title: Settings — group bool-toggle description under its switch
date: 2026-07-09
status: completed
description: "On /settings/modules each connector enable-toggle's description floated ~28px below the tall switch, reading as disconnected. Tuck it under the toggle title so each connector groups as [toggle+desc] then [key+desc]."
tags: [frontend, settings, core_connectors]
---

## Task

`http://127.0.0.1:12200/settings/modules` — проверить отображение в браузере и исправить косяки.

## Context

Browser QA of the module-settings page. Каждый коннектор (`core_connectors`) выводится плоским списком полей: bool-тумблер «Включить X» + его секретный `*_api_key`. Тумблер (VSwitch, `min-height: 40px`) выше своего однострочного заголовка, а описание bool-поля рисовалось общей подписью `SettingField.__desc` **под всей плашкой** → между заголовком «Включить Tavily» и его описанием зиял ~28px, описание читалось как висящее между тумблером и ключом (непонятно, к чему относится). Проверено в браузере: `desc.top − title.bottom = 28px`.

## What was done

- `web/src/components/settings/SettingFieldBool.vue` — описание bool-поля рендерится **внутри** `SwitchPanel` (default-слот → `switch-panel__desc`, рядом с заголовком) через `MarkdownRenderer` (ссылки в описаниях сохраняются); добавлены scoped-стили сброса `.md-body` (12px / line-height 1.4 / muted / `p { margin: 0 }`).
- `web/src/components/settings/SettingField.vue` — общая подпись снизу подавляется для bool: `descriptionBelow = Boolean(field.description) && field.kind !== 'bool'`, `v-if` на `.setting-field__desc` заменён на неё.
- `web/dist` пересобран (`corepack pnpm build`, vue-tsc 0 ошибок).

Проверено вживую (chrome-devtools, :12200 после rebuild): описание тумблера теперь в 2px под заголовком, обе строки укладываются в высоту свитча; общая подпись `.setting-field__desc` для bool отсутствует; не-bool поля (secret/choice/int в карточке «Веб-поиск») сохранили описание снизу без изменений.

## Result

Каждый коннектор читается как единый блок: [тумблер + описание тумблера] → [поле ключа + описание ключа]. Изменённые файлы:
- `web/src/components/settings/SettingFieldBool.vue`
- `web/src/components/settings/SettingField.vue`
- `web/dist/**` (rebuild)
