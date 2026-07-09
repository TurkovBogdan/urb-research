"""Контекст MCP-сервера: общая обвязка, отдаваемая конструктору каждого модуля.

``McpServerContext`` строится ОДИН раз в ``mount_mcp_servers`` и передаётся в
каждый ``mcp_server(ctx)`` модуля. Несёт agnostic-верификатор (общий на все
серверы), audit-middleware и список ``allowed_hosts`` (защиту от DNS-rebinding
навешивает ASGI-слой через ``TrustedHostMiddleware`` в момент ``http_app()`` —
форк ``fastmcp`` 3.x не имеет ``TransportSecuritySettings`` bundled-SDK).

Типы ``TokenResolver`` / ``McpServerBuilder`` объявлены здесь (leaf-модуль без
импорта ``fastmcp`` на верхнем уровне), чтобы ``core/module.py`` мог типизировать
``Module.mcp_servers`` / ``Module.mcp_token_resolver`` без тяги +13 МБ.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from fastmcp.server.auth import TokenVerifier
    from fastmcp.server.middleware import Middleware


class McpPrincipal(Protocol):
    """Утиный тип принципала, возвращаемого резолвером токена.

    Совпадает с принципалом auth-модуля по используемым полям —
    ядро его НЕ импортирует, читает только ``id``/``group``.
    """

    id: int
    group: str


# Резолвер токена: (token, scope) -> принципал | None. Поставляет auth-модуль
# через ``Module.mcp_token_resolver``.
TokenResolver = Callable[[str, str], Awaitable["McpPrincipal | None"]]

# Конструктор MCP-сервера: ``(ctx) -> FastMCP``. В модуле ВСЕГДА именуется
# ``mcp_server`` и кладётся в ``Module.mcp_servers`` под ключом-``code``.
McpServerBuilder = Callable[["McpServerContext"], "FastMCP"]


@dataclass(frozen=True)
class McpServerContext:
    """Общая обвязка, передаваемая конструктору каждого MCP-сервера."""

    auth: "TokenVerifier"
    audit: "Middleware"
    allowed_hosts: list[str] = field(default_factory=list)


__all__ = [
    "McpPrincipal",
    "McpServerBuilder",
    "McpServerContext",
    "TokenResolver",
]
