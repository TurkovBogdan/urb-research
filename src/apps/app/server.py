"""Сборка ``apps/app``: headless FastAPI-приложение (web API + раздача SPA).

Тот же ядровый HTTP-сервер отдаёт и API-зоны, и собранный фронт из ``web/dist``
(``core/router/spa.py``) — nginx/Docker не нужны. В dev фронт обычно крутит Vite
(HMR на исходниках); раздача из ``web/dist`` работает на собранном артефакте.
"""

from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

from src.apps.app.modules import build_modules
from src.core.app_factory import create_app
from src.core.app_path import AppPath, ensure_dirs
from src.core.config import Config
from src.core.loggers import set_logger_factory
from src.core.loggers.core_logger import CoreLogger


def _bootstrap_logger(config: Config) -> None:
    """Завести фабрику каналов: `logs/<channel>.log` с уровнем из config."""
    paths = AppPath.from_root()
    ensure_dirs(paths)

    def factory(channel: str) -> CoreLogger:
        return CoreLogger(
            logs_dir=paths.logs,
            file_name=channel,
            level=config.app_log_level,
        )

    set_logger_factory(factory)


config = Config()
_bootstrap_logger(config)

app = create_app(modules=build_modules(), config=config)

# Вся web-обвязка гейтится SERVER_ENABLED: при выключенном сервере процесс —
# «только worker» (фон/задачи), HTTP-поверхности (зоны, CORS, docs) нет вовсе.
if config.server_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=13410)
