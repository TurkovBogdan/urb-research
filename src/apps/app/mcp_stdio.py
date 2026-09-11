"""MCP stdio-шим: клиент спавнит нас как ``command``-сервер, мы поднимаем backend.

Модель «в покое не крутится ничего»: MCP-клиент запускает этот процесс по stdio
(транспорт ``command``), а не ходит на HTTP-порт. При старте шим:

1. Проверяет, поднят ли backend (HTTP ``/internal/health``). Если нет — спавнит
   ``src/app.py --backend`` отдельной сессией (``start_new_session`` — процесс
   переживает смерть шима: MCP-сессия закончилась, а сервер остаётся; гасят
   вручную) и ждёт готовности. Готовность — ``status="ok"`` в теле, а не сам код 200:
   backend с отставшей схемой отвечает 200 и ``degraded``, и шим отказывает,
   назвав неприменённые ревизии. Под флагом обновления не спавнит вовсе.
   Сам спавн и опрос готовности — общие с апдейтером (``core/backend_launch.py``).
2. Открывает системный браузер на главной SPA — только когда backend реально
   подняли (если сервер уже был жив, страница и так открыта, второй вкладкой не
   спамим).
3. Работает мостом stdio ↔ HTTP-MCP backend (``fastmcp`` proxy): вызовы уходят на
   ``/mcp/<code>`` живого сервера и возвращаются клиенту.

stdout зарезервирован под MCP-протокол — диагностика идёт в лог-канал (файл, не
поток), а stdio backend-подпроцесса отвязан в свой лог-файл, не в пайп клиента.

``fastmcp`` (+13 МБ) импортируется лениво в ``_build_proxy`` — импорт самого модуля
форк не тянет (как и остальная MCP-инфра).
"""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from src.core import maintenance
from src.core.backend_launch import (
    base_url,
    probe_health,
    spawn_backend,
    wait_until_ready,
)
from src.core.config import Config
from src.core.loggers import get_logger

_LOG = get_logger("mcp")


def _use_file_only_logging(config: Config) -> None:
    """Логи шима — только в файл: stdout несёт MCP-протокол, echo туда рвёт JSONRPC.

    ``CoreLogger`` по умолчанию дублирует в stdout; здесь ставим фабрику с
    ``stdout=False`` до первого лога (прокси ``get_logger`` резолвит на неё)."""
    from src.core.app_path import AppPath, ensure_dirs
    from src.core.loggers import set_logger_factory
    from src.core.loggers.core_logger import CoreLogger

    paths = AppPath.from_root()
    ensure_dirs(paths)
    set_logger_factory(
        lambda channel: CoreLogger(
            logs_dir=paths.logs,
            file_name=channel,
            level=config.app_log_level,
            stdout=False,
        )
    )


def _resolve_code(config: Config) -> str:
    """Код смонтированного MCP-сервера: из настройки или единственный из модулей."""
    if config.mcp_stdio_code:
        return config.mcp_stdio_code
    from src.apps.app.modules import build_modules

    codes = [code for module in build_modules() for code in module.mcp_servers]
    if len(codes) == 1:
        return codes[0]
    raise RuntimeError(
        f"mcp-stdio: ожидался ровно один MCP-сервер (нашлось {len(codes)}: {codes}); "
        "задайте MCP_STDIO_CODE"
    )


def _backend_log_path(config: Config) -> Path:
    from src.core.app_path import AppPath, ensure_dirs

    paths = AppPath.from_root()
    ensure_dirs(paths)
    return paths.logs / "mcp_stdio_backend.log"


def _spawn_backend(config: Config) -> None:
    """Поднять backend отдельной сессией; его stdio отвязан от пайпа MCP-клиента."""
    command = spawn_backend(
        (sys.executable,),
        with_worker=config.mcp_stdio_start_worker,
        log_path=_backend_log_path(config),
    )
    _LOG.info("mcp-stdio: spawned backend %s → %s", " ".join(command), _backend_log_path(config))


def _open_home(config: Config) -> None:
    if config.mcp_stdio_open_browser:
        webbrowser.open(base_url(config) + "/")


def _refuse_during_update() -> None:
    """Под поднятым флагом backend не спавним: апдейтер переписывает дерево под нами.

    Запуск шима гейтит и `app.py::main`, но флаг может подняться между той проверкой и
    этой — гонка закрывается здесь.
    """
    held = maintenance.active()
    if held is None:
        return
    raise RuntimeError(
        f"mcp-stdio: идёт обновление установки ({held.describe()}) — backend не поднимаем; "
        "переподключитесь после завершения обновления"
    )


def _ensure_backend(config: Config) -> None:
    """Backend готов → ничего. Деградировал → отказ с причиной. Иначе спавним и ждём."""
    _refuse_during_update()
    health = probe_health(config)
    if health is not None:
        if health.is_ready:
            _LOG.info("mcp-stdio: backend already up at %s", base_url(config))
            return
        raise RuntimeError(
            f"mcp-stdio: backend на {base_url(config)} не готов — {health.describe()}"
        )
    _spawn_backend(config)
    booted = wait_until_ready(config, timeout=config.mcp_stdio_boot_timeout)
    if booted is None:
        raise RuntimeError(
            f"mcp-stdio: backend не поднялся за {config.mcp_stdio_boot_timeout}s "
            f"(см. {_backend_log_path(config)})"
        )
    if not booted.is_ready:
        raise RuntimeError(f"mcp-stdio: backend поднялся, но не готов — {booted.describe()}")
    _open_home(config)


def _build_proxy(config: Config, code: str):
    from fastmcp.client.transports import StreamableHttpTransport
    from fastmcp.server import create_proxy

    url = f"{base_url(config)}/mcp/{code}"
    transport = StreamableHttpTransport(url, auth=config.mcp_token or None)
    return create_proxy(transport, name=code)


def run_mcp_stdio(config: Config) -> None:
    """Поднять backend (если нужно) и запустить stdio-мост к его MCP-серверу."""
    _use_file_only_logging(config)
    code = _resolve_code(config)
    _ensure_backend(config)
    proxy = _build_proxy(config, code)
    proxy.run(show_banner=False)


__all__ = ["run_mcp_stdio"]
