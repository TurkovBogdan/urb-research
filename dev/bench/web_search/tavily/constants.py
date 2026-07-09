"""Константы верстака Tavily: базовый URL, директория артефактов, фикс-запросы."""

from __future__ import annotations

from pathlib import Path

BASE_URL = "https://api.tavily.com"
OUT_DIR = Path(__file__).resolve().parent / "tmp"
TIMEOUT = 60.0

SEARCH_QUERY = "SQLAlchemy events architecture options (ORM mapper/session events, listen, before_insert, after_update)"

EXTRACT_URLS = [
    "https://docs.tavily.com/documentation/api-reference/endpoint/search",
]

MAP_URL = "https://docs.tavily.com"
