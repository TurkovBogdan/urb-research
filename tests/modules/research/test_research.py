"""research MCP: research_create / get / list / update / delete — happy-path + ошибки."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db


async def test_research_create_returns_only_code(call):
    r = await call("research_create", title="T", description="d", body="b")
    assert list(r.keys()) == ["code"]
    assert r["code"].startswith("RESEARCH@")


async def test_research_get_fields_areas_notes_updated_at_last(call):
    code = (await call("research_create", title="Parks", description="d", body="# body"))["code"]
    await call("area_create", research_code=code, title="A1")
    await call("note_create", research_code=code, kind="idea", title="N1")

    g = await call("research_get", research_code=code)

    assert g["title"] == "Parks" and g["body"] == "# body"
    assert "created_at" not in g
    assert list(g.keys())[-1] == "updated_at"
    assert len(g["areas"]) == 1 and len(g["notes"]) == 1
    assert set(g["areas"][0]) == {"code", "title", "description", "updated_at"}


async def test_research_get_not_found(call):
    with pytest.raises(ToolError, match="Research .* not found"):
        await call("research_get", research_code="RESEARCH@missing000000000000")


async def test_research_list_lean(call):
    await call("research_create", title="First")
    await call("research_create", title="Second")

    items = (await call("research_list"))["result"]

    assert {x["title"] for x in items} == {"First", "Second"}
    assert set(items[0]) == {"code", "title", "description", "updated_at"}


async def test_research_update_returns_scan_without_dates(call):
    code = (await call("research_create", title="T"))["code"]
    r = await call("research_update", research_code=code, title="T2", description="d2")
    assert r == {"code": code, "title": "T2", "description": "d2"}


async def test_research_update_not_found(call):
    with pytest.raises(ToolError, match="not found"):
        await call("research_update", research_code="RESEARCH@missing000000000000", title="z")


async def test_research_delete_cascades(call):
    code = (await call("research_create", title="T"))["code"]
    area = (await call("area_create", research_code=code, title="A"))["code"]
    await call("note_create", research_code=code, kind="idea", title="N")

    assert (await call("research_delete", research_code=code))["result"] is True
    assert (await call("research_list"))["result"] == []
    with pytest.raises(ToolError, match="Area .* not found"):
        await call("area_get", area_code=area)


async def test_research_delete_missing_returns_false(call):
    assert (await call("research_delete", research_code="RESEARCH@missing000000000000"))["result"] is False
