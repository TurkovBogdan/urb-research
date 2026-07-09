# Ссылки на сервисы + рендер ссылок в описаниях настроек

**Date:** 2026-07-08
**Status:** completed

## Goal

На странице `/settings/modules` у коннекторов (`core_connectors`):
1. В описание каждого `*_api_key`-поля добавить ссылку на страницу выпуска токена сервиса.
2. Разрешить ссылки в описаниях полей настроек и корректно их отрендерить (markdown).

## What was done

**Бэкенд** (`src/modules/core_connectors/settings.py`): в описания ключей добавлены
markdown-ссылки на страницы выпуска токенов — Tavily (`app.tavily.com/home`), Firecrawl
(`firecrawl.dev/app/api-keys`), xAI (`console.x.ai`), xAI Management (`console.x.ai` →
Settings → Management Keys), OpenRouter (`openrouter.ai/settings/keys`), OpenAI Admin
(`platform.openai.com/...admin-keys`), Anthropic Admin (`console.anthropic.com/...admin-keys`).
web_scrapper — локальный демон, ссылки нет.

**Фронт — рендер ссылок в описаниях (централизован):**
- `web/src/components/settings/SettingField.vue` — описание поля теперь рендерится в **одном
  месте** через `MarkdownRenderer` (compact, muted-caption) под редактором, для любого типа поля.
- Из всех редакторов убран собственный вывод описания: у Vuetify-инпутов сняты
  `:hint`/`persistent-hint` + добавлен `hide-details="auto"` (пустая область деталей
  схлопывается, ошибки остаются); `SettingFieldBool` больше не передаёт `:description` в
  `SwitchPanel`; `SettingFieldList` убрал собственный `__hint`.
- `SettingsView.vue` — описание модуля тоже через `MarkdownRenderer`.
- `web/src/components/MarkdownRenderer.vue` — добавлен `link`-рендерер: **внешние** ссылки
  (href не с `/`) получают `target="_blank" rel="noopener noreferrer"` (внутренние остаются
  in-app через роутер) — чтобы клик по токен-ссылке не уводил из SPA и не терял несохранённое.

**Сборка:** `web/dist` пересобран (коммитится).

## Problems

- Бекенд `/settings/modules` (`--backend` без hot-reload, запущен MCP-шимом) отдаёт старые
  описания из `settings.py` до рестарта процесса — проверку рендера делал на **временном**
  бекенде на порту 12299 (не трогая живой :12200), после — погашен.

## Result

- Рендер проверен вживую (изолированный browser-контекст, порт 12299): ссылки кликабельны,
  `href`/`target="_blank"`/`rel` корректны у всех коннекторов.
- `vue-tsc --noEmit` — 0 ошибок; `--module=core_connectors` 15 passed; `--core` 285 passed.
- Чтобы ссылки появились на живом :12200 — пользователю **перезапустить бекенд** (подхватит
  новый `settings.py`; новый `web/dist` он уже раздаёт с диска).
