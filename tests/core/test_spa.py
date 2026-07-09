"""spa: middleware раздачи фронта — граница API-префиксов и резолв файла."""

from __future__ import annotations

import pytest

from src.core.router.spa import SpaStaticMiddleware, _is_api_path

_API = ("/api", "/internal", "/storage", "/mcp", "/webhook")


async def _noop_app(scope, receive, send):  # pragma: no cover — заглушка downstream
    raise AssertionError("downstream не должен вызываться для SPA-путей")


@pytest.mark.pure
@pytest.mark.parametrize(
    "path,is_api",
    [
        ("/api", True),
        ("/api/things", True),
        ("/internal/health", True),
        ("/storage/x", True),
        ("/apidocs", False),  # префикс должен совпадать по сегменту, не по подстроке
        ("/", False),
        ("/login", False),
        ("/assets/index-abc.js", False),
    ],
)
def test_is_api_path_matches_on_segment_boundary(path: str, is_api: bool):
    assert _is_api_path(path, _API) is is_api


@pytest.mark.pure
def test_spa_response_serves_file_else_index(tmp_path):
    (tmp_path / "index.html").write_text("<div id=\"app\"></div>")
    (tmp_path / "assets").mkdir()
    asset = tmp_path / "assets" / "a.js"
    asset.write_text("export {}")
    mw = SpaStaticMiddleware(_noop_app, dist=tmp_path, api_prefixes=_API)

    index = (tmp_path / "index.html").resolve()
    assert mw._spa_response("/assets/a.js").path == asset.resolve()
    # deep-link клиентского роутинга → index.html
    assert mw._spa_response("/conversations/42").path == index
    # выход за пределы dist (traversal) → index.html, не файл снаружи
    assert mw._spa_response("/../secret").path == index
