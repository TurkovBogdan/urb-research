"""research MCP: query_search_run / list / delete + sources_list / source_get / source_review.

Веб-поиск застаблен (``use_search``): ``query_search_run`` наполняет источники детерминированно.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db

_SOURCE_KEYS = {
    "code",
    "status",
    "url",
    "title",
    "summary",
    "note",
    "relevance",
    "updated_at",
}


async def _seed(call, use_search, n: int = 2):
    """research + area + застабленный прогон на ``n`` страниц. → (research, area, query, sources)."""
    use_search(
        results=[
            {"url": f"https://ex.com/{i}", "rank": i, "summary": f"snip{i}"} for i in range(n)
        ],
        pages={f"https://ex.com/{i}": f"# body {i}" for i in range(n)},
    )
    r = (await call("research_create", title="R"))["code"]
    a = (await call("area_create", research_code=r, title="A"))["code"]
    sources = (await call("query_search_run", area_code=a, query="q"))["result"]
    q = (await call("query_search_list", code=a))["result"][0]["code"]
    return r, a, q, sources


async def test_query_search_run_creates_and_returns_sources(call, use_search):
    _, _, _, sources = await _seed(call, use_search, n=2)
    assert len(sources) == 2
    s = sources[0]
    assert set(s) == _SOURCE_KEYS
    assert s["code"].startswith("SOURCE@")
    assert s["status"] == "pending"
    assert s["url"] == "https://ex.com/0" and s["summary"] == "snip0"
    assert s["relevance"] is None


async def _seed_unfetched(call, use_search, **stub):
    """research + area + прогон, где контент страницы не дошёл. → список источников."""
    engine = use_search(
        results=[{"url": "https://ex.com/0", "rank": 1, "summary": "snip0"}], **stub
    )
    r = (await call("research_create", title="R"))["code"]
    a = (await call("area_create", research_code=r, title="A"))["code"]
    sources = (await call("query_search_run", area_code=a, query="q"))["result"]
    return r, a, sources, engine


async def test_query_search_run_marks_source_error_when_page_empty(call, use_search):
    _, _, sources, _ = await _seed_unfetched(call, use_search, pages={})

    assert len(sources) == 1
    assert sources[0]["status"] == "error"


async def test_query_search_run_marks_source_error_when_engine_unreachable(call, use_search):
    _, _, sources, _ = await _seed_unfetched(
        call, use_search, fetch_raises=ConnectionError("daemon down")
    )

    assert sources[0]["status"] == "error"


async def test_unfetched_source_is_filtered_out_of_the_review_queue(call, use_search):
    r, _, _, _ = await _seed_unfetched(call, use_search, pages={})

    assert (await call("sources_list", code=r, status="pending"))["result"] == []
    broken = (await call("sources_list", code=r, status="error"))["result"]
    assert len(broken) == 1 and broken[0]["url"] == "https://ex.com/0"


async def test_source_get_explains_a_missing_body(call, use_search):
    _, _, sources, _ = await _seed_unfetched(call, use_search, pages={})

    g = await call("source_get", source_code=sources[0]["code"])

    assert g["body"] is None
    assert g["status"] == "error"
    assert g["summary"] == "snip0"


async def test_sources_refetch_revives_a_source_once_the_material_arrives(call, use_search):
    r, _, sources, engine = await _seed_unfetched(call, use_search, pages={})
    engine.pages = {"https://ex.com/0": "# body 0"}

    report = await call("sources_refetch", codes=[r])

    assert len(report["sources"]) == 1 and report["skipped"] == []
    revived = report["sources"][0]
    assert revived["code"] == sources[0]["code"] and revived["status"] == "pending"
    assert (await call("source_get", source_code=sources[0]["code"]))["body"] == "# body 0"


async def test_sources_refetch_reports_a_source_that_failed_again(call, use_search):
    r, _, _, _ = await _seed_unfetched(call, use_search, pages={})

    report = await call("sources_refetch", codes=[r])

    assert len(report["sources"]) == 1 and report["sources"][0]["status"] == "error"


async def test_sources_refetch_takes_a_single_source_code(call, use_search):
    _, _, sources, engine = await _seed_unfetched(call, use_search, pages={})
    engine.pages = {"https://ex.com/0": "# body 0"}

    report = await call("sources_refetch", codes=[sources[0]["code"]])

    assert len(report["sources"]) == 1 and report["sources"][0]["status"] == "pending"


async def test_sources_refetch_takes_several_codes_at_once(call, use_search):
    """Пакет из кодов разных уровней — один прогон, источники со всех."""
    _, _, first, engine = await _seed_unfetched(call, use_search, pages={})
    second_research = (await call("research_create", title="R2"))["code"]
    second_area = (await call("area_create", research_code=second_research, title="A2"))["code"]
    engine.results = [{"url": "https://ex.com/9", "rank": 0, "summary": "snip9"}]
    await call("query_search_run", area_code=second_area, query="q2")
    engine.pages = {"https://ex.com/0": "# body 0", "https://ex.com/9": "# body 9"}

    report = await call("sources_refetch", codes=[first[0]["code"], second_research])

    assert {row["status"] for row in report["sources"]} == {"pending"}
    assert len(report["sources"]) == 2 and report["skipped"] == []


async def test_sources_refetch_does_not_download_an_overlapping_scope_twice(call, use_search):
    """Исследование и его же область в одном вызове — источник в ответе один, не два."""
    r, a, sources, engine = await _seed_unfetched(call, use_search, pages={})
    engine.pages = {"https://ex.com/0": "# body 0"}

    report = await call("sources_refetch", codes=[r, a, sources[0]["code"]])

    assert [row["code"] for row in report["sources"]] == [sources[0]["code"]]


async def test_sources_refetch_reports_a_code_with_nothing_to_fix(call, use_search):
    r, _, _, _ = await _seed(call, use_search, n=2)

    report = await call("sources_refetch", codes=[r])

    assert report["sources"] == []
    assert report["skipped"] == [{"code": r, "reason": "nothing_to_fix"}]


async def test_sources_refetch_reports_bad_codes_without_dropping_the_good_one(call, use_search):
    """Промах одного кода не отменяет работу по остальным — он уходит в отчёт со своей причиной."""
    r, _, _, engine = await _seed_unfetched(call, use_search, pages={})
    engine.pages = {"https://ex.com/0": "# body 0"}

    report = await call(
        "sources_refetch",
        codes=["NOTE@x0000000000000000000", "SOURCE@missing00000000000", r],
    )

    assert len(report["sources"]) == 1 and report["sources"][0]["status"] == "pending"
    assert report["skipped"] == [
        {"code": "NOTE@x0000000000000000000", "reason": "not_a_source_code"},
        {"code": "SOURCE@missing00000000000", "reason": "not_found"},
    ]


async def test_sources_refetch_caps_the_number_of_codes(call, use_search):
    r, _, _, _ = await _seed_unfetched(call, use_search, pages={})

    with pytest.raises(ToolError, match="At most 6 codes"):
        await call("sources_refetch", codes=[r] * 7)


async def test_sources_refetch_needs_at_least_one_code(call):
    with pytest.raises(ToolError, match="at least one code"):
        await call("sources_refetch", codes=[])


async def test_sources_refetch_revives_the_same_page_in_another_research(call, use_search):
    """Страница дедуплицирована на несколько исследований — оживает у всех, не только в скоупе."""
    first, _, _, engine = await _seed_unfetched(call, use_search, pages={})
    second = (await call("research_create", title="R2"))["code"]
    other_area = (await call("area_create", research_code=second, title="A2"))["code"]
    await call("query_search_run", area_code=other_area, query="q2")
    engine.pages = {"https://ex.com/0": "# body 0"}

    await call("sources_refetch", codes=[first])

    assert (await call("sources_list", code=second, status="error"))["result"] == []
    assert len((await call("sources_list", code=second, status="pending"))["result"]) == 1


async def test_sources_refetch_refuses_a_disabled_fetch_engine(call, use_search, monkeypatch):
    """Движок контента выключен — отказ до сети, а не сотня страниц, разложенных в ``error``."""
    r, _, _, engine = await _seed_unfetched(call, use_search, pages={})
    monkeypatch.setattr(engine, "available", lambda: False)

    with pytest.raises(ToolError, match="fetch_engine_disabled"):
        await call("sources_refetch", codes=[r])


async def test_query_search_run_no_results_records_search(call, use_search):
    use_search(results=[])
    r = (await call("research_create", title="R"))["code"]
    a = (await call("area_create", research_code=r, title="A"))["code"]

    sources = (await call("query_search_run", area_code=a, query="q"))["result"]

    assert sources == []
    searches = (await call("query_search_list", code=a))["result"]
    assert len(searches) == 1 and searches[0]["query"] == "q"


async def test_query_search_run_area_not_found(call):
    with pytest.raises(ToolError, match="Area .* not found"):
        await call("query_search_run", area_code="AREA@missing0000000000000", query="q")


async def test_query_search_list_by_area_and_research(call, use_search):
    r, a, _, _ = await _seed(call, use_search, n=1)
    by_area = (await call("query_search_list", code=a))["result"]
    by_research = (await call("query_search_list", code=r))["result"]
    assert len(by_area) == 1 and len(by_research) == 1
    assert set(by_area[0]) == {"code", "area_code", "query"}


async def test_query_search_list_bad_code(call):
    with pytest.raises(ToolError, match="AREA@ or RESEARCH@"):
        await call("query_search_list", code="SOURCE@x000000000000000000")


async def test_query_search_delete_cascades_sources(call, use_search):
    r, _, q, sources = await _seed(call, use_search, n=2)
    assert (await call("query_search_delete", query_code=q))["result"] is True
    assert (await call("sources_list", code=r))["result"] == []


async def test_query_search_delete_missing_false(call):
    assert (await call("query_search_delete", query_code="QUERY@missing00000000000"))["result"] is False


async def test_sources_list_by_levels_and_status_filter(call, use_search):
    r, a, q, sources = await _seed(call, use_search, n=2)

    for code in (r, a, q):
        assert len((await call("sources_list", code=code))["result"]) == 2

    await call("source_review", source_code=sources[0]["code"], decision="keep", relevance=8)
    kept = (await call("sources_list", code=r, status="kept"))["result"]
    pending = (await call("sources_list", code=r, status="pending"))["result"]
    assert len(kept) == 1 and len(pending) == 1
    assert set(kept[0]) == _SOURCE_KEYS


async def test_sources_list_bad_code(call):
    with pytest.raises(ToolError, match="RESEARCH@ / AREA@ / QUERY@"):
        await call("sources_list", code="NOTE@x0000000000000000000")


async def test_source_get_has_body(call, use_search):
    _, _, _, sources = await _seed(call, use_search, n=1)
    g = await call("source_get", source_code=sources[0]["code"])
    assert g["body"] == "# body 0"
    assert list(g.keys())[-1] == "updated_at"


async def test_source_get_not_found(call):
    with pytest.raises(ToolError, match="Source .* not found"):
        await call("source_get", source_code="SOURCE@missing00000000000")


async def test_source_review_keep_and_filter(call, use_search):
    _, _, _, sources = await _seed(call, use_search, n=2)

    kept = await call("source_review", source_code=sources[0]["code"], decision="keep", relevance=9)
    assert kept["status"] == "kept" and kept["relevance"] == 9

    filtered = await call(
        "source_review", source_code=sources[1]["code"], decision="filter", relevance=2, note="dup"
    )
    assert filtered["status"] == "filtered" and filtered["note"] == "dup"


async def test_source_review_bad_decision(call, use_search):
    _, _, _, sources = await _seed(call, use_search, n=1)
    with pytest.raises(ToolError, match="decision must be"):
        await call("source_review", source_code=sources[0]["code"], decision="maybe", relevance=5)


async def test_source_review_bad_relevance(call, use_search):
    _, _, _, sources = await _seed(call, use_search, n=1)
    with pytest.raises(ToolError, match="relevance must be"):
        await call("source_review", source_code=sources[0]["code"], decision="keep", relevance=99)


async def test_source_review_not_found(call):
    with pytest.raises(ToolError, match="Source .* not found"):
        await call("source_review", source_code="SOURCE@missing00000000000", decision="keep", relevance=5)
