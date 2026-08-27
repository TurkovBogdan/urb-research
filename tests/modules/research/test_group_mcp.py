"""research MCP: group_create / group_list / group_get / group_update / group_delete."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.crud import group as group_crud

pytestmark = pytest.mark.db

_MISSING = "GROUP@" + "0" * 22


async def test_create_returns_only_tagged_code(call):
    created = await call("group_create", title="Фронтенд")

    assert list(created.keys()) == ["code"]
    assert created["code"].startswith("GROUP@")


async def test_create_defaults_are_visible_in_get(call):
    code = (await call("group_create", title="G"))["code"]

    row = await call("group_get", group_code=code)

    assert row["description"] == ""


async def test_get_accepts_the_tagged_code_it_returned(call):
    code = (await call("group_create", title="G"))["code"]

    row = await call("group_get", group_code=code)

    assert row["code"] == code
    assert row["title"] == "G"


async def test_list_is_in_display_order(call):
    """Порядок задан человеком (``sort``) — агент его не выставляет, но видит список в нём."""
    await group_crud.group_create(title="Бета", sort=100)
    await group_crud.group_create(title="Альфа", sort=900)

    rows = await call("group_list")

    assert [r["title"] for r in rows["result"]] == ["Альфа", "Бета"]
    assert all(r["code"].startswith("GROUP@") for r in rows["result"])


async def test_update_keeps_omitted_fields(call):
    code = (await call("group_create", title="Старое", description="что тут лежит"))["code"]

    row = await call("group_update", group_code=code, title="Новое")

    assert row["title"] == "Новое" and row["description"] == "что тут лежит"


async def test_delete_reports_whether_it_existed(call):
    code = (await call("group_create", title="G"))["code"]

    assert (await call("group_delete", group_code=code))["result"] is True
    assert (await call("group_delete", group_code=code))["result"] is False


async def test_get_missing_raises(call):
    with pytest.raises(ToolError, match="Group .* not found"):
        await call("group_get", group_code=_MISSING)


async def test_update_missing_raises(call):
    with pytest.raises(ToolError, match="Group .* not found"):
        await call("group_update", group_code=_MISSING, title="X")


async def test_group_tools_are_registered(mcp):
    names = {tool.name for tool in await mcp.list_tools()}

    assert {
        "group_create",
        "group_list",
        "group_get",
        "group_update",
        "group_delete",
    } <= names
    assert "group_icons" not in names


async def test_the_agent_never_sees_how_the_shelf_looks_or_where_it_sits(mcp, call):
    """Вид и позиция полки — дело человека: ни аргумента, ни поля в ответе, ни тула палитры."""
    presentation = ("icon", "sort")
    group_tools = [t for t in await mcp.list_tools() if t.name.startswith("group_")]
    assert group_tools
    for tool in group_tools:
        assert not set(presentation) & set(tool.inputSchema["properties"])

    code = (await call("group_create", title="G"))["code"]
    responses = [
        await call("group_get", group_code=code),
        await call("group_update", group_code=code, title="G2"),
        (await call("group_list"))["result"][0],
    ]

    for row in responses:
        assert not set(presentation) & set(row)


async def test_research_create_files_into_group(call):
    group = (await call("group_create", title="Экология"))["code"]

    research = (await call("research_create", title="Парки", group_code=group))["code"]

    view = await call("research_get", research_code=research)
    assert view["group_code"] == group
    assert view["group_name"] == "Экология"


async def test_research_without_group_reports_empty_pair(call):
    research = (await call("research_create", title="Сам по себе"))["code"]

    view = await call("research_get", research_code=research)

    assert view["group_code"] is None and view["group_name"] == ""


async def test_group_name_follows_a_rename(call):
    """Имя вычисляется join'ом, а не копируется — переименование полки видно сразу."""
    group = (await call("group_create", title="Старое имя"))["code"]
    research = (await call("research_create", title="R", group_code=group))["code"]

    await call("group_update", group_code=group, title="Новое имя")

    view = await call("research_get", research_code=research)
    assert view["group_name"] == "Новое имя"


async def test_research_update_moves_between_groups(call):
    first = (await call("group_create", title="Первая"))["code"]
    second = (await call("group_create", title="Вторая"))["code"]
    research = (await call("research_create", title="R", group_code=first))["code"]

    scan = await call("research_update", research_code=research, group_code=second)

    assert scan["group_code"] == second and scan["group_name"] == "Вторая"


async def test_research_update_empty_group_code_unshelves(call):
    group = (await call("group_create", title="Полка"))["code"]
    research = (await call("research_create", title="R", group_code=group))["code"]

    scan = await call("research_update", research_code=research, group_code="")

    assert scan["group_code"] is None and scan["group_name"] == ""


async def test_research_update_keeps_group_when_omitted(call):
    group = (await call("group_create", title="Полка"))["code"]
    research = (await call("research_create", title="R", group_code=group))["code"]

    scan = await call("research_update", research_code=research, title="R2")

    assert scan["group_code"] == group and scan["group_name"] == "Полка"


async def test_research_list_reports_the_group(call):
    group = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="R", group_code=group)

    row = (await call("research_list"))["result"][0]

    assert (row["group_code"], row["group_name"]) == (group, "Полка")


async def test_research_create_with_unknown_group_raises(call):
    with pytest.raises(ToolError, match="Group .* not found"):
        await call("research_create", title="R", group_code=_MISSING)


async def test_research_update_with_unknown_group_raises(call):
    research = (await call("research_create", title="R"))["code"]

    with pytest.raises(ToolError, match="Group .* not found"):
        await call("research_update", research_code=research, group_code=_MISSING)


async def test_deleting_a_group_unshelves_its_researches(call):
    group = (await call("group_create", title="Полка"))["code"]
    research = (await call("research_create", title="R", group_code=group))["code"]

    await call("group_delete", group_code=group)

    view = await call("research_get", research_code=research)
    assert view["group_code"] is None and view["group_name"] == ""
    assert view["title"] == "R"
