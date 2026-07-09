"""Тонкий клиент Tavily для верстака: POST к API + сохранение сырого ответа в tmp/.

Ключ берём из runtime-настроек коннектора (``core_connectors.settings.service_api_key``) —
верстак догфудит модуль. Аутентификация — заголовок ``Authorization: Bearer <key>``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from dev.bench.web_search.tavily.constants import BASE_URL, OUT_DIR, TIMEOUT
from src.modules.core_connectors.settings import service_api_key


def api_key() -> str:
    key = service_api_key("tavily_api_key")
    if not key:
        raise SystemExit("TAVILY_API_KEY не задан в .env")
    return key


def call(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST ``payload`` на ``/<endpoint>`` Tavily, вернуть JSON-ответ."""
    response = httpx.post(
        f"{BASE_URL}/{endpoint}",
        json=payload,
        headers={"Authorization": f"Bearer {api_key()}"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def save(name: str, data: dict[str, Any]) -> Path:
    """Сохранить сырой ответ в ``tmp/<name>.json`` для локальных прогонов без сети."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
