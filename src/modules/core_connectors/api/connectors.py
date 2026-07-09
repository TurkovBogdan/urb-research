"""Раздел «Сервисы» — HTTP-эндпойнт коннекторов (паспорт + баланс).

Один маршрут ``GET /connectors``: паспорт каждого коннектора + баланс (снимается вживую у
включённых, умеющих его; сбой одного → ``error`` в его DTO). Корень ``/connectors`` прописан
в пути (агрегатор включает роутер без prefix). Зона internal в чистом ядре = ``allow_all``.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.core_connectors.registry import connectors_registry
from src.modules.core_connectors.services.dto import ConnectorView

router = APIRouter()


@router.get("/connectors", response_model=list[ConnectorView])
async def list_connectors() -> list[ConnectorView]:
    """Паспорт + баланс по всем коннекторам (баланс — вживую у включённых)."""
    return await connectors_registry.connectors(with_balance=True)
