"""research MCP: резолвер bearer-токена (``mcp/auth.py``) — pure, без БД/fastmcp.

``Config`` в модуле подменяется заглушкой, чтобы ветки (пустой токен = allow-all,
заданный токен = сверка) были детерминированны и не зависели от ``.env`` / окружения.
"""

from __future__ import annotations

import pytest

from src.modules.research.mcp import auth

pytestmark = pytest.mark.pure


class _Cfg:
    def __init__(self, token: str) -> None:
        self.mcp_token = token


def _use_token(monkeypatch, token: str) -> None:
    monkeypatch.setattr(auth, "Config", lambda: _Cfg(token))


async def test_wrong_scope_rejected(monkeypatch):
    _use_token(monkeypatch, "secret")
    assert await auth.resolve_mcp_token("secret", "other") is None


async def test_empty_config_allows_all(monkeypatch):
    _use_token(monkeypatch, "")
    principal = await auth.resolve_mcp_token("", "mcp")
    assert principal is not None
    assert principal.id == 0 and principal.group == "research"


async def test_configured_token_matches(monkeypatch):
    _use_token(monkeypatch, "secret")
    principal = await auth.resolve_mcp_token("secret", "mcp")
    assert principal is not None and principal.group == "research"


async def test_configured_token_mismatch_rejected(monkeypatch):
    _use_token(monkeypatch, "secret")
    assert await auth.resolve_mcp_token("wrong", "mcp") is None
