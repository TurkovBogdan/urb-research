---
title: Launcher wake-daemon (lazy backend on first MCP request)
date: 2026-07-08
status: completed  # in-work | completed | deferred
description: "Add a lightweight always-on launcher daemon that holds the public port, boots the full backend on the first incoming request, opens the system browser to the SPA home page, and reverse-proxies traffic. Nothing heavy runs by default; shutdown is manual (no idle stop)."
tags: [launcher, mcp, app-entry, platform]
---

## Task

User: сервер должен быть по умолчанию отключён; при поступлении запроса от MCP система поднимает
сервер и открывает в браузере главную страницу. Добавить отдельный демон.

Clarified decisions:
- Модель: ничего активного по умолчанию — лёгкий лаунчер держит порт, первый запрос поднимает всё (proxy-модель).
- Авто-остановка по простою: НЕТ, гасить вручную.
- Браузер: системный браузер по умолчанию на главную (`http://<host>:<port>/`).

## Context

MCP-серверы смонтированы ВНУТРИ backend'а (`src/core/router/mcp.py::mount_mcp_servers`,
`app.mount("/mcp/<code>")`), т.е. MCP-запросы принимает сам HTTP-сервер. «Курица-яйцо»:
если сервер выключен — MCP-запрос принять некому. Нужен лёгкий always-on слушатель на публичном
порту (`SERVER_PORT`), который на первый запрос поднимает backend на внутреннем порту, открывает
браузер и реверс-проксирует весь трафик (MCP + internal API + SPA).

Entry point `src/app.py` уже несёт роли `--backend`/`--worker` (флаг > env > дефолт). Лаунчер —
третья роль/процесс.

Итоговая модель (после уточнений): **не always-on прокси, а stdio-шим** — MCP-клиент
сам спавнит процесс по stdio (транспорт `command`), поэтому в покое не крутится ничего.

## What was done

- **Роль `--mcp-stdio`** в `src/app.py` (флаг `store_true` + ветка диспетчеризации до
  role-env; ленивый импорт шима). Обновлён docstring/примеры запуска.
- **Шим** `src/apps/app/mcp_stdio.py`: `_resolve_code` (настройка / единственный
  смонтированный сервер), `_backend_alive` (`GET /internal/health`), `_spawn_backend`
  (`app.py --backend [--worker]`, `start_new_session`, stdio в лог-файл, форс
  `SERVER_ENABLED`/`WORKER_ENABLED`/`SERVER_HOT_RELOAD`), `_wait_ready` (поллинг до
  таймаута), `_open_home` (системный браузер, только при реальном подъёме), `_build_proxy`
  (`create_proxy(StreamableHttpTransport(.../mcp/<code>, auth=MCP_TOKEN))`, ленивый fastmcp),
  `run_mcp_stdio`. Backend переживает шим, гасят вручную (без idle-stop).
- **Config** (`src/core/config.py`): `mcp_stdio_open_browser`/`_start_worker`/`_boot_timeout`/`_code`.
- **Env**: `MCP_STDIO_*` в `.env`, `.env.example.dev`, `.env.example.prod`.
- **IDE**: `dev/.run/run-mcp-stdio.run.xml`.
- **Доки**: `AGENTS/docs/platform/mcp-stdio-shim.md` + строка-роутер в `MEMORY.md`.
- **Тесты**: `tests/apps/test_mcp_stdio.py` (16 pure — резолв кода, alive/spawn/wait/ensure/
  browser/proxy/run, mocked subprocess/httpx/webbrowser) + 2 в `tests/apps/test_app.py`
  (парсинг флага + диспетчеризация `main`). Живой smoke против поднятого backend:
  `create_proxy` отдаёт все 23 тула `research` через токен. `--core` зелёный (284).

## Problems

Изначально предложил always-on reverse-proxy демон (HTTP). Пользователь уточнил «в покое
ничего» → перешли на stdio-модель, где триггер подъёма — сам MCP-клиент (спавн `command`).
Это убрало необходимость держать процесс на порту и проксировать SSE.

**Баг на приёмке (проверка «работает»):** `CoreLogger` по умолчанию `stdout=True` — первый
же `_LOG.info` в шиме писал строку в stdout и рвал JSONRPC (`Failed to parse JSONRPC`).
Фикс: `_use_file_only_logging` в начале `run_mcp_stdio` ставит фабрику `stdout=False`
(логи только в `logs/mcp.log`). После фикса stdout чист (0 ошибок парсинга).

**Проверка вживую (E2E через fastmcp `StdioTransport`, клиент спавнит `--mcp-stdio`):**
(1) тёплый путь (backend жив) — мост отдаёт 23 тула + `research_list` вызов ок;
(2) **холодный старт** (порт 12200 свободен) — шим сам спавнит backend, ждёт готовность,
мостит за 2.4s, 23 тула; (3) спавненный backend **пережил смерть шима** (detached,
`start_new_session`) — подтверждает «гасят вручную». Браузер в тесте отключён
(`MCP_STDIO_OPEN_BROWSER=false`), путь `_open_home` — под юнит-тестом.

## Result

Новые: `src/apps/app/mcp_stdio.py`, `tests/apps/test_mcp_stdio.py`,
`dev/.run/run-mcp-stdio.run.xml`, `AGENTS/docs/platform/mcp-stdio-shim.md`,
`AGENTS/tasks/2026-07-08-launcher-wake-daemon.md`.
Изменены: `src/app.py`, `src/core/config.py`, `.env`, `.env.example.dev`,
`.env.example.prod`, `tests/apps/test_app.py`, `AGENTS/memory/MEMORY.md`.

**Как включить:** в конфиге MCP-клиента заменить `url:` на `command`-запись
(`uv run python src/app.py --mcp-stdio`, `cwd` = корень проекта) — см. доку.
