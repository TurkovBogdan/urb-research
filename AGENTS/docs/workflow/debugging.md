# Debugging Guide

## Порты dev-окружения

Порты задаются в `.env` и читаются скриптами автоматически.

| Переменная | Сейчас | Назначение |
|------------|--------|------------|
| `SERVER_PORT` | **12200** | FastAPI backend (uvicorn) |
| `SERVER_VITE_PORT` | **12100** | Vite HMR / веб-интерфейс |

## Запуск dev-окружения

Запустить compound `group-server` в IDE (`tool-stop-all` → `watch-web` + `run-server-worker`). Он поднимает два процесса:

| Процесс | Конфиг | Адрес |
|---------|--------|-------|
| Vite HMR | `watch-web` | http://localhost:12100 |
| FastAPI + встроенный worker | `run-server-worker` | http://localhost:12200 |

Бекенд — `src/app.py --backend --worker --hot-reload` (`APP_ENV=dev`, `DB_AUTO_MIGRATE=false`); Vite на `:12100` раздаёт фронт с HMR и проксирует `/api`/`/internal` → бекенд. UI открываешь в браузере на `:12100`. Подробно — [`dev/docs/DEVELOPMENT.md`](../../../dev/docs/DEVELOPMENT.md).

Перезапустить только бекенд (например, после миграции):
```bash
bash AGENTS/tools/restart-backend.sh   # читает SERVER_PORT из .env
```

## Отладка в браузере

**Открыть веб-интерфейс:** http://localhost:12100

### Через MCP claude-in-chrome (основной способ для агента)

Использовать инструменты `mcp__claude-in-chrome__*` для прямой инспекции интерфейса в браузере пользователя:

```
navigate → http://localhost:12100
read_page / get_page_text   — DOM и текст
read_console_messages       — ошибки JS и Vue
read_network_requests       — API-запросы и ответы
javascript_tool             — выполнить произвольный JS
find                        — найти элемент на странице
```

Это живой браузер пользователя — видно реальное состояние UI, можно кликать, вводить данные, проверять сетевые запросы.

Vite проксирует `/internal/*` (и `/api/*`) → http://localhost:12200 (FastAPI backend).

**DevTools браузера** (Chrome/Firefox F12):
- Network → видно все API-запросы с реальными URL и ответами
- Console → ошибки Vue/Vuetify
- Vue DevTools (расширение) → состояние компонентов и Pinia stores

## Отладка API

Все прикладные маршруты живут в зоне `internal` (префикс `/internal`) и закрыты
session-cookie аутентификацией (`guard_auth` по умолчанию) — голый `curl` без cookie
вернёт 401. Удобнее дёргать API через вкладку браузера (cookie уже стоит) или
`mcp__claude-in-chrome__read_network_requests`. Публичный без auth — только `/internal/health`.

```bash
# Health (public)
curl http://localhost:12200/internal/health
```

> **Swagger/OpenAPI выключены** — `create_app` ставит `openapi_url=None`, так что `/docs`
> и `/openapi.json` недоступны. Список маршрутов смотри в коде (`internal_router` модулей)
> или через `app.routes`.

### Гоча: ширина окна Chrome зажата tiling-WM

В этом окружении tiling-WM зажимает любое окно Chrome до ~788px по ширине; `resize_window` /
`window.resizeTo` / F11 — все no-op для `innerWidth` (`screen.width=1920`, но вьюпорт залип). То есть
прогнать настоящий десктоп-вьюпорт (≥960) прямо в браузере нельзя. Обходной приём: проверять десктопную
ветку на вкладке, где `.vue` уже сделал HMR, а плагин `vuetify.ts` ещё не перезагрузился (поэтому
`mobile=false`). Для адаптива см. `responsive_testing_process` в памяти.

## Логи

```bash
# Backend stdout — /tmp/hh-server.log (при запуске через restart-backend.sh)
tail -f /tmp/hh-server.log

# Task-логи
tail -f runtime/dev/logs/tasks.log
```

## Частые проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| 502 на `/api/*` | бекенд не запущен | Запустить `run-server-worker` или весь `group-server` |
| Порт занят при старте | Старый процесс висит | `bash AGENTS/tools/stop-all.sh` |
