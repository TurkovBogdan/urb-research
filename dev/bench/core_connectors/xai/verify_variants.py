"""Сверить multi-agent (agent_count) и x_search живьём — разрешить «не сверено» в моделях.

    uv run python -m dev.bench.core_connectors.xai.verify_variants
"""

from __future__ import annotations

import asyncio
import json

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from src.core.database import close_database
from src.modules.core_connectors.services.xai import (
    GROK_FLAGSHIP,
    GROK_MULTI_AGENT,
    XaiGateway,
    XaiResponsesParams,
    XaiXSearchTool,
)


async def main() -> None:
    await load_gateway_store()
    gw = XaiGateway()
    try:
        print("== model(alias grok-4.20-multi-agent) ==")
        try:
            m = await gw.model(GROK_MULTI_AGENT)
            print("resolved id:", m.get("id"), "| aliases:", m.get("aliases"))
        except Exception as exc:  # noqa: BLE001
            print("alias НЕ резолвится:", type(exc).__name__, str(exc)[:200])

        print("\n== multi-agent + agent_count=4 ==")
        try:
            r = await gw.responses(XaiResponsesParams(
                model=GROK_MULTI_AGENT,
                input="Одним предложением: чем TCP отличается от UDP?",
                agent_count=4,
            ))
            print("status:", r.get("status"), "| model echo:", r.get("model"))
            print("output types:", [i.get("type") for i in (r.get("output") or [])][:12])
            print("usage:", json.dumps(r.get("usage"), ensure_ascii=False)[:300])
        except Exception as exc:  # noqa: BLE001
            print("agent_count упал:", type(exc).__name__, str(exc)[:300])

        print("\n== x_search ==")
        r = await gw.responses(XaiResponsesParams(
            model=GROK_FLAGSHIP,
            input="Что недавно постил аккаунт @xai? Кратко.",
            tools=[XaiXSearchTool(allowed_x_handles=["xai"], from_date="2026-06-01")],
        ))
        print("status:", r.get("status"))
        print("output types:", [i.get("type") for i in (r.get("output") or [])][:12])
        usage = r.get("usage") or {}
        print("tool usage:", json.dumps(usage.get("server_side_tool_usage_details"), ensure_ascii=False))
        for item in (r.get("output") or []):
            if item.get("type") == "x_search_call":
                print("x_search_call action keys:", sorted((item.get("action") or {})))
                print("action sample:", json.dumps(item.get("action"), ensure_ascii=False)[:400])
                break
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
