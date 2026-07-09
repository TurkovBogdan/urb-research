# Актуализация конфига подключения на /mcp-servers под stdio-обёртку

**Date:** 2026-07-08
**Status:** completed

## Goal

Страница `/mcp-servers` отдавала remote-HTTP конфиги (`npx mcp-remote` + токен-плейсхолдер /
нативный Streamable HTTP). После появления лёгкого демон-враппера (`app.py --mcp-stdio`,
см. README «Подключение MCP») вывод устарел — актуализировать под stdio-шим.

## What was done

**Бэкенд** (`src/modules/core_mcp/api.py`):
- Убраны генераторы remote-конфигов (`_claude_config`/`_claude_code_config`/`_connection_configs`/
  `_remote_url`/`_server_key`/`_TOKEN_PLACEHOLDER`, импорт `MCP_PREFIX`).
- Добавлен `_stdio_config(code, pin_code)` — конфиг stdio-обёртки в форме README:
  `command` = абсолютный `uv` (`shutil.which("uv")`, fallback `"uv"`), `args` =
  `run --directory <PROJECT_ROOT> python src/app.py --mcp-stdio`, ключ записи = код сервера.
  `env.MCP_STDIO_CODE` пинуется **только** когда смонтировано >1 сервера (иначе обёртка сама
  берёт единственный). `_PROJECT_ROOT` = `parents[3]` от api.py.
- DTO `McpServerDetail`: `connection_configs: dict[str,str]` → единый `connection_config: str`.

**Фронт:**
- `features/core_mcp/api.ts` — тип `McpClient` удалён, `connection_configs` → `connection_config: string`.
- `views/McpServersView.vue` — убран переключатель клиентов (VBtnToggle + `client` ref + стиль
  `mcp-servers__format`): stdio-конфиг одинаков для Claude Desktop и Claude Code. Панель получает
  единый `connection_config`.
- `locales/ru.json` — удалён блок `format`.

**Сборка:** `web/dist` пересобран.

## Problems

- Живой :12200 (бекенд от MCP-шима, без hot-reload) отдаёт старый Python до рестарта —
  проверку делал на временном бекенде :12299 (погашен). Совместимость: старый Python отдаёт
  `connection_configs`, новый фронт читает `connection_config` — на живом :12200 конфиг покажется
  пустым до рестарта бекенда.

## Result

- Проверено вживую (порт 12299, изолир. контекст): секция «Подключение» рендерит stdio-конфиг
  (`uv run --directory … --mcp-stdio`, кнопка «Копировать»), переключатель клиентов убран,
  список 23 инструментов на месте.
- `vue-tsc` 0 ошибок; `--core` 285 passed; у core_mcp своих тестов нет, ссылок на старый конфиг
  в тестах не было.
- Решение: remote-HTTP вариант и переключатель клиентов **удалены** (приложение локальное,
  токен-генерации нет — конфиг был плейсхолдерный). Если нужен remote-вариант для prod за nginx —
  вернуть отдельно.
- Живой :12200 подхватит после рестарта бекенда.
