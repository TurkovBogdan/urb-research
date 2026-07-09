"""Единая точка входа: запуск процесса (server/worker) и миграции БД.

Без подкоманды — ЗАПУСК процесса. Роль — композиция двух поверхностей
(приоритет флаг > env > дефолт):

    uv run python src/app.py --backend --worker   — dev: веб + задачи в одном процессе
    uv run python src/app.py --backend             — prod-web: только HTTP
    uv run python src/app.py --worker              — prod-worker: только фон
    uv run python src/app.py                       — роль из env (SERVER_ENABLED/WORKER_ENABLED)
    uv run python src/app.py --mcp-stdio           — MCP stdio-шим: клиент спавнит нас,
                                                     шим лениво поднимает backend + браузер

Подкоманда `migrate` — миграции БД отдельным прогоном (без подъёма сервера):

    uv run python src/app.py migrate            — dry-run сверка (alias check); exit 1 при drift
    uv run python src/app.py migrate check
    uv run python src/app.py migrate upgrade    — накатить ядро + модули до head

`--backend`/`--worker` (и `--no-backend`/`--no-worker`) перекрывают env-тогглы
`SERVER_ENABLED`/`WORKER_ENABLED`. Флаги выставляются в env ДО `Config()`, поэтому
их наследуют reload/processes-подпроцессы uvicorn.

Поверхности:
- **SERVER** (`SERVER_ENABLED`) — HTTP-сервер (зоны internal/external/webhook).
  Поднимается через uvicorn на `SERVER_HOST:SERVER_PORT`. `SERVER_HOT_RELOAD=true`
  → один процесс с watch по `src/` (dev); иначе `SERVER_PROCESSES` процессов.
- **WORKER** (`WORKER_ENABLED`) — планировщик + выполнение задач. Когда SERVER
  выключен, процесс — чистый worker: БЕЗ uvicorn и без биндинга порта, lifespan
  гоняется напрямую; scope ограничивается `WORKER_MODULES`. При `SERVER_HOT_RELOAD`
  чистый worker поднимается под watch (`watchfiles`) — тот же ключ, что и у сервера:
  worker-подпроцесс рестартует на правках `src/`. Встроенный worker (вместе с
  SERVER) перезагружается заодно с uvicorn-reload.

Когда включён SERVER, встроенный тикер поднимается в lifespan приложения по
`WORKER_ENABLED` (так dev держит и веб, и задачи). Чистый worker (без SERVER)
форсит тикер через `scheduler.configure_worker`.

`migrate` использует тот же `AlembicRunner`, что и lifespan; `DB_AUTO_MIGRATE`
для него не действует — это явная операция. На prod-web держат `DB_AUTO_MIGRATE=false`
и накатывают `src/app.py migrate upgrade` отдельным шагом деплоя. Статику фронта
раздаёт nginx (prod) / Vite (dev).
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

# Точка входа лежит в src/ — корень проекта это родитель src/.
sys.path.insert(0, str(Path(__file__).parents[1]))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="app",
        description="Запуск процесса (server/worker) или миграции БД (migrate).",
    )
    # ── флаги запуска (top-level; действуют, когда подкоманда не задана) ──────
    p.add_argument(
        "--backend",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="поднимать HTTP-сервер; перекрывает SERVER_ENABLED (флаг > env)",
    )
    p.add_argument(
        "--worker",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="поднимать планировщик + задачи; перекрывает WORKER_ENABLED (флаг > env)",
    )
    p.add_argument(
        "--mcp-stdio",
        action="store_true",
        help="роль MCP stdio-шима: клиент спавнит по stdio, шим лениво поднимает "
        "backend + браузер и мостит вызовы на его /mcp/<code> (см. apps/app/mcp_stdio.py)",
    )
    p.add_argument(
        "--hot-reload",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="hot-reload сервера/воркера на правках src/ (dev); перекрывает SERVER_HOT_RELOAD",
    )
    p.add_argument("--host", default=None, help="перекрыть SERVER_HOST")
    p.add_argument("--port", type=int, default=None, help="перекрыть SERVER_PORT")
    p.add_argument(
        "--processes",
        type=int,
        default=None,
        help="перекрыть SERVER_PROCESSES (игнорируется при hot-reload)",
    )
    p.add_argument(
        "--debug-delay",
        type=int,
        default=None,
        metavar="MS",
        help="DEBUG: задержка (мс) на каждый запрос internal API; ← SERVER_DEBUG_DELAY_MS (0=выкл)",
    )
    p.add_argument(
        "--worker-module",
        action="append",
        default=None,
        metavar="NAME",
        help="scope воркера: только задачи этого модуля (повторяемый); ← WORKER_MODULES",
    )
    p.add_argument(
        "--worker-tick-seconds",
        type=int,
        default=None,
        help="перекрыть WORKER_TICK_SECONDS",
    )
    p.add_argument(
        "--worker-max-concurrent",
        type=int,
        default=None,
        help="перекрыть WORKER_MAX_CONCURRENT_RUNS",
    )

    # ── подкоманда migrate ───────────────────────────────────────────────────
    sub = p.add_subparsers(dest="command")
    mig = sub.add_parser("migrate", help="миграции БД (check|upgrade)")
    mig.add_argument(
        "action",
        nargs="?",
        choices=("check", "upgrade"),
        default="check",
        help="check — dry-run сверка (дефолт); upgrade — накатить до head",
    )
    return p.parse_args(argv)


def _apply_env_overrides(args: argparse.Namespace) -> None:
    """CLI > env: выставить env ДО Config()/импорта приложения.

    Значения подхватят и reload-, и processes-подпроцессы uvicorn (наследуют env).
    """
    if args.backend is not None:
        os.environ["SERVER_ENABLED"] = "true" if args.backend else "false"
    if args.worker is not None:
        os.environ["WORKER_ENABLED"] = "true" if args.worker else "false"
    if args.hot_reload is not None:
        os.environ["SERVER_HOT_RELOAD"] = "true" if args.hot_reload else "false"
    if args.debug_delay is not None:
        os.environ["SERVER_DEBUG_DELAY_MS"] = str(args.debug_delay)
    if args.worker_module is not None:
        os.environ["WORKER_MODULES"] = ",".join(args.worker_module)
    if args.worker_tick_seconds is not None:
        os.environ["WORKER_TICK_SECONDS"] = str(args.worker_tick_seconds)
    if args.worker_max_concurrent is not None:
        os.environ["WORKER_MAX_CONCURRENT_RUNS"] = str(args.worker_max_concurrent)


def _run_server(config, args: argparse.Namespace) -> None:
    """Поднять HTTP-сервер через uvicorn. Встроенный тикер — в lifespan по WORKER_ENABLED."""
    import uvicorn

    host = args.host or config.server_host
    port = args.port or config.server_port
    log_level = config.app_log_level.lower()
    if config.server_hot_reload:
        # --reload несовместим с processes>1: reload-супервизор держит один процесс.
        uvicorn.run(
            "src.apps.app.server:app",
            host=host,
            port=port,
            reload=True,
            reload_dirs=[str(Path(__file__).parent)],
            log_level=log_level,
        )
        return
    uvicorn.run(
        "src.apps.app.server:app",
        host=host,
        port=port,
        workers=args.processes or config.server_processes,
        log_level=log_level,
    )


def _run_worker_hot_reload() -> None:
    """Чистый worker под watch: рестарт worker-подпроцесса на правках src/ (dev).

    Тот же ключ `SERVER_HOT_RELOAD`, что и у сервера. У чистого worker нет uvicorn
    (а значит и его reload-супервизора), поэтому watch держим сами через
    `watchfiles.run_process`: на изменение `src/` подпроцесс перезапускается с нуля.
    Дочерний процесс — тот же `src/app.py --worker --no-backend`, но уже `--no-hot-reload`
    (иначе рекурсия watch-watch); scope/ручки наследуются через env.
    """
    import shlex

    from watchfiles import run_process

    src_dir = str(Path(__file__).parent)
    cmd = shlex.join(
        [sys.executable, str(Path(__file__)), "--worker", "--no-backend", "--no-hot-reload"]
    )
    run_process(src_dir, target=cmd)


async def _run_worker(config) -> None:
    """Чистый worker: lifespan напрямую, без uvicorn/порта. Ждёт SIGTERM/SIGINT."""
    from src.apps.app.modules import build_modules
    from src.core import scheduler
    from src.core.app_factory import create_app

    # Форсим тикер (минуя SERVER) + задаём scope/ручки из config.
    scheduler.configure_worker(
        modules=config.worker_modules_set,
        max_concurrent=config.worker_max_concurrent_runs,
        tick=config.worker_tick_seconds,
    )
    app = create_app(modules=build_modules(), config=config)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover — не-POSIX
            pass

    async with app.router.lifespan_context(app):
        await stop.wait()


# ── миграции (подкоманда migrate) ───────────────────────────────────────────


def _print_migration_status(status) -> None:
    print(f"current heads: {', '.join(status.current_heads) or '(none — fresh DB)'}")
    print(f"target heads:  {', '.join(status.target_heads) or '(none)'}")
    if status.up_to_date:
        print("migrations: up to date — nothing to apply")
        return
    print(f"pending ({len(status.pending)}):")
    for rev in status.pending:
        print(f"  {rev.revision}  {rev.message}")
        print(f"      {rev.path}")


async def _run_migrate(action: str) -> int:
    """check — вывести состояние (exit 1 при drift); upgrade — накатить до head."""
    from src.apps.app.modules import build_modules
    from src.core.config import Config
    from src.core.database import close_database, init_database
    from src.core.database.migrations import AlembicRunner

    runner = AlembicRunner(modules=build_modules())
    engine = await init_database(Config())
    try:
        status = await runner.status(engine)
        _print_migration_status(status)
        if action == "check":
            return 0 if status.up_to_date else 1
        if status.up_to_date:
            return 0
        await runner.upgrade_head(engine)
        print("migrations: applied — now at head")
    finally:
        await close_database()
    return 0


def main(argv: list[str] | None = None) -> int | None:
    args = _parse_args(argv)

    if args.command == "migrate":
        return asyncio.run(_run_migrate(args.action))

    if args.mcp_stdio:
        # Шим сам поднимает backend отдельным процессом — role-env этого процесса
        # не трогаем (он не server и не worker, а stdio-мост).
        from src.apps.app.mcp_stdio import run_mcp_stdio
        from src.core.config import Config

        run_mcp_stdio(Config())
        return None

    _apply_env_overrides(args)

    from src.core.config import Config

    config = Config()
    if not config.server_enabled and not config.worker_enabled:
        # Ни одной поверхности — не ошибка, а валидный no-op (например, процесс,
        # который запускали только под `migrate`). Чистый выход (код 0).
        print(
            "ни SERVER, ни WORKER не включены — нечего запускать (для миграций: "
            "`src/app.py migrate`). Выход."
        )
        return None

    if config.server_enabled:
        # Встроенный worker (если WORKER_ENABLED) поднимется в lifespan приложения.
        _run_server(config, args)
        return None
    # Чистый worker — без uvicorn и без порта.
    if config.server_hot_reload:
        _run_worker_hot_reload()
    else:
        asyncio.run(_run_worker(config))
    return None


if __name__ == "__main__":
    raise SystemExit(main())
