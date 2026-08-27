"""research CRUD: group_create / group_get / group_list / group_update / group_delete."""

from __future__ import annotations

import pytest
from sqlalchemy import update

from src.core.database import session_scope
from src.modules.research.constants import (
    GROUP_COLOR_MAX,
    GROUP_DESCRIPTION_MAX,
    GROUP_ICON_MAX,
    GROUP_SORT_DEFAULT,
    GROUP_TITLE_MAX,
)
from src.modules.research.crud.group import (
    group_create,
    group_delete,
    group_get,
    group_list,
    group_update,
)
from src.modules.research.crud.research import research_create, research_get
from src.modules.research.models.research import Research

pytestmark = pytest.mark.db


async def _attach(research_code: str, group_code: str) -> None:
    """Привязать исследование к группе напрямую — ``crud/research.py`` про группы ещё не знает."""
    async with session_scope() as s:
        await s.execute(
            update(Research)
            .where(Research.code == research_code)
            .values(group_code=group_code)
        )


async def test_create_fills_defaults(db):
    row = await group_create(title="Фронтенд")

    assert len(row.code) == 22
    assert row.title == "Фронтенд"
    assert row.description == "" and row.icon == "" and row.color == ""
    assert row.sort == GROUP_SORT_DEFAULT


async def test_create_stores_look_and_sort(db):
    row = await group_create(
        title="Инфра", description="d", icon="server", color="blue", sort=900
    )

    stored = await group_get(row.code)
    assert (stored.description, stored.icon, stored.color, stored.sort) == (
        "d",
        "server",
        "blue",
        900,
    )


async def test_create_codes_are_unique(db):
    first = await group_create(title="A")
    second = await group_create(title="A")

    assert first.code != second.code


async def test_get_missing_returns_none(db):
    assert await group_get("0" * 22) is None


async def test_list_orders_by_sort_desc_then_title(db):
    await group_create(title="Бета", sort=100)
    await group_create(title="Альфа", sort=900)
    await group_create(title="Аврора", sort=900)

    assert [row.title for row in await group_list()] == ["Аврора", "Альфа", "Бета"]


async def test_list_empty(db):
    assert await group_list() == []


async def test_update_changes_only_passed_fields(db):
    row = await group_create(
        title="Старое", description="описание", icon="folder", color="teal"
    )

    updated = await group_update(row.code, title="Новое")

    assert updated.title == "Новое"
    assert updated.description == "описание"
    assert (updated.icon, updated.color) == ("folder", "teal")


async def test_update_replaces_the_colour(db):
    row = await group_create(title="G", color="teal")

    updated = await group_update(row.code, color="rose")

    assert (await group_get(row.code)).color == "rose" == updated.color


async def test_update_clears_the_colour_with_an_empty_string(db):
    """``""`` — это «цвет снят», а не «не трогать»: снять его иначе было бы нечем."""
    row = await group_create(title="G", color="teal")

    updated = await group_update(row.code, color="")

    assert updated.color == ""


async def test_update_sort_zero_is_applied(db):
    """``0`` — валидная позиция: условие в CRUD проверяет ``is not None``, не truthiness."""
    row = await group_create(title="G", sort=900)

    updated = await group_update(row.code, sort=0)

    assert updated.sort == 0


async def test_update_missing_returns_none(db):
    assert await group_update("0" * 22, title="X") is None


async def test_long_fields_are_clipped_by_code_points(db):
    row = await group_create(
        title="я" * (GROUP_TITLE_MAX + 50),
        description="ю" * (GROUP_DESCRIPTION_MAX + 50),
        icon="i" * (GROUP_ICON_MAX + 50),
        color="c" * (GROUP_COLOR_MAX + 50),
    )

    assert len(row.title) == GROUP_TITLE_MAX and row.title[-1] == "я"
    assert len(row.description) == GROUP_DESCRIPTION_MAX
    assert len(row.icon) == GROUP_ICON_MAX
    assert len(row.color) == GROUP_COLOR_MAX


async def test_delete_detaches_researches_but_keeps_them(db):
    group = await group_create(title="Полка")
    research = await research_create(title="Иссл")
    await _attach(research.code, group.code)

    assert await group_delete(group.code) is True

    assert await group_get(group.code) is None
    kept = await research_get(research.code)
    assert kept is not None and kept.group_code is None


async def test_delete_leaves_other_groups_attached(db):
    doomed = await group_create(title="Удаляемая")
    kept_group = await group_create(title="Остаётся")
    research = await research_create(title="Иссл")
    await _attach(research.code, kept_group.code)

    await group_delete(doomed.code)

    assert (await research_get(research.code)).group_code == kept_group.code


async def test_delete_missing_returns_false(db):
    assert await group_delete("0" * 22) is False
