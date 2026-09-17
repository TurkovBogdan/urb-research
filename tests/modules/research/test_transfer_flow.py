"""Перенос исследования: круг «экспорт → импорт», повтор, обрыв, коллизия кода, слияние страниц.

Данные засеиваются теми же тулами, какими их пишет агент, — иначе тест проверял бы не ту
цепочку, которая ездит вживую. Веб-поиск застаблен (``use_search``).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import delete, select

from src.core.database import session_scope, write_scope
from src.core.utils.date import utc_now
from src.modules.research.codes import strip_prefix
from src.modules.research.models.area import ResearchArea
from src.modules.research.models.group import ResearchGroup
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery
from src.modules.research.transfer.constants import (
    ACTION_CREATE,
    ACTION_MERGE,
    ACTION_SKIP,
    ENTITY_AREAS,
    ENTITY_NOTES,
    ENTITY_PAGES,
    ENTITY_RESEARCH,
    ENTITY_SEARCHES,
    ENTITY_SOURCES,
    ENTITY_SOURCE_QUERIES,
    IMPORT_MODE_ALWAYS,
    IMPORT_MODE_NEVER,
    IMPORT_MODE_NEWER,
)
from src.modules.research.transfer.export import export_research
from src.modules.research.transfer.runner import analyze_archive, import_archive
from src.modules.web_search.constants import FETCH_STATUS_DONE, FETCH_STATUS_PENDING
from src.modules.web_search.models.page import WebSearchPage
from src.modules.web_search.models.query import WebSearchQuery
from src.modules.web_search.models.query_result import WebSearchQueryResult

pytestmark = pytest.mark.db

_LONG_AGO = datetime(2020, 1, 1, 12, 0, 0)

_RESEARCH_TABLES = (
    ResearchSourceDocument,
    ResearchSourceQuery,
    ResearchNote,
    ResearchArea,
    Research,
    ResearchGroup,
)
_WEB_SEARCH_TABLES = (WebSearchQueryResult, WebSearchQuery, WebSearchPage)


async def _seed(call, use_search, *, pages: int = 2):
    """Полка + исследование с областью, заметкой, прогоном поиска и источниками.

    Тело исследования ссылается на область и заметку — ровно те ссылки, которые обязаны
    переехать при перевыпуске кода.
    """
    use_search(
        results=[
            {"url": f"https://ex.com/{i}", "rank": i, "summary": f"snip{i}"} for i in range(pages)
        ],
        pages={f"https://ex.com/{i}": f"# material {i}" for i in range(pages)},
    )
    group = (await call("group_create", title="Полка"))["code"]
    research = (await call("research_create", title="Тема", group_code=group))["code"]
    area = (await call("area_create", research_code=research, title="Область"))["code"]
    note = (await call("note_create", research_code=research, kind="result", title="Вывод"))["code"]
    await call("query_search_run", area_code=area, query="q")
    await call("body_set", code=research, text=f"Свод по {area} и по {note}.")
    await call("body_set", code=area, text=f"Раздел ссылается на {note}.")
    return {
        "group": strip_prefix(group),
        "research": strip_prefix(research),
        "area": strip_prefix(area),
        "note": strip_prefix(note),
    }


async def _archive(tmp_path, research_code: str, name: str = "archive.urch"):
    return await export_research(research_code, tmp_path / name)


async def _wipe(*, keep_pages: bool = False):
    """Опустошить базу, как будто архив приехал на чужую установку."""
    tables = _RESEARCH_TABLES + (() if keep_pages else _WEB_SEARCH_TABLES)
    async with write_scope() as s:
        for model in tables:
            await s.execute(delete(model))


def _stranger_research(code: str, title: str) -> Research:
    """Чужая запись под нужным кодом.

    Время создания задано заведомо старым не для красоты: тождество записи проверяется по
    секунде создания, а всё, что тест создаёт в одном прогоне, попадает в одну и ту же секунду —
    и «чужая» запись читалась бы как наша.
    """
    return Research(
        code=code,
        title=title,
        description="",
        body="",
        created_at=_LONG_AGO,
        updated_at=_LONG_AGO,
    )


async def _set_updated_at(code: str, moment: datetime) -> None:
    """Развести время правки с архивом: в одну и ту же секунду они неразличимы по построению."""
    async with write_scope() as s:
        await s.execute(
            Research.__table__.update().where(Research.code == code).values(updated_at=moment)
        )


async def _rows(model):
    async with session_scope() as s:
        return list((await s.execute(select(model))).scalars().all())


async def _count(model) -> int:
    return len(await _rows(model))


async def test_export_carries_the_whole_chain(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=3)

    archive = await _archive(tmp_path, codes["research"])

    counts = archive.manifest.counts
    assert counts[ENTITY_RESEARCH] == 1
    assert counts[ENTITY_AREAS] == 1
    assert counts[ENTITY_NOTES] == 1
    assert counts[ENTITY_SOURCES] == 3
    assert counts[ENTITY_PAGES] == 3
    assert archive.manifest.roots[0].code == codes["research"]
    assert archive.file_name == "Тема.urch"


async def test_import_into_an_empty_base_restores_the_research(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=2)
    before = {
        "research": await _rows(Research),
        "areas": await _rows(ResearchArea),
        "sources": await _rows(ResearchSourceDocument),
    }
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_RESEARCH]["created"] == 1
    restored = (await _rows(Research))[0]
    assert restored.code == before["research"][0].code
    assert restored.title == before["research"][0].title
    assert restored.body == before["research"][0].body
    assert restored.group_code == codes["group"]
    assert await _count(ResearchArea) == len(before["areas"])
    assert await _count(ResearchSourceDocument) == len(before["sources"])
    assert await _count(WebSearchPage) == 2
    assert {page.status for page in await _rows(WebSearchPage)} == {FETCH_STATUS_DONE}
    assert (await _rows(WebSearchPage))[0].body.startswith("# material")


async def test_importing_the_same_archive_twice_changes_nothing(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()
    await import_archive(archive.path, mode=IMPORT_MODE_NEWER)
    counts_before = {model.__name__: await _count(model) for model in _RESEARCH_TABLES}

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_RESEARCH]["created"] == 0
    assert report.counts[ENTITY_SOURCES]["created"] == 0
    assert plan.counts()[ENTITY_RESEARCH][ACTION_SKIP] == 1
    assert {model.__name__: await _count(model) for model in _RESEARCH_TABLES} == counts_before


async def test_import_into_its_own_base_recognises_every_record(call, use_search, tmp_path):
    """Архив, поданный в ту же базу, из которой снят, — это «восстановить», а не «скопировать»."""
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert plan.same_install is True
    assert report.counts[ENTITY_RESEARCH]["created"] == 0
    assert await _count(Research) == 1
    assert await _count(ResearchArea) == 1


async def test_interrupted_import_resumes_without_duplicates(
    call, use_search, tmp_path, monkeypatch
):
    """Обрыв на середине лечится повторным запуском того же файла, а не ручной чисткой."""
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    from src.modules.research.crud import transfer as transfer_crud

    honest_insert = transfer_crud.insert_rows

    async def insert_until_notes(model, rows):
        if model is ResearchNote:
            raise RuntimeError("обрыв посреди импорта")
        return await honest_insert(model, rows)

    monkeypatch.setattr(transfer_crud, "insert_rows", insert_until_notes)
    with pytest.raises(RuntimeError):
        await import_archive(archive.path, mode=IMPORT_MODE_NEWER)
    assert await _count(Research) == 1
    assert await _count(ResearchNote) == 0

    monkeypatch.setattr(transfer_crud, "insert_rows", honest_insert)
    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_RESEARCH]["created"] == 0
    assert report.counts[ENTITY_NOTES]["created"] == 1
    assert await _count(Research) == 1
    assert await _count(ResearchArea) == 1
    assert await _count(ResearchNote) == 1
    assert await _count(ResearchSourceDocument) == 2


async def test_code_collision_recodes_and_moves_the_references(call, use_search, tmp_path):
    """Коллизия вживую не встретится (≈1 на 50 000 импортов) — поэтому она навязана тестом."""
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    async with write_scope() as s:
        s.add(_stranger_research(codes["research"], "Чужое исследование"))

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert plan.counts()[ENTITY_RESEARCH]["recode"] == 1
    assert report.counts[ENTITY_RESEARCH]["created"] == 1
    researches = {row.code: row for row in await _rows(Research)}
    assert len(researches) == 2
    assert researches[codes["research"]].title == "Чужое исследование"

    imported = next(row for code, row in researches.items() if code != codes["research"])
    area = (await _rows(ResearchArea))[0]
    note = (await _rows(ResearchNote))[0]
    assert area.research_code == imported.code
    assert f"AREA@{area.code}" in imported.body
    assert f"NOTE@{note.code}" in imported.body
    assert report.refs_rewritten == 0  # коды детей свободны — переехал только корень


async def test_area_code_collision_rewrites_the_body_reference(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    async with write_scope() as s:
        s.add(_stranger_research("ffffffffff", "Чужое исследование"))
    async with write_scope() as s:
        s.add(
            ResearchArea(
                code=codes["area"],
                research_code="ffffffffff",
                title="Чужая область",
                created_at=_LONG_AGO,
                updated_at=_LONG_AGO,
            )
        )

    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    imported_area = next(row for row in await _rows(ResearchArea) if row.title == "Область")
    research = next(row for row in await _rows(Research) if row.title == "Тема")
    assert imported_area.code != codes["area"]
    assert f"AREA@{imported_area.code}" in research.body
    assert f"AREA@{codes['area']}" not in research.body
    assert report.refs_rewritten >= 1


async def test_a_collision_on_the_search_layer_recodes_the_whole_branch(
    call, use_search, tmp_path
):
    """Столкновение кодов прогона, источникового запроса и источника разом.

    Эти три ветки перевыпуска в бою срабатывают реже всех, поэтому тест навязывает их
    искусственно: иначе самый редкий путь остаётся единственным непроверенным.
    """
    codes = await _seed(call, use_search, pages=2)
    async with session_scope() as s:
        archived = (await s.execute(select(ResearchSourceQuery))).scalars().all()
        source_query_code = archived[0].code
        search_code = archived[0].search_code
        source_code = (await s.execute(select(ResearchSourceDocument))).scalars().first().code

    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    async with write_scope() as s:
        s.add(_stranger_research("ffffffffff", "Чужое исследование"))
        s.add(
            WebSearchQuery(
                code=search_code,
                search_engine="other",
                fetch_engine="other",
                status="done",
                query="чужой запрос",
                created_at=_LONG_AGO,
                updated_at=_LONG_AGO,
            )
        )
    async with write_scope() as s:
        s.add(
            ResearchArea(
                code="eeeeeeeeee",
                research_code="ffffffffff",
                title="Чужая область",
                created_at=_LONG_AGO,
                updated_at=_LONG_AGO,
            )
        )
    async with write_scope() as s:
        s.add(
            ResearchSourceQuery(
                code=source_query_code,
                research_code="ffffffffff",
                area_code="eeeeeeeeee",
                search_code=search_code,
                query="чужой запрос",
                created_at=_LONG_AGO,
            )
        )
    async with write_scope() as s:
        s.add(
            ResearchSourceDocument(
                code=source_code,
                research_code="ffffffffff",
                area_code="eeeeeeeeee",
                query_code=source_query_code,
                page_code="0" * 22,
                status="pending",
                created_at=_LONG_AGO,
                updated_at=_LONG_AGO,
            )
        )

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert plan.counts()[ENTITY_SEARCHES]["recode"] == 1
    assert plan.counts()[ENTITY_SOURCE_QUERIES]["recode"] == 1
    # Чужая запись занимает код одного источника из двух — перевыпускается ровно он.
    assert plan.counts()[ENTITY_SOURCES]["recode"] == 1
    assert report.counts[ENTITY_SOURCES]["created"] == 2

    imported_research = next(row for row in await _rows(Research) if row.title == "Тема")
    imported_queries = [
        row for row in await _rows(ResearchSourceQuery)
        if row.research_code == imported_research.code
    ]
    imported_sources = [
        row for row in await _rows(ResearchSourceDocument)
        if row.research_code == imported_research.code
    ]
    searches = {row.code: row for row in await _rows(WebSearchQuery)}

    assert len(imported_queries) == 1
    assert imported_queries[0].code != source_query_code
    assert imported_queries[0].search_code != search_code
    assert searches[imported_queries[0].search_code].query == "q"
    assert searches[search_code].query == "чужой запрос"
    assert {row.query_code for row in imported_sources} == {imported_queries[0].code}
    assert len(imported_sources) == 2


async def test_a_research_without_a_group_travels_alone(call, use_search, tmp_path):
    """Полка необязательна: у неразложенного исследования ссылке на группу неоткуда взяться."""
    use_search(results=[], pages={})
    research = (await call("research_create", title="Без полки"))["code"]

    archive = await _archive(tmp_path, strip_prefix(research), name="lonely.urch")
    await _wipe()
    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_RESEARCH]["created"] == 1
    assert await _count(ResearchGroup) == 0
    assert (await _rows(Research))[0].group_code is None


async def test_page_material_fills_an_empty_page_and_spares_a_live_one(
    call, use_search, tmp_path
):
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe(keep_pages=True)

    pages = sorted(await _rows(WebSearchPage), key=lambda row: row.url)
    async with write_scope() as s:
        await s.execute(
            WebSearchPage.__table__.update()
            .where(WebSearchPage.code == pages[0].code)
            .values(status=FETCH_STATUS_PENDING, body=None, body_hash=None)
        )
        await s.execute(
            WebSearchPage.__table__.update()
            .where(WebSearchPage.code == pages[1].code)
            .values(body="местный материал", body_hash="local")
        )

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    merged = {page.code: page for page in await _rows(WebSearchPage)}
    assert plan.counts()[ENTITY_PAGES][ACTION_MERGE] == 1
    assert plan.counts()[ENTITY_PAGES][ACTION_SKIP] == 1
    assert report.counts[ENTITY_PAGES]["created"] == 0
    assert merged[pages[0].code].status == FETCH_STATUS_DONE
    assert merged[pages[0].code].body.startswith("# material")
    assert merged[pages[1].code].body == "местный материал"
    assert plan.warnings.diverged_pages[0]["code"] == pages[1].code


async def test_page_code_that_points_elsewhere_is_refused(call, use_search, tmp_path):
    """Код страницы — хеш url; тот же код при другом адресе означает подделанный архив."""
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe(keep_pages=True)

    async with write_scope() as s:
        await s.execute(
            WebSearchPage.__table__.update().values(url="https://another.example/")
        )

    from src.modules.research.transfer.errors import ArchiveError

    with pytest.raises(ArchiveError):
        await analyze_archive(archive.path, mode=IMPORT_MODE_NEWER)


async def test_mode_never_leaves_an_existing_record_alone(call, use_search, tmp_path):
    """Местная запись состарена намеренно: иначе режим «по времени правки» пропустил бы её сам,
    и тест был бы зелёным даже с выключённым режимом «не трогать» (мутант это и показал)."""
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])
    await call("body_set", code=f"RESEARCH@{codes['research']}", text="местная правка")
    await _set_updated_at(codes["research"], _LONG_AGO)

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEVER)

    assert plan.counts()[ENTITY_RESEARCH][ACTION_SKIP] == 1
    assert report.counts[ENTITY_RESEARCH]["updated"] == 0
    assert (await _rows(Research))[0].body == "местная правка"


async def test_mode_always_overwrites_a_newer_local_edit(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])
    await call("body_set", code=f"RESEARCH@{codes['research']}", text="местная правка")

    _, report = await import_archive(archive.path, mode=IMPORT_MODE_ALWAYS)

    assert report.counts[ENTITY_RESEARCH]["updated"] == 1
    assert (await _rows(Research))[0].body != "местная правка"


async def test_newer_mode_keeps_the_fresher_local_edit_and_says_so(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])
    await call("body_set", code=f"RESEARCH@{codes['research']}", text="местная правка")
    await _set_updated_at(codes["research"], utc_now() + timedelta(minutes=1))

    plan, _ = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert (await _rows(Research))[0].body == "местная правка"
    assert any(item["entity"] == ENTITY_RESEARCH for item in plan.warnings.locally_newer)


async def test_sources_survive_a_second_import_by_their_natural_key(call, use_search, tmp_path):
    """У источника естественный ключ есть в схеме — повтор обязан узнать его даже без кода."""
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()
    await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    async with write_scope() as s:
        await s.execute(
            ResearchSourceDocument.__table__.update().values(code="0000000000")
            .where(ResearchSourceDocument.code == (await _rows(ResearchSourceDocument))[0].code)
        )

    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_SOURCES]["created"] == 0
    assert await _count(ResearchSourceDocument) == 2


async def test_analyze_does_not_touch_the_base(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    plan = await analyze_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert plan.counts()[ENTITY_RESEARCH][ACTION_CREATE] == 1
    assert await _count(Research) == 0
    assert await _count(WebSearchPage) == 0


async def test_a_page_missing_from_the_archive_is_refused_before_any_write(
    call, use_search, tmp_path
):
    """Источник без своей страницы — не «источник без материала», а битая ссылка в базе."""
    codes = await _seed(call, use_search, pages=2)
    archive = await _archive(tmp_path, codes["research"])
    tampered = tmp_path / "tampered.urch"
    _rewrite_archive(archive.path, tampered, drop_first_row_of="rows/pages.jsonl")

    from src.modules.research.transfer.errors import ArchiveError

    await _wipe()
    with pytest.raises(ArchiveError):
        await analyze_archive(tampered, mode=IMPORT_MODE_NEWER)
    assert await _count(Research) == 0


async def test_unicode_line_separators_in_material_survive_the_round_trip(
    call, use_search, tmp_path
):
    """U+2028 и родня приезжают из веба живьём, а ``splitlines`` рвёт по ним строку JSON.

    Материал ниже содержит их **буквально** (U+2028 после «строка», U+0085 после «вторая») — в
    экранированном виде тест проверял бы не то: в архив они уходят такими же непечатаемыми.
    Дефект был найден вживую на выгрузке настоящего исследования, а не выдуман.
    """
    use_search(
        results=[{"url": "https://ex.com/0", "rank": 0, "summary": "снип внутри"}],
        pages={"https://ex.com/0": "первая строка втораятретья"},
    )
    research = (await call("research_create", title="Разделители"))["code"]
    area = (await call("area_create", research_code=research, title="Область"))["code"]
    await call("query_search_run", area_code=area, query="q")

    archive = await _archive(tmp_path, strip_prefix(research), name="separators.urch")
    await _wipe()
    _, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert report.counts[ENTITY_PAGES]["created"] == 1
    assert (await _rows(WebSearchPage))[0].body == "первая строка втораятретья"


def _rewrite_archive(source, target, *, drop_first_row_of: str) -> None:
    """Пересобрать архив без первой строки одного из файлов — и **починить манифест** под него.

    Без правки манифеста подделку ловит сверка сумм, и проверка связности так и остаётся
    непроверенной: тест был бы зелёным по другой причине (мутационный прогон это и показал).
    """
    import hashlib
    import json
    import zipfile

    with zipfile.ZipFile(source) as original:
        entries = {item.filename: original.read(item.filename) for item in original.infolist()}
        order = [item.filename for item in original.infolist()]

    entries[drop_first_row_of] = b"\n".join(entries[drop_first_row_of].split(b"\n")[1:])
    manifest = json.loads(entries["manifest.json"])
    for item in manifest["files"]:
        if item["path"] != drop_first_row_of:
            continue
        item["bytes"] = len(entries[drop_first_row_of])
        item["sha256"] = hashlib.sha256(entries[drop_first_row_of]).hexdigest()
    entries["manifest.json"] = json.dumps(manifest, ensure_ascii=False).encode("utf-8")

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as tampered:
        for name in order:
            tampered.writestr(name, entries[name])


async def test_an_unknown_mode_is_refused_by_the_core_not_only_by_the_handler(
    call, use_search, tmp_path
):
    """Режим проверяется там, где по нему принимают решение, а не только на границе HTTP."""
    codes = await _seed(call, use_search, pages=1)
    archive = await _archive(tmp_path, codes["research"])

    from src.modules.research.transfer.errors import ArchiveError

    with pytest.raises(ArchiveError):
        await analyze_archive(archive.path, mode="как-нибудь")


async def test_exporting_a_research_that_is_gone_says_so(db, tmp_path):
    with pytest.raises(LookupError):
        await export_research("0000000000", tmp_path / "missing.urch")


async def test_dangling_reference_is_reported_not_erased(call, use_search, tmp_path):
    codes = await _seed(call, use_search, pages=1)
    await call(
        "body_set",
        code=f"RESEARCH@{codes['research']}",
        text="ссылка наружу: NOTE@a19ec74847",
    )
    archive = await _archive(tmp_path, codes["research"])
    await _wipe()

    plan, report = await import_archive(archive.path, mode=IMPORT_MODE_NEWER)

    assert "NOTE@a19ec74847" in plan.warnings.dangling_refs
    assert "NOTE@a19ec74847" in report.dangling_refs
    assert "NOTE@a19ec74847" in (await _rows(Research))[0].body
