"""research MCP: свободная работа с группами — устойчивость связки к произвольному порядку вызовов.

``test_group_mcp`` фиксирует контракт каждого тула по отдельности; здесь — сценарии, где группы
переживают чужие операции (правку тела, удаление исследования, переезд полки), и случаи, которые
ломаются только в связке (ungrouped-строки в списке, коды без префикса).
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.crud import group as group_crud

pytestmark = pytest.mark.db

_UNKNOWN_GROUP = "GROUP@" + "0" * 22


async def test_list_keeps_ungrouped_researches(call):
    """Join полки — внешний: неразложенное исследование обязано остаться в списке."""
    group = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="На полке", group_code=group)
    await call("research_create", title="Без полки")

    rows = (await call("research_list"))["result"]

    assert {row["title"] for row in rows} == {"На полке", "Без полки"}
    by_title = {row["title"]: row for row in rows}
    assert by_title["Без полки"]["group_code"] is None
    assert by_title["На полке"]["group_name"] == "Полка"


async def test_delete_unshelves_every_research_of_the_group(call):
    group = (await call("group_create", title="Полка"))["code"]
    codes = [
        (await call("research_create", title=f"R{i}", group_code=group))["code"]
        for i in range(3)
    ]

    await call("group_delete", group_code=group)

    for code in codes:
        assert (await call("research_get", research_code=code))["group_code"] is None


async def test_group_survives_deleting_a_research_it_holds(call):
    group = (await call("group_create", title="Полка"))["code"]
    doomed = (await call("research_create", title="R1", group_code=group))["code"]
    kept = (await call("research_create", title="R2", group_code=group))["code"]

    await call("research_delete", research_code=doomed)

    assert (await call("group_get", group_code=group))["title"] == "Полка"
    assert (await call("research_get", research_code=kept))["group_name"] == "Полка"


async def test_body_edit_keeps_the_research_on_its_shelf(call):
    group = (await call("group_create", title="Полка"))["code"]
    research = (await call("research_create", title="R", group_code=group, body="# Итог"))["code"]

    await call("body_add", code=research, text="\nещё абзац", position="end")

    view = await call("research_get", research_code=research)
    assert view["group_code"] == group and view["group_name"] == "Полка"
    assert view["body"].endswith("ещё абзац")


async def test_codes_work_with_and_without_the_type_tag(call):
    """``strip_prefix`` идемпотентен — голый код должен приниматься наравне с ``GROUP@``."""
    tagged = (await call("group_create", title="Полка"))["code"]
    bare = tagged.removeprefix("GROUP@")

    assert (await call("group_get", group_code=bare))["code"] == tagged

    research = (await call("research_create", title="R", group_code=bare))["code"]
    assert (await call("research_get", research_code=research))["group_code"] == tagged


async def test_the_users_icon_and_position_survive_an_mcp_update(call):
    """Вид и позицию ставит человек, а агент правит ту же строку — его правка их не стирает."""
    code = (await call("group_create", title="G"))["code"]
    bare = code.removeprefix("GROUP@")
    await group_crud.group_update(bare, icon="flask", sort=900)

    await call("group_update", group_code=code, title="G2", description="d")

    row = await group_crud.group_get(bare)
    assert (row.title, row.icon, row.sort) == ("G2", "flask", 900)


async def test_overlong_fields_are_trimmed_not_rejected(call):
    code = (await call("group_create", title="я" * 200, description="ю" * 600))["code"]

    row = await call("group_get", group_code=code)

    assert len(row["title"]) == 128 and len(row["description"]) == 512


async def test_reordering_shelves_in_the_interface_changes_the_agents_list(call):
    """Переставляет полки человек — агенту это видно тем, в каком порядке приходит список."""
    first = await group_crud.group_create(title="Первая", sort=900)
    second = await group_crud.group_create(title="Вторая", sort=100)
    tagged = [f"GROUP@{first.code}", f"GROUP@{second.code}"]

    assert [g["code"] for g in (await call("group_list"))["result"]] == tagged

    await group_crud.group_update(second.code, sort=1000)

    assert [g["code"] for g in (await call("group_list"))["result"]] == tagged[::-1]


async def test_research_pipeline_is_untouched_by_grouping(call, use_search):
    """Группа — раскладка, не часть пайплайна: области/поиски/источники работают как раньше."""
    use_search(
        results=[{"url": "https://ex.com/0", "rank": 0, "summary": "snip"}],
        pages={"https://ex.com/0": "# body"},
    )
    group = (await call("group_create", title="Экология"))["code"]
    research = (await call("research_create", title="Парки", group_code=group))["code"]
    area = (await call("area_create", research_code=research, title="Микроклимат"))["code"]

    sources = (await call("query_search_run", area_code=area, query="urban parks"))["result"]

    assert sources and all(s["status"] == "pending" for s in sources)
    view = await call("research_get", research_code=research)
    assert view["group_name"] == "Экология"
    assert [a["title"] for a in view["areas"]] == ["Микроклимат"]


async def test_free_form_session_stays_consistent(call):
    """Произвольная последовательность: создать, разложить, переименовать, переехать, снять, удалить."""
    science = (await call("group_create", title="Наука"))["code"]
    misc = (await call("group_create", title="Разное"))["code"]
    first = (await call("research_create", title="Парки", group_code=science))["code"]
    second = (await call("research_create", title="Черновик"))["code"]

    await call("group_update", group_code=science, title="Естественные науки")
    await call("research_update", research_code=second, group_code=misc)
    await call("research_update", research_code=first, group_code="")
    await call("group_delete", group_code=misc)

    rows = {row["title"]: row for row in (await call("research_list"))["result"]}
    assert rows["Парки"]["group_code"] is None
    assert rows["Черновик"]["group_code"] is None
    remaining = (await call("group_list"))["result"]
    assert [g["title"] for g in remaining] == ["Естественные науки"]

    await call("research_update", research_code=first, group_code=science)
    assert (await call("research_get", research_code=first))["group_name"] == "Естественные науки"


async def test_stale_group_code_is_rejected_after_the_shelf_is_gone(call):
    group = (await call("group_create", title="Полка"))["code"]
    await call("group_delete", group_code=group)
    research = (await call("research_create", title="R"))["code"]

    with pytest.raises(ToolError, match="Group .* not found"):
        await call("research_update", research_code=research, group_code=group)


async def test_list_filters_by_group(call):
    group = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="На полке", group_code=group)
    await call("research_create", title="Без полки")

    rows = (await call("research_list", group_code=group))["result"]

    assert [row["title"] for row in rows] == ["На полке"]


async def test_list_filters_the_ungrouped_with_an_empty_code(call):
    group = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="На полке", group_code=group)
    await call("research_create", title="Без полки")

    rows = (await call("research_list", group_code=""))["result"]

    assert [row["title"] for row in rows] == ["Без полки"]


async def test_list_without_the_filter_returns_everything(call):
    group = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="На полке", group_code=group)
    await call("research_create", title="Без полки")

    rows = (await call("research_list"))["result"]

    assert {row["title"] for row in rows} == {"На полке", "Без полки"}


async def test_list_filter_accepts_a_bare_group_code(call):
    tagged = (await call("group_create", title="Полка"))["code"]
    await call("research_create", title="На полке", group_code=tagged)

    rows = (await call("research_list", group_code=tagged.removeprefix("GROUP@")))["result"]

    assert [row["title"] for row in rows] == ["На полке"]


async def test_list_filter_with_unknown_group_raises(call):
    with pytest.raises(ToolError, match="Group .* not found"):
        await call("research_list", group_code=_UNKNOWN_GROUP)


async def test_list_filter_of_an_empty_shelf_is_empty(call):
    group = (await call("group_create", title="Пустая"))["code"]
    await call("research_create", title="Без полки")

    assert (await call("research_list", group_code=group))["result"] == []
