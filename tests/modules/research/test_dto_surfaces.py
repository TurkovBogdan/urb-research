"""Две поверхности контрактов research: агентская и интерфейсная.

Что видит агент, в этом модуле управляется жёстко, и граница проведена именем: класс с префиксом
``Agent`` возвращают тулы MCP и больше никто, всё остальное — контракты web-вьюера. Интерфейсная
деталь наследует агентскую и добавляет то, что нужно только человеку, — путь наверх.

Правило держится на договорённости, поэтому проверяется здесь: разъехавшись, оно протекает молча
— агент начинает получать поля, которых ему не показывали, и замечено это будет не сразу.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from src.modules.research import dto
from src.modules.research.codes import strip_prefix, tagged

pytestmark = pytest.mark.pure

RESEARCH_SRC = Path(dto.__file__).parent

# Путь наверх — поля страницы, а не артефакта: агент и так знает, в каком месте дерева работает.
WAY_UP_FIELDS = {"research_code", "research_title", "area_code", "area_title"}

# Интерфейсная деталь ← её агентская основа.
DETAIL_PAIRS = [
    (dto.AreaDetail, dto.AgentAreaDetail),
    (dto.NoteDetail, dto.AgentNoteDetail),
    (dto.ResearchSourceDocumentDetail, dto.AgentSourceDocumentDetail),
]


def _agent_models() -> list[tuple[str, type[BaseModel]]]:
    found = []
    for name in dir(dto):
        value = getattr(dto, name)
        if name.startswith("Agent") and isinstance(value, type) and issubclass(value, BaseModel):
            found.append((name, value))
    return found


def test_agent_contracts_are_found():
    """Сам обход: перестань классы находиться, и правило ниже стало бы молчаливо зелёным."""
    assert len(_agent_models()) > 10


@pytest.mark.parametrize("name,model", _agent_models(), ids=lambda v: v if isinstance(v, str) else "")
def test_agent_contract_hides_the_way_up(name: str, model: type[BaseModel]):
    leaked = WAY_UP_FIELDS & set(model.model_fields)
    assert not leaked, f"{name}: агентский контракт отдаёт поля страницы {sorted(leaked)}"


@pytest.mark.parametrize("web,agent", DETAIL_PAIRS, ids=lambda v: getattr(v, "__name__", ""))
def test_web_detail_is_the_agent_one_plus_the_way_up(web: type[BaseModel], agent: type[BaseModel]):
    """Интерфейс получает всё, что и агент: наследование, а не второй набор полей, который
    разъедется с первым при первой же правке."""
    added = set(web.model_fields) - set(agent.model_fields)

    assert set(agent.model_fields) <= set(web.model_fields)
    assert added <= WAY_UP_FIELDS, f"{web.__name__}: сверх агентского набора лишнее {sorted(added - WAY_UP_FIELDS)}"
    assert added, f"{web.__name__}: наследник ничего не добавил — тогда и разделять было нечего"


def test_http_api_takes_no_agent_contract():
    """Обратная половина правила: интерфейс не отдаёт человеку суженный под агента набор — на
    странице тогда не хватало бы ровно того, ради чего поверхности и разводили."""
    source = (RESEARCH_SRC / "api.py").read_text(encoding="utf-8")

    assert not re.findall(r"\bAgent[A-Z]\w+", source)


def test_mcp_tools_take_no_web_contract():
    """И прямая: тул MCP не возвращает интерфейсную деталь — вместе с ней утёк бы путь наверх."""
    web_details = {pair[0].__name__ for pair in DETAIL_PAIRS}

    for path in sorted((RESEARCH_SRC / "mcp").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for name in web_details:
            assert not re.search(rf"(?<![A-Za-z]){name}\b", source), f"{path.name}: {name}"


def test_tagged_and_strip_prefix_are_inverse():
    """``tagged`` — вторая половина ``strip_prefix``: коды родителей попадают в резолвер ссылок
    уже в презентационной форме, и собирать её конкатенацией по месту нельзя."""
    bare = "0123456789abcdef012345"

    assert tagged("AREA", bare) == f"AREA@{bare}"
    assert strip_prefix(tagged("AREA", bare)) == bare
    assert tagged("AREA", None) is None
