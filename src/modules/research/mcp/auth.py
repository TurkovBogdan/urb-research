"""Черновой резолвер MCP-токена — снимает блокер ``_collect_resolver``.

Пока нет auth-модуля, research сам поставляет единственный
``mcp_token_resolver``: сверяет предъявленный bearer со статичным токеном из
core-настроек ENV (``Config.mcp_token``). Пусто = локальный режим без проверки
(allow-all, dev). Будущий auth-модуль заберёт эту роль и токен-выдачу.

Не тянет fastmcp: только ``Config`` + dataclass. Тип принципала — утиный
(``id``/``group``), как ждёт ``McpServerTokenVerifier``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.config import Config

if TYPE_CHECKING:
    from src.core.mcp.context import McpPrincipal

_MCP_SCOPE = "mcp"


@dataclass(frozen=True)
class _StaticPrincipal:
    id: int = 0
    group: str = "research"


async def resolve_mcp_token(token: str, scope: str) -> "McpPrincipal | None":
    if scope != _MCP_SCOPE:
        return None
    configured = Config().mcp_token
    if not configured:
        return _StaticPrincipal()
    return _StaticPrincipal() if token == configured else None


__all__ = ["resolve_mcp_token"]
