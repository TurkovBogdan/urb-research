"""Сборка одного ``FastMCP``-сервера под ``McpServerContext``.

``make_mcp_server`` — единственная фабрика конструирования ``FastMCP``: модульный
``mcp_server(ctx)`` зовёт её, затем регистрирует свои инструменты
(``register(mcp)``). Все серверы получают общий ``auth`` (bearer) + ``audit``
(per-tool лог) даром. ``transport``/``allowed_hosts`` навешиваются позже, на
``http_app()`` в ``mount_mcp_servers`` (ASGI-слой).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp import FastMCP

if TYPE_CHECKING:
    from src.core.mcp.context import McpServerContext

_SERVER_VERSION = "0.1"


def make_mcp_server(
    code: str, instructions: str, ctx: "McpServerContext"
) -> FastMCP:
    """``FastMCP`` с именем ``code``, общими auth + audit из ``ctx``.

    ``name=code`` совпадает с URL-сегментом ``/mcp/<code>``; ``version`` форк 3.x
    принимает напрямую (workaround ``_mcp_server.version`` bundled-SDK не нужен).
    """
    return FastMCP(
        name=code,
        instructions=instructions,
        version=_SERVER_VERSION,
        auth=ctx.auth,
        middleware=[ctx.audit],
    )


__all__ = ["make_mcp_server"]
