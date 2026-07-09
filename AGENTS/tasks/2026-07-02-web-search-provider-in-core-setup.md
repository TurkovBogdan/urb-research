---
title: Split settings — web_content tokens + provider → runtime settings (secret fields)
date: 2026-07-02
status: completed
description: "Move web_content provider tokens (and keep provider) into runtime DB settings with a new secret-field capability; core_setup stays server/infra-only."
tags: [core_setup, web_content, settings, secret]
---

## Task

Изначально: добавить выбор поискового провайдера в `core_setup`. По ходу обсуждения
пользователь развернул решение: **перенести токены провайдеров в runtime-настройки (БД)** и
закрепить в приложении разделение «серверная часть (ENV/core_setup) vs остальное (runtime/БД)».

## Context

Было: провайдер — горячая runtime-настройка (`ChoiceField provider`), а токены
(`TAVILY_API_KEY`/`FIRECRAWL_API_KEY`) — ENV (`WebContentConfig`), правились в `core_setup`
(группа «Веб-источники»). Два разных места для настроек одного модуля.

Решение: провайдер + токены живут вместе в runtime-настройках web_content; core_setup остаётся
только для инфраструктуры (DB/server/worker — то, что нужно, чтобы поднять процесс и дойти до БД;
коннект к БД физически не может жить в БД). Для токенов понадобилась новая возможность —
**секретное поле настроек** (маскирование на чтение), которого в системе не было.

## What was done

**Секретное поле (общая инфраструктура settings):**
- `_settings/fields.py`: `StrField.secret: bool` + `Field.is_secret()`; `repr_for_log` маскирует секрет; `secret` в `ui_descriptor`.
- `_settings/api.py`: `_store_values` маскирует секреты (GET → `""`), `_module_payload` добавляет `is_set` в дескриптор; `put_value` — пустой PUT секрета = «не менять» (очистка через reset).
- Фронт: `features/settings/api.ts` (`secret`/`is_set` в `StrFieldDescriptor`); `components/settings/SettingFieldString.vue` — password-инпут + подсказка «токен задан».

**web_content: токены → runtime-настройки:**
- `module_settings.py`: в `SCHEMA` добавлены secret `StrField` `tavily_api_key`/`firecrawl_api_key` (рядом с `ChoiceField provider`); хелпер `provider_api_key(key)` (fallback `""`, если store не загружен).
- `providers/tavily.py`+`firecrawl.py`: токен из `provider_api_key(...)` вместо `WebContentConfig()`.
- Удалён `config.py` (`WebContentConfig`); `module.py` — убран `config_cls`.
- `core_setup/keys.py`: удалена группа «Веб-источники» (TAVILY/FIRECRAWL). `.env`/`.env.example.{dev,prod}` — токены убраны, оставлен комментарий-указатель на `/core/settings`.

**Тесты:**
- `tests/core/_settings/test_api.py`: +3 (маскирование секрета, `is_set`, пустой PUT не затирает) + модуль `_SecretM`.
- `tests/modules/web_content/test_module_settings.py` (новый, взамен удалённого `test_config.py`): схема с secret-токенами, нет `config_cls`, fallback `provider_api_key`.

**Доки/память:** `web_content/INDEX.md` (раздел ENV → «Настройки (runtime, БД)»), `core_setup/INDEX.md` (граница серверное/прикладное), `MEMORY.md` (строки web_content/core_setup + новый факт про secret-поле).

## Problems

`searcher.active_provider_code()` НЕ менялся — провайдер и так был runtime-настройкой; развернули только токены (ENV → settings), а не провайдер (ENV-вариант из первой итерации отменён).

## Result

Провайдер и токены web_content — в одном месте (`/core/settings`, секреты маскируются, горячо).
core_setup — только сервер/инфра. Тесты: `--core --module=web_content` 300 passed; `vue-tsc` чист.

**Данные:** реальные dev-токены больше не в `.env` — их надо один раз ввести на `/core/settings`
(значения Tavily/Firecrawl взять из менеджера секретов, в записи не хранятся). Для применения
фронта нужен ребилд `web/dist`.

Файлы: `src/core/_settings/{fields,api}.py`, `web/src/features/settings/api.ts`,
`web/src/components/settings/SettingFieldString.vue`, `src/modules/web_content/{module,module_settings}.py`,
`src/modules/web_content/providers/{tavily,firecrawl}.py`, `src/modules/core_setup/keys.py`,
`.env`, `.env.example.dev`, `.env.example.prod`, `tests/core/_settings/test_api.py`,
`tests/modules/web_content/test_module_settings.py` (+ удалены `web_content/config.py`,
`tests/modules/web_content/test_config.py`), доки/память.
