"""Проверка пайплайна: web_search + строгий JSON-массив релевантных ссылок.

Ключевой вопрос — заземлены ли возвращённые URL (из реального поиска) или выдуманы.
Сверяем links[].url против объединения web_search_call.action.sources[].url.

    uv run python -m dev.bench.core_connectors.xai.verify_relevant_links
"""

from __future__ import annotations

import asyncio
import json

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from src.core.database import close_database
from src.modules.core_connectors.services.xai import (
    GROK_FLAGSHIP,
    XaiGateway,
    XaiResponsesParams,
    XaiWebSearchTool,
    json_schema_text,
)

AGENT_INSTRUCTION = (
    "Ты ассистент-ресёрчер. По запросу пользователя найди в вебе самые релевантные "
    "источники (официальная документация, авторитетные статьи, разборы). Верни только "
    "ссылки, отсортированные по убыванию релевантности; не выдумывай URL — бери из поиска."
)
USER_QUERY = "Создание системы очередей на Python"

LINKS_SCHEMA = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "reason": {"type": "string"},
                    "relevance": {"type": "number"},
                },
                "required": ["url", "title", "reason", "relevance"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["links"],
    "additionalProperties": False,
}


def _norm(u: str) -> str:
    return (u or "").rstrip("/").lower()


async def main() -> None:
    await load_gateway_store()
    params = XaiResponsesParams(
        model=GROK_FLAGSHIP,
        instructions=AGENT_INSTRUCTION,
        input=USER_QUERY,
        tools=[XaiWebSearchTool()],
        text=json_schema_text("relevant_links", LINKS_SCHEMA),
    )
    try:
        data = await XaiGateway().responses(params)
    finally:
        await close_database()

    usage = data.get("usage") or {}
    print("status:", data.get("status"),
          "| web_search_calls:", (usage.get("server_side_tool_usage_details") or {}).get("web_search_calls"))

    searched: set[str] = set()
    for item in data.get("output") or []:
        if item.get("type") == "web_search_call":
            for s in (item.get("action") or {}).get("sources") or []:
                searched.add(_norm(s.get("url")))

    msg = [i for i in (data.get("output") or []) if i.get("type") == "message"][0]
    parsed = json.loads(msg["content"][0]["text"])
    links = parsed["links"]
    print(f"\nвернул ссылок: {len(links)} | поиск нашёл уникальных: {len(searched)}\n")
    grounded = 0
    for i, l in enumerate(links, 1):
        ok = _norm(l["url"]) in searched
        grounded += ok
        print(f"  {i}. [{l['relevance']}] grounded={'Y' if ok else 'NO'} {l['url']}")
        print(f"     {l['title']}")
    print(f"\nзаземлено (URL из реального поиска): {grounded}/{len(links)}")


if __name__ == "__main__":
    asyncio.run(main())
