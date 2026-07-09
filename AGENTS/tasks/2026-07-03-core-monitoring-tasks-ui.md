---
title: core_monitoring — раздел «Задачи» (список задач + запуски + логи)
date: 2026-07-03
status: completed  # in-work | completed | deferred
description: "Портировать из semaphore-core модуль core_monitoring: бэкенд /tasks (список задач + 24ч-статистика + запуски + логи запуска) и фронт-фичу (TasksView + TaskRunsView). Без auth: guard'ы, кнопка запуска и раздел «Запросы» опущены."
tags: [core_monitoring, tasks, frontend, observability]
---

## Task

«Как раньше выводили список задач и их логов — сделай так-же» (эталон
`AGENTS/semaphore-core` + `.../web`). Портировать раздел мониторинга задач.

## Context

Наш core уже держит планировщик + `core/crud/tasks.py`/`tasks_logs.py` +
`models/tasks.py`, но нет модуля `core_monitoring` (API) и фронт-фичи. Проект
**без auth** и без модулей `core_users`/`llm_providers`, поэтому из эталона
выпадают: guard'ы (`@guard(...)`), ручной запуск (`/core-users/task-requests`,
кнопка «Запустить», `$can`), раздел «Запросы».

## What was done

- **Backend** — новый read-only модуль `src/modules/core_monitoring/` (без таблиц/миграций/настроек):
  `module.py`, `constants.py`, `api/{__init__,tasks}.py`. Эндпойнты зоны internal (без prefix):
  `GET /tasks` (реестр + 24ч-статистика), `GET /tasks/{m}/{c}`, `GET /tasks/{m}/{c}/runs`
  (пагинация+фильтр статуса+серверная сортировка), `GET /tasks/{m}/{c}/runs/{run_id}/logs`.
  Читает `core/crud/tasks`+`tasks_logs`+реестр планировщика; даты — `DatetimeUTCStr`
  (SQL-формат). Зарегистрирован в `apps/app/modules.py::build_modules`.
- **Frontend** — фича `web/src/features/core_monitoring/`: `api.ts`, `taskText.ts`,
  `stores/tasks.store.ts` (кэш списка в localStorage), `views/TasksView.vue` (карточки задач
  + KPI + фильтр/поиск), `views/TaskRunsView.vue` (таблица запусков + разворот payload/логов),
  `routes.ts`, `locales/ru.json`. Роуты подключены в `router/index.ts`; пункт «Мониторинг
  задач» (IconClock) добавлен в `AppSidebar.vue`.
- **Опущено (проект без auth / без core_users)**: guard'ы `@guard(...)`, ручной запуск
  (`/core-users/task-requests`, кнопка «Запустить», `$can`), раздел «Запросы задач», `/monitor`-локи.
- **Тесты**: `tests/modules/core_monitoring/test_tasks_api.py` (список+статистика, 404,
  runs+logs roundtrip, фильтр статуса) — 4 шт.

## Result

- Новые файлы: `src/modules/core_monitoring/**` (5), `web/src/features/core_monitoring/**` (7),
  `tests/modules/core_monitoring/test_tasks_api.py`.
- Изменены: `src/apps/app/modules.py`, `web/src/router/index.ts`, `web/src/layout/components/AppSidebar.vue`.
- Записи: `docs/core_monitoring/INDEX.md`, `memory/MEMORY.md` (роутинг), tasks INDEX.
- Проверки: `pytest --module=core_monitoring` → 4 passed; `pytest --core` → 265 passed;
  `vue-tsc --noEmit` → 0; ASGI-смоук — 4 роута под `/internal/tasks`.
- **Не сделано**: пересборка `web/dist` (коммитится в репо; для прод-раздачи нужен
  `pnpm --dir web build` — в dev работает через Vite сразу).
