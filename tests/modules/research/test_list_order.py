"""research MCP: обещанный порядок каждого списка — против фикстуры, которая ловит разворот.

Каждый список-тул обещает порядок словами: области и заметки — «oldest first», исследования —
«most recently updated first», источники — «in search-launch order», группы — «в порядке, который
выставил человек». Порядок тут не украшение: по нему агент читает план области и решает, что уже
сделано, а по списку источников — в каком порядке их разбирать.

Порядок строится на времени, а время в проекте секундное (``utc_now`` рубит микросекунды), и
тайбрейком стоит **случайный** код сущности. Поэтому тесты разведены на два вида: с разным
временем (порядок держится) и с одинаковым, то есть внутри одной секунды (порядок разворачивается
— это дефект, тесты оставлены красными).

Чтобы краснота была воспроизводимой, а не монеткой, генератор кодов в этих тестах выдаёт коды
**по убыванию**: в проде он случаен, и каждая соседняя пара ложится не туда с вероятностью 1/2.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from src.core.database import write_scope
from src.core.utils.date import utc_now
from src.modules.research.crud import area as area_crud
from src.modules.research.crud import group as group_crud
from src.modules.research.crud import note as note_crud
from src.modules.research.crud import research as research_crud
from src.modules.research.crud import source_document as source_document_crud
from src.modules.research.crud import source_query as source_query_crud
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research

pytestmark = pytest.mark.db


@pytest.fixture
def descending_codes(monkeypatch):
    """Заставить выбранный CRUD выдавать коды по убыванию — тайбрейк становится предсказуемым."""

    def _install(module, attr: str) -> None:
        letters = iter("fedcba")
        monkeypatch.setattr(module, attr, lambda: next(letters) * 10)

    return _install


async def _backdate(model, code: str, seconds: int) -> None:
    """Отодвинуть ``created_at``/``updated_at`` строки в прошлое — разные секунды без ожидания."""
    async with write_scope() as s:
        row = await s.get(model, code)
        row.created_at = utc_now() - timedelta(seconds=seconds)
        row.updated_at = row.created_at


async def _research(call, title: str = "R") -> str:
    return (await call("research_create", title=title))["code"]


# ── порядок держится, когда время разное ─────────────────────────────────────
async def test_areas_list_puts_the_older_area_first(call):
    research = await _research(call)
    first = (await call("area_create", research_code=research, title="A1"))["code"]
    second = (await call("area_create", research_code=research, title="A2"))["code"]
    await _backdate(ResearchArea, first.removeprefix("AREA@"), seconds=60)

    rows = (await call("areas_list", research_code=research))["result"]

    assert [row["code"] for row in rows] == [first, second]


async def test_research_list_puts_the_freshly_updated_research_first(call):
    older = await _research(call, title="Older")
    newer = await _research(call, title="Newer")
    await _backdate(Research, older.removeprefix("RESEARCH@"), seconds=60)

    rows = (await call("research_list"))["result"]

    assert [row["title"] for row in rows] == ["Newer", "Older"]


async def test_research_list_moves_a_research_up_when_it_is_edited(call):
    """Смысл порядка: список отвечает на «где я работал последним», а правка — то, что этот
    ответ меняет."""
    first = await _research(call, title="First")
    second = await _research(call, title="Second")
    for code in (first, second):
        await _backdate(Research, code.removeprefix("RESEARCH@"), seconds=60)

    await call("research_update", research_code=first, description="тронули")

    assert [row["title"] for row in (await call("research_list"))["result"]] == ["First", "Second"]


async def test_group_list_breaks_a_tie_by_title(call):
    """У новых групп ``sort`` одинаковый, и тайбрейк тут не случайный, а алфавитный — список не
    перетасовывается от вызова к вызову."""
    for title in ("Ваня", "Аня", "Боря"):
        await call("group_create", title=title)

    rows = (await call("group_list"))["result"]

    assert [row["title"] for row in rows] == ["Аня", "Боря", "Ваня"]


async def test_group_list_puts_the_arrangement_above_the_alphabet(call):
    await group_crud.group_create(title="Аня", sort=100)
    await group_crud.group_create(title="Боря", sort=900)

    rows = (await call("group_list"))["result"]

    assert [row["title"] for row in rows] == ["Боря", "Аня"]


async def test_notes_list_keeps_its_order_under_a_kind_filter(call):
    research = await _research(call)
    old_idea = (await call("note_create", research_code=research, kind="idea", title="I1"))["code"]
    await call("note_create", research_code=research, kind="question", title="Q")
    new_idea = (await call("note_create", research_code=research, kind="idea", title="I2"))["code"]
    await _backdate(ResearchNote, old_idea.removeprefix("NOTE@"), seconds=60)

    rows = (await call("notes_list", research_code=research, kind="idea"))["result"]

    assert [row["code"] for row in rows] == [old_idea, new_idea]


# ── дефект: внутри одной секунды порядок разворачивается ─────────────────────
async def test_areas_list_is_oldest_first_within_one_second(call, descending_codes):
    """ДЕФЕКТ: «oldest first» не выполняется для областей, заведённых в одну секунду.

    ``created_at`` секундный, тайбрейк — случайный код, поэтому три области, созданные подряд
    (обычный сценарий: агент размечает план исследования одним заходом), приезжают в порядке
    своих кодов. Здесь коды убывают, и список выходит перевёрнутым целиком.
    """
    research = await _research(call)
    descending_codes(area_crud, "area_code")
    created = [
        (await call("area_create", research_code=research, title=title))["code"]
        for title in ("A1", "A2", "A3")
    ]

    rows = (await call("areas_list", research_code=research))["result"]

    assert [row["code"] for row in rows] == created


async def test_research_get_lists_areas_oldest_first_within_one_second(call, descending_codes):
    """ДЕФЕКТ, та же причина на другом туле: ``research_get`` обещает области «ordered by update
    time oldest first», а сортировка по равным датам устойчива и сохраняет порядок кодов."""
    research = await _research(call)
    descending_codes(area_crud, "area_code")
    created = [
        (await call("area_create", research_code=research, title=title))["code"]
        for title in ("A1", "A2", "A3")
    ]

    view = await call("research_get", research_code=research)

    assert [area["code"] for area in view["areas"]] == created


async def test_notes_list_is_oldest_first_within_one_second(call, descending_codes):
    """ДЕФЕКТ: то же и с заметками — рабочая память приезжает в порядке, обратном записанному."""
    research = await _research(call)
    descending_codes(note_crud, "note_code")
    created = [
        (await call("note_create", research_code=research, kind="idea", title=title))["code"]
        for title in ("N1", "N2", "N3")
    ]

    rows = (await call("notes_list", research_code=research))["result"]

    assert [row["code"] for row in rows] == created


async def test_research_list_is_newest_first_within_one_second(call, descending_codes):
    """ДЕФЕКТ: «most recently updated first» переворачивается на исследованиях, заведённых в одну
    секунду, — верхним оказывается не то, где работали последним."""
    descending_codes(research_crud, "research_code")
    created = [await _research(call, title=title) for title in ("R1", "R2", "R3")]

    rows = (await call("research_list"))["result"]

    assert [row["code"] for row in rows] == list(reversed(created))


async def test_sources_list_repeats_the_order_the_run_returned(call, use_search, descending_codes):
    """ДЕФЕКТ: «in search-launch order» не выполняется. Все источники одного прогона создаются в
    одну секунду, поэтому список отдаёт их в порядке кодов, а не по рангу выдачи — тот же набор
    в ``query_search_run`` и в ``sources_list`` приезжает в разном порядке, и агент, разбирающий
    источники по списку, идёт не с самого релевантного.
    """
    use_search(
        results=[{"url": f"https://ex.com/{i}", "rank": i, "summary": f"s{i}"} for i in range(3)],
        pages={f"https://ex.com/{i}": f"# b{i}" for i in range(3)},
    )
    research = await _research(call)
    area = (await call("area_create", research_code=research, title="A"))["code"]
    descending_codes(source_document_crud, "source_document_code")
    found = (await call("query_search_run", area_code=area, query="q"))["result"]

    listed = (await call("sources_list", code=area))["result"]

    assert [row["url"] for row in found] == ["https://ex.com/0", "https://ex.com/1", "https://ex.com/2"]
    assert [row["code"] for row in listed] == [row["code"] for row in found]


async def test_query_search_list_is_in_launch_order_within_one_second(
    call, use_search, descending_codes
):
    """ДЕФЕКТ: прогоны области тоже приезжают в порядке кодов — по списку не видно, каким
    запросом искали раньше, а каким позже."""
    use_search(results=[], pages={})
    research = await _research(call)
    area = (await call("area_create", research_code=research, title="A"))["code"]
    descending_codes(source_query_crud, "source_query_code")
    for query in ("первый", "второй", "третий"):
        await call("query_search_run", area_code=area, query=query)

    rows = (await call("query_search_list", code=area))["result"]

    assert [row["query"] for row in rows] == ["первый", "второй", "третий"]
