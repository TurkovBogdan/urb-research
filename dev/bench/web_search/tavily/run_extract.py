"""Extract: достать полный контент по готовому списку URL (markdown).

Это путь «доскрейпа» указателей (bucket B) и цитат (bucket C) → тело document.

    uv run python -m dev.bench.web_search.tavily.run_extract
"""

from __future__ import annotations

from dev.bench.web_search.tavily import client
from dev.bench.web_search.tavily.constants import EXTRACT_URLS


def main() -> None:
    payload = {
        "urls": EXTRACT_URLS,
        "format": "markdown",
        "extract_depth": "basic",
    }
    data = client.call("extract", payload)
    path = client.save("extract", data)

    print(f"top-level keys: {sorted(data)}")
    print(f"response_time={data.get('response_time')}")
    for r in data.get("results", []):
        raw = r.get("raw_content") or ""
        print(f"  ok: {r.get('url')}  raw_content[{len(raw)}]  keys={sorted(r)}")
    for f in data.get("failed_results", []):
        print(f"  failed: {f}")
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
