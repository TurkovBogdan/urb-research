"""Поиск с полным контентом: include_raw_content (markdown) + advanced + answer.

Показывает, что Tavily умеет отдать поиск И тело страниц в одном вызове (бакет A+B).

    uv run python -m dev.bench.web_search.tavily.run_search_raw
"""

from __future__ import annotations

from dev.bench.web_search.tavily import client
from dev.bench.web_search.tavily.constants import SEARCH_QUERY


def main() -> None:
    payload = {
        "query": SEARCH_QUERY,
        "search_depth": "advanced",
        "max_results": 3,
        "include_answer": True,
        "include_raw_content": "markdown",
    }
    data = client.call("search", payload)
    path = client.save("search_raw", data)

    answer = data.get("answer") or ""
    print(f"response_time={data.get('response_time')}")
    print(f"answer[{len(answer)}]: {answer[:300]}")
    for i, r in enumerate(data.get("results", []), 1):
        raw = r.get("raw_content") or ""
        print(f"  {i}. raw_content[{len(raw)}] | {(r.get('title') or '')[:60]}")
        print(f"     {raw[:160].strip()}…")
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
