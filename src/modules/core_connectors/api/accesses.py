"""``/accesses`` — записи доступа: список со статусом, форма, живая проверка и баланс.

Секрет не уходит наружу ни одним маршрутом: на чтение заданное значение подменяется
сентинелом ``NOT_CHANGED``, на запись сентинел (или пустая строка) значит «не менять».
Очистка выражается явным списком ``clear`` — у записи доступа нет «сброса к умолчанию»,
которым это делается на странице настроек, а пустая строка уже занята под «не трогал».

Живые вызовы (проверка, баланс) отдают диагноз **значением**: неготовая запись или
недоступный сервис — это ``error`` в DTO, а не пятисотка на всю страницу.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.api import ApiError
from src.core.router import guard
from src.modules.core_connectors import service
from src.modules.core_connectors.access.model import AccessDetail, AccessRow, AccessView
from src.modules.core_connectors.connectors.passport import ConnectorBalance, ConnectorCheck
from src.modules.core_connectors.errors import (
    AccessUndecryptable,
    ConnectorsError,
    UnknownConnector,
)

router = APIRouter()


# Длина совпадает с колонкой ``core_connectors_access.connector``: слишком длинное значение
# должно отвергаться проверкой формы, а не падать на вставке в Postgres (SQLite длину
# игнорирует, поэтому в dev дефект был бы не виден).
class CreateAccessBody(BaseModel):
    connector: str = Field(max_length=64)
    values: dict[str, str] = {}
    enabled: bool = True


class UpdateAccessBody(BaseModel):
    enabled: bool | None = None
    values: dict[str, str] = {}
    clear: list[str] = []


@router.get("/accesses", response_model=list[AccessView])
async def list_accesses(
    connector: str | None = None, with_balance: bool = False
) -> list[AccessView]:
    """Записи со статусом; ``with_balance`` снимает баланс вживую под общим дедлайном."""
    return await service.access_views(connector=connector, with_balance=with_balance)


@router.get("/accesses/{access_id}", response_model=AccessDetail)
async def get_access(access_id: int) -> AccessDetail:
    detail = await service.access_detail(access_id)
    if detail is None:
        raise ApiError.not_found("Запись доступа не найдена")
    return detail


@router.post("/accesses", response_model=AccessRow, status_code=201)
@guard("allow_all")
async def create_access(body: CreateAccessBody) -> AccessRow:
    try:
        return await service.create_access(
            connector=body.connector, values=body.values, enabled=body.enabled
        )
    except UnknownConnector as exc:
        raise ApiError.bad_request(str(exc))
    except AccessUndecryptable as exc:
        raise ApiError.conflict(str(exc))


@router.put("/accesses/{access_id}", response_model=AccessRow)
@guard("allow_all")
async def update_access(access_id: int, body: UpdateAccessBody) -> AccessRow:
    try:
        row = await service.update_access(
            access_id, enabled=body.enabled, values=body.values, clear=body.clear
        )
    except AccessUndecryptable as exc:
        # Мастер-ключ пропал или сменился: сказать об этом прямо честнее, чем записать
        # значения открытым текстом рядом с шифрованными.
        raise ApiError.conflict(str(exc))
    if row is None:
        raise ApiError.not_found("Запись доступа не найдена")
    return row


@router.delete("/accesses/{access_id}", status_code=204)
@guard("allow_all")
async def delete_access(access_id: int) -> None:
    await service.delete_access(access_id)


@router.post("/accesses/{access_id}/check", response_model=ConnectorCheck)
@guard("allow_all")
async def check_access(access_id: int) -> ConnectorCheck:
    return await service.check_access(access_id)


@router.get("/accesses/{access_id}/balance", response_model=ConnectorBalance)
async def access_balance(access_id: int) -> ConnectorBalance:
    try:
        return await service.access_balance(access_id)
    except ConnectorsError as exc:
        return ConnectorBalance(service="", name="", error=str(exc))
