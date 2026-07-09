"""Зон-роутер модуля core_connectors (зона internal, без собственного префикса).

Поверхность — ``/connectors`` (список коннекторов с балансом). Модуль не задаёт
``internal_router_prefix``; корень пути прописан в самих маршрутах под-роутера.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.core_connectors.api.connectors import router as connectors_router

internal_router = APIRouter()
internal_router.include_router(connectors_router, tags=["connectors"])

__all__ = ["internal_router"]
