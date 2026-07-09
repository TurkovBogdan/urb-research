# core/scheduler

Планировщик фоновых задач: тикер с фиксированным шагом, модуль-глобальный реестр, owner-based авто-снятие локов, heartbeat и cleanup zombie-запусков.

## Где регистрируются задачи

Соглашение: handler-ы и регистрация лежат в `tasks.py` или пакете `tasks/` рядом с кодом, который их выполняет:

- ядро — `src/core/tasks.py`, регистрируется из `app_factory.create_app`.
- модуль — `src/modules/<name>/tasks.py` либо `src/modules/<name>/tasks/<task>_task.py`, регистрируется из `register(app, settings)` модуля.

`module` в `scheduler.register` — полное имя модуля (`"headhunter"`, не `"hh"`).

## Регистрация задачи

Каждая задача — статичный класс с `register()` и `handle()`:

```python
from src.core import scheduler
from src.core.scheduler import TaskContext


class SyncVacanciesTask:
    """Один прогон синхронизации вакансий."""

    @staticmethod
    def register() -> None:
        scheduler.register(
            module="headhunter",
            code="sync_vacancies",
            name="Синхронизация вакансий",
            description="Каждые 5 минут тянет свежие вакансии из выдачи hh.ru.",
            schedule="*/5 * * * *",   # стандартный 5-польный cron
            handler=SyncVacanciesTask.handle,
            ttl=300,                   # секунды; и timeout хендлера, и TTL task-лока
            enabled=True,              # false → тикер пропускает задачу
            manual_run=False,          # true → задачу можно запустить вручную через UI
        )

    @staticmethod
    async def handle(ctx: TaskContext) -> None:
        await ctx.info("syncing")
        # ... работа ...
```

Через `CoreTaskBase` (декларативный вариант):

```python
from src.core.scheduler import CoreTaskBase, TaskContext


class SyncVacanciesTask(CoreTaskBase):
    MODULE = "headhunter"
    CODE = "sync_vacancies"
    NAME = "Синхронизация вакансий"
    DESCRIPTION = "Каждые 5 минут тянет свежие вакансии из выдачи hh.ru."
    SCHEDULE = "*/5 * * * *"
    TTL = 300
    ENABLED = True
    MANUAL_RUN = False  # опционально; по умолчанию False

    @staticmethod
    async def handle(ctx: TaskContext) -> None:
        await ctx.info("syncing")
```

- **`schedule`** — стандартный 5-польный cron (`minute hour dom mon dow`). Минимальная гранулярность — раз в минуту. `None` — автозапуск отключён (тикер пропускает задачу; задача может быть запущена только вручную).
- **`ttl`** — целое число секунд. Используется и как `asyncio.wait_for` timeout, и как TTL task-лока.
- **`enabled`** — флаг активности; `false` отключает задачу на уровне реестра (тикер пропускает её при обходе, ничего не пишет в `core_tasks`).
- **`manual_run`** — разрешение ручного запуска через UI/API (`POST /api/core/tasks/{module}/{code}/run`). Декларативный флаг: `run_entry` безопасен для вызова откуда угодно, флаг только сигнализирует UI и защищает эндпоинт. По умолчанию `False`.
- **`sort`** — целое число, определяет порядок вывода задач в UI (меньше → раньше). Не влияет на выполнение задач. По умолчанию `500`.
- `(module, code)` уникальны в реестре. Двойная регистрация — `ValueError`.

### Паттерн: только ручной запуск

Задача без расписания — `schedule=None, manual_run=True`. Тикер её игнорирует; UI показывает кнопку "Запустить".

```python
class ReindexTask(CoreTaskBase):
    MODULE = "search"
    CODE = "reindex"
    NAME = "Переиндексация"
    DESCRIPTION = "Ручной полный пересчёт индекса."
    SCHEDULE = None       # не запускать автоматически
    TTL = 600
    MANUAL_RUN = True     # разрешить запуск через UI
```

## Что видит handler — `TaskContext`

```python
@dataclass
class TaskContext:
    task_id: int
    module: str
    code: str
    lock: CoreLock          # task-level лок: ключ "task:{module}:{code}", owner=task_run:{id}
```

- `ctx.{debug,info,warn,error}(msg, *args)` — пишет в `core_tasks_logs` и дублирует в канал `tasks` (`logs/tasks.log`). Каждый вызов — своя сессия с мгновенным коммитом, чтобы лог пережил отвал по TTL. Принимает `%`-args. Ошибки записи в БД глотаются — логирование не валит handler.
- `ctx.set_payload(payload)` — апдейт `core_tasks.payload` свежей сессией с мгновенным коммитом.
- `ctx.lock` — `CoreLock`-экземпляр task-уровня, поднятый раннером. Хендлер может звать `ctx.lock.is_owner()` / `ctx.lock.extend(ttl)` (например, для длинных задач с heartbeat-расширением).

### Суб-локи под тем же owner-ом

Если задача внутри хочет локи на ресурсы (`hh:sync`, `pdf:render` и т.д.) — берёт их через `CoreLock.acquire(...)`, передавая `owner=ctx.lock.owner`. Тогда runner в `finally` снимет всё одним `release_for_owners`:

```python
async def sync_vacancies(ctx):
    res = await CoreLock.acquire("hh:api", 60, owner=ctx.lock.owner)
    if res is None:
        return  # ресурс занят
    # ... работа; release можно не звать — runner подчистит ...
```

## Lifecycle

`scheduler.start(config)` стартует `Ticker`; `scheduler.stop()` останавливает. Оба зовутся из `lifespan` фабрики приложения. Источник параметров и сам факт старта зависят от роли процесса:

- **Встроенный (dev, `--backend --worker`):** старт по `config.worker_enabled`; scope/ручки — из `config` (`worker_modules_set`, `worker_tick_seconds`, `worker_max_concurrent_runs`). Один процесс держит и веб, и задачи.
- **Чистый worker (`--worker` без `--backend`):** точка входа `src/app.py` зовёт `scheduler.configure_worker(modules, max_concurrent, tick)` ДО lifespan — это форсит старт тикера (минуя `worker_enabled`) и задаёт scope. Процесс — без uvicorn/порта, lifespan гоняется напрямую.

Роль процесса — композиция флагов `--backend`/`--worker` (приоритет флаг > env > дефолт); см. [`dev/docs/ENV.md`](../../../dev/docs/ENV.md).

Настройки в `Config`:
- `WORKER_ENABLED` (default `false`) — встроенный планировщик внутри веб-бэкенда. `true` в dev (один процесс держит веб + задачи); прод-web оставляет `false` — фон в отдельном worker-процессе. В тестах `false`. Чистый worker форсит тикер через `configure_worker` независимо от флага.
- `WORKER_MODULES` (default пусто) — scope: CSV имён модулей; пусто = весь реестр. `Config.worker_modules_set` → `frozenset | None`; `Ticker(modules=...)` фильтрует реестр по `entry.module`.
- `WORKER_TICK_SECONDS` (default `5`) — гранулярность тика (ручка движка, общая для встроенного и worker). Поскольку минимум cron — 1 минута, дефолт `5` гарантирует, что тикер не пропустит минутную границу.
- `WORKER_MAX_CONCURRENT_RUNS` (default `10`) — потолок одновременных задач (asyncio.Semaphore в `Ticker`).

## Внутренности

### `Ticker._loop`

```
while not stop:
    _tick_once()
    wait(tick_seconds) или ранний выход по stop
```

`_tick_once`:
1. **Cleanup zombies.** `crud_tasks.cleanup_zombies(threshold_seconds)` финализирует `running`-записи со stale `heartbeat_at` как `error("orphaned: stale heartbeat")` и возвращает их id. Локи этих id (`owner=task_run:{id}`) снимаются bulk-ом через `release_for_owners`.
2. **Итерация реестра.** Если у тикера задан `modules` scope — записи других модулей пропускаются. Для каждого `TaskEntry` с `enabled=True` и `schedule != None` берём `last_run_at(module, code)` и проверяем `is_due(entry.schedule, now, last)`. Готовые — спавним. Записи с `schedule=None` пропускаются тикером всегда.

### Спавн и concurrency

`_spawn` создаёт `asyncio.Task`, регистрирует в `_active`, ставит `done_callback` на удаление. Внутри `_guarded_run` ограничивает concurrency через `asyncio.Semaphore(max_concurrent_runs)` и ловит исключения, чтобы упавший `run_entry` не валил тикер.

### `run_entry(entry)`

1. `crud_tasks.create_running(module, code)` — UPSERT с partial-unique индексом `(module, code) WHERE status='running'`. Возвращает `task_id` или `None` если уже running. Атомарно: одновременный двойной запуск — второй no-op.
2. `CoreLock.acquire("task:{module}:{code}", ttl=entry.ttl, owner="task_run:{task_id}")`. Если занят (например, висит лок от мёртвого процесса до его TTL) — `finalize_error("task lock busy")` и выход.
3. Стартует `_heartbeat_loop(task_id, interval=30)` — раз в 30s обновляет `heartbeat_at`, чтобы тикер другого инстанса не посчитал задачу зомби.
4. Вызывает `entry.handler(ctx)` под `asyncio.wait_for(timeout=entry.ttl)`.
5. `finally`:
   - `success` → `finalize_success`, `error`/`TimeoutError` → `finalize_error(text=...)` плюс traceback в `core_tasks_logs`.
   - heartbeat-задача отменяется.
   - `release_for_owners(["task_run:{task_id}"])` снимает task-лок и любые суб-локи с тем же owner-ом.

### Партициальный уникальный индекс

```sql
CREATE UNIQUE INDEX ux_core_tasks_running
  ON core_tasks (module, code) WHERE status = 'running';
```

Гарантирует на уровне БД, что две одновременных running-задачи одной `(module, code)` невозможны. Task-лок поверх этого даёт TTL-ограниченное удержание ресурса (полезно при cluster-deploy: если процесс убит без graceful shutdown, лок сам отпустится по TTL).

### Heartbeat и zombie-порог

- handler пишет `heartbeat_at` каждые 30s.
- `Ticker(zombie_threshold=90)` считает зомби, если `heartbeat_at < now - 90s`.
- Запас 3× против интервала heartbeat покрывает GC-паузы и кратковременные сетевые лаги.

### Shutdown

`Ticker.stop`:
1. `_stop.set()` — `_loop` выходит после текущего ожидания/тика.
2. `await asyncio.wait_for(gather(*active), timeout=shutdown_grace_seconds)` — ждём активные `run_entry`.
3. По таймауту — `cancel()` оставшимся.

В `lifespan` `scheduler.stop()` вызывается до `close_database`, чтобы дотекущие задачи могли финализироваться через сессии.

## Файлы

- `registry.py` — `TaskEntry`, `TaskRegistry`, `get_registry()`. Поля: `schedule: str | None` (cron или None), `manual_run: bool`.
- `context.py` — `TaskContext` (включая методы логирования и `set_payload`).
- `runner.py` — `run_entry`, heartbeat-loop.
- `ticker.py` — `Ticker` + функция `is_due(expression, now, last)` (5-польный cron). Пропускает записи с `schedule=None`.
- `task_base.py` — `CoreTaskBase`; атрибуты: `SCHEDULE: str | None`, `MANUAL_RUN: bool = False`.
- `__init__.py` — публичный API + `register/start/stop` + `configure_worker` (worker-override). HTTP-эндпоинты задач — в `src/core/api/system.py` (роутер `/api/core/tasks`).
