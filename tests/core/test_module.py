"""Module ABC: declarative attrs + default hooks."""

from __future__ import annotations

import pytest

from pathlib import Path

from fastapi import FastAPI
from pydantic_settings import BaseSettings

from src.core.config import Config
from src.core.module import Module


@pytest.mark.pure
def test_minimal_module():
    class X(Module):
        name = "x"

    m = X()
    assert m.name == "x"
    assert m.migrations_dir is None
    assert m.config_cls is None
    assert m.settings_schema is None


@pytest.mark.pure
def test_full_module():
    class XConfig(BaseSettings):
        pass

    class X(Module):
        name = "x"
        migrations_dir = Path("/tmp/x/versions")
        config_cls = XConfig

    m = X()
    assert m.migrations_dir == Path("/tmp/x/versions")
    assert m.config_cls is XConfig


@pytest.mark.pure
def test_default_hooks_are_noops():
    class X(Module):
        name = "x"

    m = X()
    app = FastAPI()
    cfg = Config()
    m.configure(app, cfg)
    m.on_settings_change(object())


@pytest.mark.pure
async def test_default_shutdown_noop():
    class X(Module):
        name = "x"

    m = X()
    await m.shutdown(FastAPI())
