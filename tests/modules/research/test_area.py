"""research MCP: area_create / areas_list / area_get / area_update / area_delete."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db


async def _research(call) -> str:
    return (await call("research_create", title="R"))["code"]


async def test_area_create_returns_only_code(call):
    r = await _research(call)
    a = await call("area_create", research_code=r, title="A", description="d")
    assert list(a.keys()) == ["code"]
    assert a["code"].startswith("AREA@")


async def test_area_create_stores_brief_shown_in_get(call):
    r = await _research(call)
    a = (await call(
        "area_create",
        research_code=r,
        title="A",
        objective="obj",
        scope="sc",
        expectations="ex",
    ))["code"]

    g = await call("area_get", area_code=a)

    assert g["objective"] == "obj" and g["scope"] == "sc" and g["expectations"] == "ex"
    # порядок: бриф перед body, updated_at последним
    keys = list(g.keys())
    assert keys.index("expectations") < keys.index("body") < keys.index("updated_at")
    assert keys[-1] == "updated_at"


async def test_area_create_research_not_found(call):
    with pytest.raises(ToolError, match="Research .* not found"):
        await call("area_create", research_code="RESEARCH@missing000000000000", title="A")


async def test_areas_list_scan(call):
    r = await _research(call)
    await call("area_create", research_code=r, title="One")
    await call("area_create", research_code=r, title="Two")

    rows = (await call("areas_list", research_code=r))["result"]

    assert {x["title"] for x in rows} == {"One", "Two"}
    assert set(rows[0]) == {"code", "title", "description", "updated_at"}


async def test_areas_list_research_not_found(call):
    with pytest.raises(ToolError, match="Research .* not found"):
        await call("areas_list", research_code="RESEARCH@missing000000000000")


async def test_area_get_not_found(call):
    with pytest.raises(ToolError, match="Area .* not found"):
        await call("area_get", area_code="AREA@missing0000000000000")


async def test_area_update_fields(call):
    r = await _research(call)
    a = (await call("area_create", research_code=r, title="A"))["code"]
    await call("area_update", area_code=a, description="d2", objective="o2", body="# synth")
    g = await call("area_get", area_code=a)
    assert g["description"] == "d2" and g["objective"] == "o2" and g["body"] == "# synth"


async def test_area_update_not_found(call):
    with pytest.raises(ToolError, match="Area .* not found"):
        await call("area_update", area_code="AREA@missing0000000000000", title="z")


async def test_area_delete_true_then_gone(call):
    r = await _research(call)
    a = (await call("area_create", research_code=r, title="A"))["code"]
    assert (await call("area_delete", area_code=a))["result"] is True
    assert (await call("areas_list", research_code=r))["result"] == []


async def test_area_delete_missing_returns_false(call):
    assert (await call("area_delete", area_code="AREA@missing0000000000000"))["result"] is False
