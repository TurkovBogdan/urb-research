"""Зон-роутер модуля core_connectors (зона internal, без собственного префикса).

Две поверхности: ``/connectors`` — что бывает (паспорта), ``/accesses`` — чем мы
располагаем (записи, проверка, баланс). Модуль не задаёт ``internal_router_prefix``;
корень пути прописан в самих маршрутах под-роутеров.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.core_connectors.api.accesses import router as accesses_router
from src.modules.core_connectors.api.connectors import router as connectors_router

internal_router = APIRouter()
internal_router.include_router(connectors_router, tags=["connectors"])
internal_router.include_router(accesses_router, tags=["connectors"])

__all__ = ["internal_router"]
