"""research MCP: каталог навыков и чтение — через MCP-клиент + загрузчик напрямую."""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.services.skills import list_skills, read_skill

BODY_MARKUP = "body-markup"


@pytest.mark.pure
def test_catalogue_carries_description_and_sections_but_no_text():
    catalogue = {skill.name: skill for skill in list_skills()}
    body_markup = catalogue[BODY_MARKUP]
    assert body_markup.description
    assert set(body_markup.sections) == {"markdown", "references", "structure"}
    assert not hasattr(body_markup, "text")


@pytest.mark.pure
def test_read_skill_returns_guide_with_its_sections():
    guide = read_skill(BODY_MARKUP)
    assert guide.section == ""
    assert "references" in guide.sections
    assert guide.text.startswith("# Writing a body")


@pytest.mark.pure
def test_read_section_returns_that_file_and_keeps_the_section_list():
    section = read_skill(BODY_MARKUP, "references")
    assert section.section == "references"
    assert section.text.startswith("# References")
    assert "markdown" in section.sections


@pytest.mark.pure
def test_unknown_skill_names_the_available_ones():
    with pytest.raises(ValueError, match=f"Available skills: .*{BODY_MARKUP}.*mermaid"):
        read_skill("graphviz")


@pytest.mark.pure
def test_unknown_section_names_the_sections():
    with pytest.raises(ValueError, match="Sections: markdown, references, structure"):
        read_skill(BODY_MARKUP, "tables")


@pytest.mark.pure
def test_skill_name_cannot_escape_the_catalogue():
    with pytest.raises(ValueError, match="Unknown skill"):
        read_skill("../../services")


@pytest.mark.pure
def test_mermaid_skill_covers_every_renderable_type():
    mermaid = read_skill("mermaid")
    assert set(mermaid.sections) == {"chart", "class", "er", "flowchart", "sequence", "state"}
    assert "replace_block" in mermaid.text


@pytest.mark.db
async def test_skills_list_tool_lists_both_skills(call):
    catalogue = (await call("skills_list"))["result"]
    assert [skill["name"] for skill in catalogue] == [BODY_MARKUP, "mermaid"]
    assert all(skill["description"] for skill in catalogue)


@pytest.mark.db
async def test_skill_get_tool_returns_section_text(call):
    section = await call("skill_get", skill_name=BODY_MARKUP, section="structure")
    assert section["section"] == "structure"
    assert "Headings are the page outline" in section["text"]


@pytest.mark.db
async def test_skill_get_tool_rejects_unknown_skill(call):
    with pytest.raises(ToolError, match="Unknown skill"):
        await call("skill_get", skill_name="nope")


@pytest.mark.db
async def test_every_tool_that_writes_a_body_points_at_the_skills(mcp):
    """Указатель на справку обязан стоять там, где тело пишут, — иначе агент его не встретит."""
    writers = {
        tool.name: tool
        for tool in await mcp.list_tools()
        if "body" in (tool.inputSchema.get("properties") or {})
    }
    assert writers, "ни один тул не принимает body — тест потерял предмет"
    for name, tool in writers.items():
        hint = tool.inputSchema["properties"]["body"].get("description") or ""
        assert "skill_get('body-markup')" in hint, f"{name}: нет указателя на разметку"
        assert "skill_get('mermaid')" in hint, f"{name}: нет указателя на схемы"


@pytest.mark.db
async def test_body_editor_points_at_the_skills(mcp):
    editors = [tool for tool in await mcp.list_tools() if tool.name in ("body_add", "body_edit")]
    assert len(editors) == 2
    for tool in editors:
        assert "skill_get('body-markup')" in tool.description
        assert "skill_get('mermaid')" in tool.description
