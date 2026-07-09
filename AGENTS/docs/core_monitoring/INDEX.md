# core_monitoring — раздел «Задачи» (список + запуски + логи)

Инфра-модуль наблюдаемости (`src/modules/core_monitoring/`): read-only HTTP-поверхность
над планировщиком. Своих таблиц/миграций/настроек **нет** — читает core-CRUD
(`core/crud/tasks`, `core/crud/tasks_logs`) и реестр планировщика (`core/scheduler/registry`).
Портирован из `AGENTS/semaphore-core` без auth-частей (проект без auth / без `core_users`).

## Backend

- `module.py` — `CoreMonitoringModule`: `migrations_dir/config_cls/settings_schema = None`,
  `internal_router` без `internal_router_prefix` (корень пути — в самих маршрутах). Регистрируется
  в `apps/app/modules.py::build_modules`.
- `api/tasks.py` — зона **internal** (в чистом ядре = `allow_all`, guard не нужен). Эндпойнты:
  - `GET /tasks` — все зарегистрированные задачи (реестр) + `stats_24h` (total/success/error/running),
    сортировка `core → core_* → модули`, затем `module`, затем `sort`.
  - `GET /tasks/{module}/{code}` — одна задача (+ её 24ч-статистика); 404 если не в реестре.
  - `GET /tasks/{module}/{code}/runs` — запуски (`core_tasks`) с пагинацией (`limit/offset`),
    фильтром `status` (`CoreTaskStatus`) и серверной сортировкой (`sort_by`/`sort_dir`).
  - `GET /tasks/{module}/{code}/runs/{run_id}/logs` — логи одного запуска (`core_tasks_logs`, asc).
  - Даты сериализуются `DatetimeUTCStr` (`core/utils/date`, SQL-формат `YYYY-MM-DD HH:MM:SS`).
- Фактические пути в приложении — под `/internal` (зон-агрегатор): `/internal/tasks…`.

## Frontend (`web/src/features/core_monitoring/`)

- `api.ts` — клиент (`fetchTasks`, `fetchTask`, `fetchTaskRuns`, `fetchTaskRunLogs`); базовый путь
  `/tasks` (клиент `internalApi` добавляет `/internal`).
- `stores/tasks.store.ts` — Pinia-стор списка: кэш в `localStorage` (`core.tasks.list`,
  stale-while-revalidate), фильтр `all|running|errors` + поиск, группировка по модулям, summary.
- `taskText.ts` — i18n-имя/описание задачи по паре `(module, code)`: `<module>.task.<code>.<field>`
  → `core_monitoring.catalog.<module>.<code>.<field>` → литерал с бэка (`NAME`/`DESCRIPTION`).
- `views/TasksView.vue` — карточки задач (KPI, бейджи enabled/schedule/TTL, 24ч-статистика),
  клик → запуски. `views/TaskRunsView.vue` — `VDataTable` запусков (серверная сортировка/пагинация
  `TablePaginationBar`), разворот строки = payload + логи запуска (ленивая догрузка).
- `routes.ts` — `/tasks` (TasksView), `/tasks/:module/:code` (TaskRunsView). Подключены в
  `web/src/router/index.ts`; пункт «Мониторинг задач» — в `AppSidebar.vue` (хардкод-массив `nav`).
- i18n — `locales/ru.json` (namespace `core_monitoring`, грузится глобом `features/*/locales/ru.json`).

## Опущено из эталона (нет в этом проекте)

Guard'ы (`@guard`), ручной запуск задач (`/core-users/task-requests`, кнопка «Запустить», `$can`),
раздел «Запросы задач» (`TaskRequestsView`, зависит от `core_users`), `/monitor`-локи. При появлении
auth/`core_users` — до-портировать оттуда.

## Прод-раздача

Фронт собран в `web/dist` (коммитится). После правок фичи — `pnpm --dir web build` перед коммитом
dist; в dev (Vite) изменения видны сразу.
