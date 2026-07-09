"""Модуль ``research`` — оркестратор + реестр ресёрча.

Выставляет MCP-сервер ``research`` (исследования + области + поиски/источники + заметки +
body-редактор) как тонкий адаптер над CRUD. Схема (research_index → area → source_query →
source_document, + note) строится миграциями ``rem_*`` (портируемые типы — идут и на SQLite,
и на PG). Поиск (``research_source_query``) — только ссылки, тела у него нет; синтез пишется
в ``body`` исследования/области/заметки через body-редактор (``services/body.py``).
Резолвер MCP-токена — черновой, из ``mcp/auth.py`` (снимает блокер до auth-модуля).

``services/`` — пока только ``body.py`` (оркестрация пайплайна поиска ещё не выделена);
``api.py`` — read-вьюер.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from src.core.module import Module
from src.modules.research import models  # noqa: F401 — регистрирует модели в Base.metadata
from src.modules.research.api import router
from src.modules.research.mcp import mcp_server
from src.modules.research.mcp.auth import resolve_mcp_token

_HERE = Path(__file__).resolve().parent


class ResearchModule(Module):
    name: ClassVar[str] = "research"
    description: ClassVar[str] = "Реестр исследований, областей, документов и заметок; MCP-сервер research."
    migrations_dir = _HERE / "migrations" / "versions"
    internal_router = router
    internal_router_prefix = "/research"
    # Значение — функция-конструктор, не экземпляр → объявление не тянет fastmcp.
    mcp_servers = {"research": mcp_server}
    # Единственный резолвер MCP-токена (черновой, до auth-модуля) — иначе
    # mount_mcp_servers падает на _collect_resolver. staticmethod: иначе доступ
    # через экземпляр (m.mcp_token_resolver) связал бы функцию как метод и подставил
    # self первым аргументом (resolve_mcp_token(self, token, scope) → TypeError).
    mcp_token_resolver = staticmethod(resolve_mcp_token)


__all__ = ["ResearchModule"]
