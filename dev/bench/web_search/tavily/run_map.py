"""Map (beta): обнаружение структуры сайта — только URL, без контента.

    uv run python -m dev.bench.web_search.tavily.run_map
"""

from __future__ import annotations

from dev.bench.web_search.tavily import client
from dev.bench.web_search.tavily.constants import MAP_URL


def main() -> None:
    payload = {"url": MAP_URL, "max_depth": 1, "limit": 30}
    data = client.call("map", payload)
    path = client.save("map", data)

    print(f"top-level keys: {sorted(data)}")
    print(f"base_url={data.get('base_url')}  response_time={data.get('response_time')}")
    results = data.get("results", [])
    print(f"discovered URLs: {len(results)}")
    for u in results[:15]:
        print(f"  {u}")
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
