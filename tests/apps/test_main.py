"""apps/app: интеграционная сборка — health, CORS, lifespan."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.db
async def test_health():
    from src.apps.app.server import app

    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            r = await c.get("/internal/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}


@pytest.mark.pure
async def test_cors_headers_on_preflight():
    from src.apps.app.server import app
    from src.core.config import Config

    origin = f"http://localhost:{Config().server_vite_port}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.options(
            "/internal/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.status_code in (200, 204)
        assert r.headers.get("access-control-allow-origin") == origin


@pytest.mark.pure
def test_health_route_registered():
    from src.apps.app.server import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/internal/health" in paths
