"""``GET /connectors`` — паспорта зарегистрированных коннекторов и справочник их групп.

Что вообще можно настроить в этой установке: код сервиса, имя, группа, владелец регистрации,
умеет ли баланс и из каких полей состоит доступ. Значений и балансов тут нет — они
принадлежат записям (``/accesses``). Реестр читается лениво, в момент запроса: чужой
модуль мог зарегистрировать свой коннектор уже после сборки.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.modules.core_connectors import service
from src.modules.core_connectors.connectors.groups import ConnectorGroup
from src.modules.core_connectors.connectors.passport import ConnectorPassport

router = APIRouter()


@router.get("/connectors", response_model=list[ConnectorPassport])
async def list_connectors() -> list[ConnectorPassport]:
    return service.passports()


@router.get("/connectors/groups", response_model=list[ConnectorGroup])
async def list_connector_groups() -> list[ConnectorGroup]:
    return service.connector_groups()
