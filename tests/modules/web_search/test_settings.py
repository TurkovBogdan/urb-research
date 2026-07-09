"""web_search: runtime-настройки — движок поиска + сервис контента; токены в core_connectors."""

from __future__ import annotations

import pytest

from src.core.settings.fields import ChoiceField, IntField
from src.modules.web_search import WebSearchModule
from src.modules.web_search.settings import SCHEMA


@pytest.mark.pure
def test_schema_has_search_and_fetch_engines():
    by_key = {f.key: f for f in SCHEMA}
    assert isinstance(by_key["search_engine"], ChoiceField)
    assert isinstance(by_key["fetch_engine"], ChoiceField)

    search_opts = {code for code, _ in by_key["search_engine"].options}
    fetch_opts = {code for code, _ in by_key["fetch_engine"].options}
    assert search_opts == {"tavily", "firecrawl", "xai"}  # Grok умеет искать
    assert fetch_opts == {"tavily", "firecrawl", "web_scrapper"}  # daemon-web-scrapper — только фетч


@pytest.mark.pure
def test_schema_has_max_concurrent_searches_limit():
    by_key = {f.key: f for f in SCHEMA}
    field = by_key["max_concurrent_searches"]
    assert isinstance(field, IntField)
    assert field.default_ == 3  # консервативный дефолт, правится на /core/settings
    assert (field.min, field.max) == (1, 50)


@pytest.mark.pure
def test_schema_has_no_api_tokens():
    # Токены доступа живут в core_connectors, не в web_search.
    keys = {f.key for f in SCHEMA}
    assert "tavily_api_key" not in keys
    assert "firecrawl_api_key" not in keys


@pytest.mark.pure
def test_module_exposes_settings_schema_no_config_cls():
    assert WebSearchModule.name == "web_search"
    assert WebSearchModule.settings_schema is SCHEMA
    assert WebSearchModule.config_cls is None
