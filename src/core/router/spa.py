"""Раздача собранного SPA (``web/dist``) тем же HTTP-сервером, что и API-зоны.

Ядровый uvicorn — единственный веб-сервер; SPA это его штатная функция (не отдельный
сервер/процесс). ``mount_spa`` вешает middleware в build phase под ``SERVER_ENABLED``
(см. ``mount_router_zones``).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from src.core.app_path import project_root
from src.core.loggers import get_logger
from src.core.router.api import API_PREFIX
from src.core.router.internal import INTERNAL_PREFIX
from src.core.router.mcp import MCP_PREFIX
from src.core.router.storage import STORAGE_PREFIX
from src.core.router.webhook import WEBHOOK_PREFIX

_LOG = get_logger()

_API_PREFIXES = (API_PREFIX, INTERNAL_PREFIX, STORAGE_PREFIX, MCP_PREFIX, WEBHOOK_PREFIX)


def _is_api_path(path: str, prefixes: tuple[str, ...]) -> bool:
    """Путь принадлежит backend-зоне (точное совпадение префикса или сегмент под ним)."""
    return any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes)


class SpaStaticMiddleware:
    """Отдаёт встроенный фронт (``web/dist``) для любого GET/HEAD вне API-префиксов.

    Существующий файл из ``dist`` отдаётся как есть (ассеты, фавиконки); для всех
    прочих путей — ``index.html`` (deep-link клиентского роутинга). Запросы под
    API-префиксами проходят в backend без изменений — JSON-контракт ошибок не
    затрагивается. Middleware короткозамыкает раздачу до роутинга, поэтому порядок
    монтажа зон значения не имеет.
    """

    def __init__(
        self, app: ASGIApp, *, dist: Path, api_prefixes: tuple[str, ...]
    ) -> None:
        self._app = app
        self._dist = dist.resolve()
        self._index = self._dist / "index.html"
        self._api_prefixes = api_prefixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        is_browser_get = scope["type"] == "http" and scope["method"] in ("GET", "HEAD")
        if not is_browser_get or _is_api_path(scope["path"], self._api_prefixes):
            await self._app(scope, receive, send)
            return
        await self._spa_response(scope["path"])(scope, receive, send)

    def _spa_response(self, path: str) -> Response:
        relative = path.lstrip("/")
        if relative:
            candidate = (self._dist / relative).resolve()
            if candidate.is_file() and self._dist in candidate.parents:
                return FileResponse(candidate)
        return FileResponse(self._index)


def mount_spa(app: FastAPI) -> None:
    """Смонтировать раздачу фронта из ``web/dist``; нет сборки → WARNING + no-op."""
    dist = project_root() / "web" / "dist"
    if not (dist / "index.html").is_file():
        _LOG.warning(
            "spa: %s/index.html не найден — фронт не раздаётся; соберите "
            "(`pnpm --dir web build`)",
            dist,
        )
        return
    app.add_middleware(SpaStaticMiddleware, dist=dist, api_prefixes=_API_PREFIXES)
    _LOG.info("spa: фронт раздаётся из %s", dist)
