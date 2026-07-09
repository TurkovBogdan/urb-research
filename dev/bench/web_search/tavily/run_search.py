"""Базовый поиск Tavily: как запускается и что возвращает (топ-уровень + поля результата).

    uv run python -m dev.bench.web_search.tavily.run_search
"""

from __future__ import annotations

from dev.bench.web_search.tavily import client
from dev.bench.web_search.tavily.constants import SEARCH_QUERY


def main() -> None:
    payload = {
        "query": SEARCH_QUERY,
        "search_depth": "basic",
        "max_results": 5,
        "topic": "general",
        "include_answer": False,
        "include_raw_content": False,
    }
    data = client.call("search", payload)
    path = client.save("search", data)

    print(f"query: {data.get('query')}")
    print(f"top-level keys: {sorted(data)}")
    print(f"response_time={data.get('response_time')}  request_id={data.get('request_id')}")
    results = data.get("results", [])
    print(f"results: {len(results)}")
    for i, r in enumerate(results, 1):
        content = r.get("content") or ""
        print(f"  {i}. score={r.get('score')} | {(r.get('title') or '')[:70]}")
        print(f"     url: {r.get('url')}")
        print(f"     content[{len(content)}]: {content[:120]}…")
        print(f"     raw_content: {'present' if r.get('raw_content') else 'None'}")
        print(f"     result keys: {sorted(r)}")
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
