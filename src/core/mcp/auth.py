"""Bearer-верификатор MCP-серверов — agnostic, без импорта auth-модуля.

Смонтированное ASGI-подприложение обходит FastAPI ``dependencies=[...]``, поэтому
auth живёт ВНУТРИ сервера через форковский ``TokenVerifier.verify_token`` — это
единственная точка, переживающая границу монтажа.

Резолвер ``(token, scope) -> принципал | None`` ИНЪЕЦИРУЕТСЯ (его поставляет
auth-модуль через ``Module.mcp_token_resolver``), ровно как guard'ы вливаются
через ``Module.guards``: ядро никогда не импортирует модуль. Этот файл —
backend-only (его тянет только ``mount_mcp_servers`` под ``server_enabled``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastmcp.server.auth import AccessToken, TokenVerifier

if TYPE_CHECKING:
    from src.core.mcp.context import TokenResolver

# Auth-scope токена (его определяет auth-модуль). Отличается от *зоны* роутера
# ``/mcp``: токен другого scope, предъявленный сюда, — бесплатный reject.
_MCP_SCOPE = "mcp"


class McpServerTokenVerifier(TokenVerifier):
    """Резолвит bearer-токен в MCP ``AccessToken`` через инъецированный резолвер.

    ``verify_token`` зовёт ``resolve(token, "mcp")`` (проверка, что токен типа
    ``mcp``) и мапит принципала в ``AccessToken(client_id=str(id), scopes=[group])``;
    ``None`` верификатора → 401 до инструментов.
    """

    def __init__(self, resolve: "TokenResolver") -> None:
        super().__init__()
        self._resolve = resolve

    async def verify_token(self, token: str) -> AccessToken | None:
        principal = await self._resolve(token, _MCP_SCOPE)
        if principal is None:
            return None
        return AccessToken(
            token=token,
            client_id=str(principal.id),
            scopes=[principal.group],
        )


__all__ = ["McpServerTokenVerifier"]
