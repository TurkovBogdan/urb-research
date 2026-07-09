"""Сверить structured output (strict json_schema) через /v1/responses живьём.

Строим payload вручную (в типизированной модели поля `text` пока нет) и постим через
XaiGateway._post, чтобы проверить, принимает ли xAI `text.format=json_schema, strict`.

    uv run python -m dev.bench.core_connectors.xai.verify_structured
"""

from __future__ import annotations

import asyncio
import json

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from src.core.database import close_database
from src.modules.core_connectors.services.xai import XaiGateway, GROK_FLAGSHIP

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}


async def main() -> None:
    await load_gateway_store()
    gw = XaiGateway()
    payload = {
        "model": GROK_FLAGSHIP,
        "input": "Извлеки данные: Ивану Петрову 30 лет.",
        "text": {
            "format": {
                "type": "json_schema",
                "name": "person",
                "strict": True,
                "schema": SCHEMA,
            }
        },
    }
    try:
        data = await gw._post("/v1/responses", payload)
    finally:
        await close_database()

    print("status:", data.get("status"))
    print("text echo:", json.dumps(data.get("text"), ensure_ascii=False))
    msg = [i for i in (data.get("output") or []) if i.get("type") == "message"]
    if msg:
        text = msg[0]["content"][0].get("text")
        print("raw text:", text)
        try:
            print("parsed:", json.loads(text))
        except Exception as exc:  # noqa: BLE001
            print("NOT valid json:", exc)


if __name__ == "__main__":
    asyncio.run(main())
