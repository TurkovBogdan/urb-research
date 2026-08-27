"""research MCP: interface_open — код любой сущности → адрес страницы + открытие в браузере.

``webbrowser.open`` подменяется: тест проверяет, что открыли ровно тот адрес, что вернули.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from src.modules.research.mcp import interface

pytestmark = pytest.mark.db


@pytest.fixture
def opened(monkeypatch):
    """Перехватить открытие браузера: список адресов, которые тул попытался открыть."""
    urls: list[str] = []

    def _open(url: str) -> bool:
        urls.append(url)
        return True

    monkeypatch.setattr(interface.webbrowser, "open", _open)
    return urls


@pytest.mark.parametrize(
    ("code", "path"),
    [
        ("RESEARCH@abc0000000000000000001", "/research/researches/RESEARCH@abc0000000000000000001"),
        ("GROUP@abc0000000000000000002", "/research/researches/GROUP@abc0000000000000000002"),
        ("AREA@abc0000000000000000003", "/research/areas/AREA@abc0000000000000000003"),
        ("NOTE@abc0000000000000000004", "/research/notes/NOTE@abc0000000000000000004"),
        ("QUERY@abc0000000000000000005", "/research/queries/QUERY@abc0000000000000000005"),
        ("SOURCE@abc0000000000000000006", "/research/sources/SOURCE@abc0000000000000000006"),
        ("SEARCH@abc0000000000000000007", "/web-search/queries/abc0000000000000000007"),
        ("PAGE@abc0000000000000000008", "/web-search/pages/abc0000000000000000008"),
    ],
)
async def test_interface_open_maps_every_code_type_to_its_page(call, opened, code, path):
    url = (await call("interface_open", code=code))["result"]

    assert url.endswith(path)
    assert url.startswith("http://")
    assert opened == [url]


async def test_interface_open_reports_a_host_with_no_browser(call, monkeypatch):
    """Открыть нечем — отказ с адресом в тексте, а не молчаливое «сделано»."""
    monkeypatch.setattr(interface.webbrowser, "open", lambda url: False)

    with pytest.raises(ToolError, match="No browser to open"):
        await call("interface_open", code="RESEARCH@abc0000000000000000011")


async def test_interface_open_rejects_an_untyped_code(call, opened):
    with pytest.raises(ToolError, match="RESEARCH@ / AREA@"):
        await call("interface_open", code="abc0000000000000000009")

    assert opened == []


async def test_interface_open_rejects_an_unknown_code_type(call, opened):
    with pytest.raises(ToolError, match="RESEARCH@ / AREA@"):
        await call("interface_open", code="WIDGET@abc0000000000000000010")

    assert opened == []
