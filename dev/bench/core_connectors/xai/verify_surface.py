"""Проверка всей поверхности XaiGateway живьём: read-методы + tokenize + get/delete roundtrip.

    uv run python -m dev.bench.core_connectors.xai.verify_surface
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
    XaiTokenizeParams,
)


def _short(data: object, limit: int = 300) -> str:
    return json.dumps(data, ensure_ascii=False)[:limit]


async def main() -> None:
    await load_gateway_store()
    gw = XaiGateway()
    try:
        print("== api_key_info ==")
        info = await gw.api_key_info()
        print("keys:", sorted(info))

        print("\n== models ==")
        models = await gw.models()
        ids = [m.get("id") for m in (models.get("data") or models.get("models") or [])]
        print("top keys:", sorted(models), "| ids:", ids[:12])

        print("\n== language_models ==")
        lm = await gw.language_models()
        print("top keys:", sorted(lm), "| sample:", _short(lm, 200))

        print("\n== model(grok-4.3) ==")
        print(_short(await gw.model(GROK_FLAGSHIP), 300))

        print("\n== tokenize ==")
        tok = await gw.tokenize(XaiTokenizeParams(text="очередь на Python", model=GROK_FLAGSHIP))
        print(_short(tok, 300))

        print("\n== responses roundtrip (store→get→delete) ==")
        created = await gw.responses(XaiResponsesParams(
            model=GROK_FLAGSHIP, input="Ответь одним словом: столица Франции?", store=True,
        ))
        rid = created.get("id")
        print("created id:", rid, "| status:", created.get("status"))
        got = await gw.get_response(rid)
        print("get status:", got.get("status"), "| same id:", got.get("id") == rid)
        deleted = await gw.delete_response(rid)
        print("delete:", _short(deleted, 200))
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
