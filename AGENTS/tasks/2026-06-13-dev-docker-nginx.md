---
title: Dev Docker nginx front
date: 2026-06-13
status: in-work
description: "Local dev nginx container (single origin, like prod) so the private-zone file flow (X-Accel-Redirect / internal location) can be exercised locally — Vite dev-server can't do it. SPA proxied to Vite (HMR kept); backend zones proxied to the host dev backend."
tags: [dev, docker, nginx, storage]
---

## Task

Развернуть для разработки docker-контейнер с nginx. Главная цель (со слов пользователя):
**проверять отдачу файлов в приватной зоне** (`/storage/protected/` через `X-Accel-Redirect`),
чего Vite dev-server не умеет.

## Context

- Прод-контейнер `core.example.com` (вне репо, рядом с чекаутом) уже реализует схему:
  nginx раздаёт `static/` + `/storage/public/` напрямую, `/storage/protected/` = `internal;`
  + alias (отдаётся только по `X-Accel-Redirect` бэкенда), `/internal`,`/api`,`/mcp` → backend.
- В dev фронт отдаёт Vite (`:12100`, HMR) и сам проксирует `/internal`,`/api` → backend (`:12200`,
  `127.0.0.1`). Vite не знает про `internal`-локации и `X-Accel-Redirect`, поэтому приватную зону
  через него не проверить — отсюда нужен nginx-фронт.
- ОГОВОРКА: бэкенд-эндпоинт, эмитящий `X-Accel-Redirect`, в коде ещё НЕ реализован (отложен до
  `core_auth`, см. `2026-06-02-server-docker-migration`). Файлов в `storage/protected/` тоже нет.
  nginx-фронт проверяет саму механику зоны (direct → 404; public → 200); сквозной X-Accel-сценарий
  заработает с появлением эндпоинта.

## Decisions (с пользователем)

- Состав: **только nginx** в Docker; backend + Vite остаются на хосте как сейчас.
- Сеть: `network_mode: host` (Linux) → апстримы на `127.0.0.1:12100` (Vite) / `12200` (backend).
- SPA: nginx **проксирует `/` → Vite** (HMR сохраняется), не раздаёт собранную static.
- Размещение: **в репозитории `dev/docker/`** (рядом с `dev/.run`, `dev/docs`).
- Внешний порт фронта: `:8080`.

## What was done

- `dev/docker/docker-compose.dev.yml` — один сервис `nginx:1.27-alpine`, `network_mode: host`,
  bind-mount репозитория `../..:/srv/project:ro` + конфиг.
- `dev/docker/nginx/default.conf` — адаптация боевого шаблона под dev: `/` → Vite (с
  WebSocket-upgrade для HMR), `/internal`,`/api`,`/webhook` → backend, `/mcp` → backend без
  буферизации (стриминг), `/storage/public/` alias напрямую, `/storage/protected/` `internal;` + alias.
- `dev/docker/README.md` — запуск + smoke-тесты.

## Result

См. файлы в `dev/docker/`. Эндпоинт X-Accel в приложении — отдельная работа (core_auth).
