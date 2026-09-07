"""core_interface: таблица настроек — пачка, сброс, время жизни строки."""

from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import select

from src.core.database import session_scope
from src.modules.core_interface import crud
from src.modules.core_interface.models import InterfaceSetting

pytestmark = pytest.mark.db


async def test_empty_table_reports_no_deviations(db):
    assert await crud.list_all() == {}


async def test_batch_applies_every_key(db):
    await crud.upsert_many({"interface_theme": "light", "interface_font_reading_size": 17})

    assert await crud.list_all() == {
        "interface_theme": "light",
        "interface_font_reading_size": 17,
    }


async def test_repeated_write_keeps_the_first_creation_time(db):
    await crud.upsert_many({"interface_theme": "light"})
    created_at = await _created_at("interface_theme")

    await crud.upsert_many({"interface_theme": "system"})

    assert await _created_at("interface_theme") == created_at
    assert (await crud.list_all())["interface_theme"] == "system"


async def test_delete_removes_the_deviation(db):
    await crud.upsert_many({"interface_theme": "light", "interface_font": "golos"})

    await crud.delete_many(["interface_theme"])

    assert await crud.list_all() == {"interface_font": "golos"}


async def test_prune_removes_keys_outside_the_registry(db):
    await crud.upsert_many({"interface_theme": "light", "app_message_mode": "html"})

    removed = await crud.prune_unknown(["interface_theme"])

    assert removed == 1
    assert await crud.list_all() == {"interface_theme": "light"}


async def test_delete_all_clears_the_table(db):
    await crud.upsert_many({"interface_theme": "light"})

    await crud.delete_all()

    assert await crud.list_all() == {}


async def _created_at(key: str) -> datetime:
    async with session_scope() as s:
        row = (
            await s.execute(select(InterfaceSetting).where(InterfaceSetting.key == key))
        ).scalar_one()
        return row.created_at
