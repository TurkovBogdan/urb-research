"""MCP stdio-шим: клиент спавнит нас как ``command``-сервер, мы поднимаем backend.

Модель «в покое не крутится ничего»: MCP-клиент запускает этот процесс по stdio
(транспорт ``command``), а не ходит на HTTP-порт. При старте шим:

1. Проверяет, поднят ли backend (HTTP ``/internal/health``). Если нет — спавнит
   ``src/app.py --backend`` отдельной сессией (``start_new_session`` — процесс
   переживает смерть шима: MCP-сессия закончилась, а сервер остаётся; гасят
   вручную) и ждёт готовности.
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

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import httpx

from src.core.config import Config
from src.core.loggers import get_logger

_LOG = get_logger("mcp")

_APP_ENTRY = Path(__file__).resolve().parents[2] / "app.py"
_HEALTH_PATH = "/internal/health"
_READY_POLL_SECONDS = 0.3


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


def _connect_host(config: Config) -> str:
    """Хост локального подключения к backend: 0.0.0.0/пусто → 127.0.0.1."""
    return config.server_host if config.server_host not in ("", "0.0.0.0") else "127.0.0.1"


def _base_url(config: Config) -> str:
    return f"http://{_connect_host(config)}:{config.server_port}"


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


def _health_url(config: Config) -> str:
    return _base_url(config) + _HEALTH_PATH


def _backend_alive(config: Config) -> bool:
    try:
        response = httpx.get(_health_url(config), timeout=1.0)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


def _backend_log_path(config: Config) -> Path:
    from src.core.app_path import AppPath, ensure_dirs

    paths = AppPath.from_root()
    ensure_dirs(paths)
    return paths.logs / "mcp_stdio_backend.log"


def _spawn_backend(config: Config) -> None:
    """Поднять backend отдельной сессией; его stdio отвязан от пайпа MCP-клиента."""
    env = dict(os.environ)
    env["SERVER_ENABLED"] = "true"
    env["WORKER_ENABLED"] = "true" if config.mcp_stdio_start_worker else "false"
    env["SERVER_HOT_RELOAD"] = "false"
    command = [sys.executable, str(_APP_ENTRY), "--backend"]
    if config.mcp_stdio_start_worker:
        command.append("--worker")
    backend_log = open(_backend_log_path(config), "a")  # noqa: SIM115 — наследует потомок
    subprocess.Popen(
        command,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=backend_log,
        stderr=backend_log,
        start_new_session=True,
    )
    _LOG.info("mcp-stdio: spawned backend %s → %s", " ".join(command), _backend_log_path(config))


def _wait_ready(config: Config) -> bool:
    deadline = time.monotonic() + config.mcp_stdio_boot_timeout
    while time.monotonic() < deadline:
        if _backend_alive(config):
            return True
        time.sleep(_READY_POLL_SECONDS)
    return False


def _open_home(config: Config) -> None:
    if config.mcp_stdio_open_browser:
        webbrowser.open(_base_url(config) + "/")


def _ensure_backend(config: Config) -> None:
    """Backend жив → ничего. Иначе спавним, ждём готовности и открываем браузер."""
    if _backend_alive(config):
        _LOG.info("mcp-stdio: backend already up at %s", _base_url(config))
        return
    _spawn_backend(config)
    if not _wait_ready(config):
        raise RuntimeError(
            f"mcp-stdio: backend не поднялся за {config.mcp_stdio_boot_timeout}s "
            f"(см. {_backend_log_path(config)})"
        )
    _open_home(config)


def _build_proxy(config: Config, code: str):
    from fastmcp.client.transports import StreamableHttpTransport
    from fastmcp.server import create_proxy

    url = f"{_base_url(config)}/mcp/{code}"
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
