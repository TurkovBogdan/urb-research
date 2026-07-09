"""research MCP: query_search_run / list / delete + sources_list / source_get / source_review.

Веб-поиск застаблен (``use_search``): ``query_search_run`` наполняет источники детерминированно.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

pytestmark = pytest.mark.db

_SOURCE_KEYS = {"code", "status", "url", "title", "summary", "note", "relevance", "updated_at"}


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
