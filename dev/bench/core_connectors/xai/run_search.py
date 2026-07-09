"""Живой прогон xAI Responses API с web_search: что возвращает, форма citations/annotations.

    uv run python -m dev.bench.core_connectors.xai.run_search
"""

from __future__ import annotations

import asyncio
import json

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from dev.bench.core_connectors.xai.constants import OUT_DIR, SEARCH_QUERY
from src.core.database import close_database
from src.modules.core_connectors.services.xai import (
    GROK_FLAGSHIP,
    XaiGateway,
    XaiResponsesParams,
    XaiWebSearchTool,
)


def _text_blocks(output: list[dict]) -> list[dict]:
    return [c for item in output if isinstance(item, dict)
            for c in (item.get("content") or []) if isinstance(c, dict)]


async def main() -> None:
    await load_gateway_store()
    try:
        params = XaiResponsesParams(
            model=GROK_FLAGSHIP,
            input=SEARCH_QUERY,
            tools=[XaiWebSearchTool()],
        )
        data = await XaiGateway().responses(params)
    finally:
        await close_database()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "search.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"top-level keys: {sorted(data)}")
    print(f"id={data.get('id')}  model={data.get('model')}  status={data.get('status')}")
    print(f"usage={json.dumps(data.get('usage'), ensure_ascii=False)}")
    citations = data.get("citations")
    print(f"citations: {len(citations) if citations else 0}")
    for c in (citations or [])[:10]:
        print(f"  - {c}")
    text = data.get("output_text")
    if text:
        print(f"\noutput_text[{len(text)}]:\n{text[:600]}…")
    for block in _text_blocks(data.get("output") or []):
        anns = block.get("annotations")
        if anns:
            print(f"\nannotations: {len(anns)}; first: {json.dumps(anns[0], ensure_ascii=False)}")
            break
    print(f"\nsaved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
