"""Module lifecycle: configure ordering, settings dispatch, reverse shutdown."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI

from src.core.settings.fields import IntField
from src.core.app_factory import create_app
from src.core.config import Config
from src.core.module import Module
from tests.core._support import AuthStubModule


@pytest.fixture
def config() -> Config:
    return Config()


def _make_module(
    name: str, calls: list[str], *, schema=None, shutdown_raises: bool = False
):
    class _M(Module):
        pass

    _M.name = name
    _M.settings_schema = schema

    def configure(self, app: FastAPI, cfg: Config) -> None:
        calls.append(f"configure:{name}")

    def on_settings_change(self, store: Any) -> None:
        calls.append(f"settings:{name}")

    async def shutdown(self, app: FastAPI) -> None:
        calls.append(f"shutdown:{name}")
        if shutdown_raises:
            raise RuntimeError("boom")

    _M.configure = configure
    _M.on_settings_change = on_settings_change
    _M.shutdown = shutdown
    return _M()


@pytest.mark.pure
def test_configure_order_matches_list(config: Config):
    calls: list[str] = []
    a = _make_module("la", calls)
    b = _make_module("lb", calls)
    create_app(modules=[AuthStubModule(), a, b], config=config)
    assert calls == ["configure:la", "configure:lb"]


@pytest.mark.db
async def test_lifespan_dispatches_initial_settings_change(config: Config):
    calls: list[str] = []
    m = _make_module(
        "lc", calls,
        schema=(IntField(key="n", label="N", default_=1),),
    )
    app = create_app(modules=[AuthStubModule(), m], config=config)
    async with app.router.lifespan_context(app):
        pass
    assert "settings:lc" in calls


@pytest.mark.db
async def test_shutdown_reverse_order_even_on_exception(config: Config):
    calls: list[str] = []
    a = _make_module("ra", calls)
    b = _make_module("rb", calls, shutdown_raises=True)
    c = _make_module("rc", calls)
    app = create_app(modules=[AuthStubModule(), a, b, c], config=config)
    async with app.router.lifespan_context(app):
        pass
    shutdown_calls = [c for c in calls if c.startswith("shutdown:")]
    assert shutdown_calls == ["shutdown:rc", "shutdown:rb", "shutdown:ra"]
