---
title: Settings — one Save button (no per-field auto-save)
date: 2026-07-02
status: completed
description: "Replace per-field auto-save on the settings page with a single «Сохранить» button; secret fields stop resetting mid-typing."
tags: [frontend, settings, secret, ux]
---

## Task

Настройки должны сохраняться по клику на **одну** кнопку «Сохранить», а не автосейвом по
вводу. Автосейв к тому же резко «сбрасывал» секретное поле (бэк отдаёт замаскированное
пустое), и было непонятно, что произошло.

## What was done

- `web/src/features/settings/views/SettingsView.vue` переписан: убран debounce-автосейв
  (`onChange`→save). Теперь `values` — редактируемая копия, `saved` — снимок с сервера;
  `dirty` по разнице (JSON-сравнение). **Одна** кнопка «Сохранить» внизу (`saveAll`) пишет все
  изменённые поля (per-key PUT), затем перечитывает состояние. Ошибки — по полю
  (`fieldErrors`) + общий алерт. Кнопка `disabled`, пока нет изменений.
- `web/src/components/settings/SettingFieldSecret.vue` упрощён до обычного password-инпута
  (placeholder по `is_set`, эмитит по вводу) — без собственной кнопки; сохраняется общей.
  `SettingField.vue` по-прежнему роутит `str+secret` сюда.
- i18n `settings.action.save`, `settings.error.save_failed`; описание страницы →
  «Применяются по кнопке «Сохранить»».

**Логика секрета (сентинел `NOT_CHANGED`):**
- Бэкенд `_settings/api.py`: заданный секрет наружу отдаётся сентинелом `NOT_CHANGED`
  (не токен; пустой = не задан). PUT `""`/`NOT_CHANGED` = «не менять».
- Фронт `SettingFieldSecret.vue`: сентинел показывается пустым полем (плейсхолдер «задан»),
  но остаётся в модели → если не трогать, уходит обратно сентинелом = keep.
- `saveAll` НЕ перечитывает страницу после сохранения → введённое значение **остаётся в поле**;
  свежий сентинел приходит только при следующем открытии страницы (GET).
- Тесты сохранения (`tests/core/_settings/test_api.py`, проверяют **реальное** значение в
  store через `get_registry().get(...).token`, а не только `is_set`):
  `test_secret_set_stores_value_but_returns_sentinel` (store=токен, наружу=`NOT_CHANGED`),
  `test_secret_update_replaces_value` (новое значение перезаписывает),
  **`test_sentinel_put_does_not_overwrite_token`** (пришло `NOT_CHANGED` → токен прежний, не
  затёрт литералом/пустым), `test_blank_put_does_not_overwrite_token`, `test_reset_clears_secret`.

## Result

Все настройки применяются одной кнопкой «Сохранить». Секрет: ввёл → сохранил → значение в поле;
открыл заново → с бэка `NOT_CHANGED` (пустое поле, «задан»). `--core --module=web_content`
301 passed; `vue-tsc` чист, `web/dist` пересобран. Файлы: `src/core/_settings/api.py`,
`SettingsView.vue`, `SettingFieldSecret.vue`, `SettingField.vue`, `settings/locales/ru.json`,
`tests/core/_settings/test_api.py`.
