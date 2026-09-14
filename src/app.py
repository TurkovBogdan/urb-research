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

Подкоманда `backup` — копия базы (`src/core/backup.py`) перед миграцией: SQLite через
`VACUUM INTO` + `integrity_check`, PostgreSQL через `pg_dump --format=custom` с проверкой
`pg_restore --list`. Без аргумента путь выбирается по провайдеру:

    uv run python src/app.py backup            — рядом с файловой базой / runtime/<профиль>/backup
    uv run python src/app.py backup <путь>     — явный файл (существующий не перезаписывается)

Подкоманда `update` — обновление установки целиком (обёртка `./update.sh`): проверки,
флаг обслуживания, остановка процессов, fast-forward на origin/UPDATE_BRANCH, `uv sync`,
копия базы, миграции, рестарт с ожиданием готовности. `--dry-run` печатает шаги и план
остановки, не трогая ничего. Коды выхода: 0 — обновлено/уже актуально, 1 — не прошли
предусловия, 2 — флаг держит другой апдейтер, 3 — откат, 4 — упала миграция (флаг
оставлен поднятым), 5 — не снялась копия базы (схему не трогали), 6 — не удался откат,
7 — не удалось остановить процессы установки, 8 — backend не поднялся после обновления,
9 — обновление упало непредвиденно (в лог уходит traceback, флаг остаётся как был),
10 — найдены процессы установки без записи о себе (снять `--stop-unregistered`),
11 — платформа не поддерживается (Windows): напечатана ручная процедура.

Подкоманда `stop` — погасить процессы этой установки (и только её) по тем же записям
реестра и тем же слоем, что и обновление: группой TERM → CONT → KILL с доказательством
смерти, чужой пользователь и незарегистрированные процессы — отказ, а не тихий пропуск.
Vite остановка не касается — он не процесс приложения (его гасит `./run.sh stop`).

    uv run python src/app.py stop                       — погасить
    uv run python src/app.py stop --dry-run             — напечатать план, не трогая
    uv run python src/app.py stop --stop-unregistered   — гасить и процессы без записи

Коды выхода: 0 — погашено (или гасить было нечего), 7 — что-то пережило сигналы, процесс
чужого пользователя или общая группа с гасящим, 10 — найдены процессы без записи о себе,
11 — платформа не поддерживается (Windows).

Запуск процесса (server/worker) записывает себя в реестр `runtime/processes/<pid>.json`
(`src/core/process_registry.py`) и снимает запись при выходе: по этим записям обновление
гасит установку, вместо того чтобы опознавать её по cwd и argv.

Пока флаг обслуживания держит живой апдейтер (`runtime/maintenance.json`), ЗАПУСК
процесса отклоняется с кодом 1 — иначе MCP-шим поднял бы backend на полупереписанном
дереве. Подкоманды не гейтятся: обновление накатывает `backup` и `migrate upgrade` как
раз под поднятым флагом.

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

Миграции накатывает ТОЛЬКО `migrate upgrade` (и обновление установки, которое его
зовёт) — старт процесса не мигрирует базу, у которой уже есть схема: отставшая
цепочка поднимает приложение в режиме заглушки (`src/core/router/degraded.py`).
Исключение — пустая база: свежая установка накатывает цепочку сама. Статику фронта
раздаёт тот же backend из `web/dist` (в dev — Vite).
"""

import argparse
import asyncio
import atexit
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

    # ── подкоманда backup ────────────────────────────────────────────────────
    bak = sub.add_parser("backup", help="копия базы перед миграцией (sqlite/postgres)")
    bak.add_argument(
        "target",
        nargs="?",
        default=None,
        metavar="PATH",
        help="куда положить копию; пусто — рядом с файловой базой либо runtime/<профиль>/backup",
    )

    # ── подкоманда update ────────────────────────────────────────────────────
    upd = sub.add_parser("update", help="обновить установку до origin/UPDATE_BRANCH")
    upd.add_argument(
        "--dry-run",
        action="store_true",
        help="пройти последовательность и напечатать шаги (в т.ч. план остановки процессов), "
        "ничего не трогая: без сигналов, fetch/merge/sync, копии базы и миграций",
    )
    upd.add_argument(
        "--stop-unregistered",
        action="store_true",
        help="гасить и процессы этого чекаута без записи в реестре (иначе обновление "
        "отказывается с кодом 10); нужен один раз — на первом обновлении после выкатки реестра",
    )

    # ── подкоманда stop ──────────────────────────────────────────────────────
    stp = sub.add_parser("stop", help="погасить процессы этой установки по их записям в реестре")
    stp.add_argument(
        "--dry-run",
        action="store_true",
        help="напечатать план остановки и выйти, не подавая сигналов",
    )
    stp.add_argument(
        "--stop-unregistered",
        action="store_true",
        help="гасить и процессы этого чекаута без записи в реестре (иначе отказ с кодом 10)",
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


def _run_the_role(config, args: argparse.Namespace) -> None:
    """Собственно работа процесса: HTTP-сервер либо чистый worker (при hot-reload — под watch)."""
    if config.server_enabled:
        # Встроенный worker (если WORKER_ENABLED) поднимется в lifespan приложения.
        _run_server(config, args)
        return
    # Чистый worker — без uvicorn и без порта.
    if config.server_hot_reload:
        _run_worker_hot_reload()
        return
    asyncio.run(_run_worker(config))


def _run_recorded(config, args: argparse.Namespace) -> None:
    """Отработать роль, пока процесс записан в реестре установки (`process_registry`).

    Снятие записи нужно в двух местах: uvicorn возвращается из `run()` по SIGTERM и доходит до
    `finally`, а `SystemExit` из глубины (например, занятый порт) уходит через `atexit`. Ни то,
    ни другое не срабатывает на SIGKILL и на `os.execv` — запись, пережившую свой процесс,
    опознаёт по паре pid + время старта и убирает следующий `announce`.
    """
    from src.core import process_registry

    process_registry.announce(config)
    atexit.register(process_registry.withdraw)
    try:
        _run_the_role(config, args)
    finally:
        process_registry.withdraw()


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


def _launches_a_process(args: argparse.Namespace) -> bool:
    """Нет подкоманды — значит запускаем процесс (в том числе `--mcp-stdio`).

    Подкоманды (`migrate`, `backup`, `update`, `stop`) освобождены от гейта намеренно: сам
    апдейтер гоняет `backup` и `migrate upgrade` при поднятом флаге, а упавшая миграция
    флаг не опускает — гейт на подкомандах запер бы обновление изнутри и лишил бы повтора.
    """
    return args.command is None


def _maintenance_refusal() -> str | None:
    """Текст отказа, когда флаг обслуживания держит живой апдейтер; иначе None."""
    from src.core import maintenance

    held = maintenance.active()
    if held is None:
        return None
    return (
        f"идёт обновление установки ({held.describe()}) — запуск процесса запрещён.\n"
        f"дождитесь завершения обновления; флаг: {maintenance.flag_path()}"
    )


def main(argv: list[str] | None = None) -> int | None:
    args = _parse_args(argv)

    if args.command == "migrate":
        return asyncio.run(_run_migrate(args.action))

    if args.command == "backup":
        from src.core.backup import backup_command

        return backup_command(args.target)

    if args.command == "update":
        from src.core.update import update_command

        return update_command(dry_run=args.dry_run, stop_unregistered=args.stop_unregistered)

    if args.command == "stop":
        from src.core.update import stop_command

        return stop_command(dry_run=args.dry_run, stop_unregistered=args.stop_unregistered)

    if _launches_a_process(args):
        refusal = _maintenance_refusal()
        if refusal is not None:
            print(refusal, file=sys.stderr)
            return 1

    if args.mcp_stdio:
        # Шим сам поднимает backend отдельным процессом — role-env этого процесса
        # не трогаем (он не server и не worker, а stdio-мост).
        from src.apps.app.mcp_stdio import run_mcp_stdio
        from src.core.config import Config

        run_mcp_stdio(Config())
        return None

    _apply_env_overrides(args)

    from src.core.config import Config
    from src.modules.core_setup.env_file import (
        ensure_generated,
        ensure_keys_present,
        env_path,
        seed_defaults_if_absent,
    )

    config = Config()
    if seed_defaults_if_absent(config):
        print(f"первый запуск: создан {env_path()} со значениями по умолчанию")
    # Ключи, появившиеся позже самого файла, иначе не доезжают до живой установки:
    # ни в `.env`, ни на странице настроек их не видно, и поправить значение негде.
    for key in ensure_keys_present(config):
        print(f"добавлен со значением по умолчанию: {key} → {env_path()}")
    # Секреты установки досыпаются и в уже существующий .env: ключ шифрования появился
    # позже самого файла, и без этого шага он не завёлся бы ни на одной живой установке.
    for key in ensure_generated(config):
        print(f"сгенерирован {key} → {env_path()}")
    if not config.server_enabled and not config.worker_enabled:
        # Ни одной поверхности — не ошибка, а валидный no-op (например, процесс,
        # который запускали только под `migrate`). Чистый выход (код 0).
        print(
            "ни SERVER, ни WORKER не включены — нечего запускать (для миграций: "
            "`src/app.py migrate`). Выход."
        )
        return None

    _run_recorded(config, args)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
