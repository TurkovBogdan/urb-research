"""``/settings`` — значения настроек интерфейса, их схема, обновление и сброс.

Четыре маршрута под четыре сценария; ручки удаления нет — убрать настройку не
пользовательский сценарий, человек сбрасывает её к умолчанию.

Тело обновления проверяется **целиком** до первой записи: отказ несёт все виноватые ключи
разом, а полуприменённой пачки не бывает.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.core.api import ApiError
from src.modules.core_interface import crud, registry
from src.modules.core_interface.dto import (
    InterfaceSchemaOut,
    InterfaceSettingsOut,
    InterfaceSettingsPatch,
    InterfaceSettingsReset,
    SettingSchemaOut,
)

internal_router = APIRouter(tags=["interface"])


@internal_router.get("/settings", response_model=InterfaceSettingsOut)
async def get_settings(include_schema: bool = False) -> InterfaceSettingsOut:
    """Действующие значения всех полей; ``include_schema`` добавляет схему — запрос старта."""
    return await _settings_out(include_schema=include_schema)


@internal_router.get("/settings/schema", response_model=InterfaceSchemaOut)
async def get_schema() -> InterfaceSchemaOut:
    """Схема отдельно: она меняется только при выкладке, и клиент кеширует её у себя."""
    return InterfaceSchemaOut(fields=_schema())


@internal_router.patch("/settings", response_model=InterfaceSettingsOut)
async def patch_settings(body: InterfaceSettingsPatch) -> InterfaceSettingsOut:
    refusals = {
        key: reason
        for key, value in body.values.items()
        if (reason := registry.rejection(key, value)) is not None
    }
    if refusals:
        raise ApiError.validation("Настройки не приняты", fields=refusals)
    await crud.upsert_many(body.values)
    return await _settings_out()


@internal_router.post("/settings/reset", response_model=InterfaceSettingsOut)
async def reset_settings(body: InterfaceSettingsReset) -> InterfaceSettingsOut:
    """Снять переопределения перечисленных ключей — снова действует умолчание.

    Список обязателен: «сбросить всё» клиент выражает перечнем всех ключей, который знает
    из схемы. Молчаливое «пустой список = стереть всё» было бы слишком лёгким способом
    снести настройки целиком.
    """
    unknown = registry.unknown_keys(body.keys)
    if unknown:
        raise ApiError.validation(
            "Настройки не приняты", fields={key: "неизвестная настройка" for key in unknown}
        )
    await crud.delete_many(body.keys)
    return await _settings_out()


async def _settings_out(*, include_schema: bool = False) -> InterfaceSettingsOut:
    values = registry.effective_values(await crud.list_all())
    return InterfaceSettingsOut(values=values, fields=_schema() if include_schema else None)


def _schema() -> list[SettingSchemaOut]:
    return [SettingSchemaOut(**field) for field in registry.schema()]


__all__ = ["internal_router"]
