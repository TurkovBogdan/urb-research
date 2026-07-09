"""Сравнение чистоты контента Firecrawl vs Tavily на одном наборе URL.

Берёт 19 URL из сохранённого ответа Tavily (search + include_raw_content), гоняет
каждый через Firecrawl ``/v2/scrape`` в чистом режиме (``onlyMainContent=true``) и
кладёт длины рядом с ``raw_content`` Tavily. Ключ Firecrawl читается из dev-настроек
(``core_modules_settings``), сеть — httpx, параллелизм — семафор.

    uv run python -m dev.bench.web_search.firecrawl.compare_scrape
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import statistics
from pathlib import Path
from typing import Any

import httpx

_ROOT = Path(__file__).resolve().parents[4]
_DEV_DB = _ROOT / "runtime" / "dev" / "app.sqlite3"
_TAVILY_DUMP = Path("/path/to/tavily_search_dump.txt")
_OUT = Path(__file__).resolve().parent / "tmp" / "firecrawl_scrape.json"
_SCRAPE_URL = "https://api.firecrawl.dev/v2/scrape"
_CONCURRENCY = 5
_TIMEOUT = 120.0


def firecrawl_key() -> str:
    con = sqlite3.connect(_DEV_DB)
    try:
        row = con.execute(
            "SELECT value FROM core_modules_settings WHERE module='core_connectors' AND key='firecrawl_api_key'"
        ).fetchone()
    finally:
        con.close()
    if not row or not row[0]:
        raise SystemExit("firecrawl_api_key не задан в dev-настройках")
    return row[0]


def tavily_results() -> list[dict[str, Any]]:
    data = json.loads(_TAVILY_DUMP.read_text(encoding="utf-8"))
    return data["results"]


async def scrape_one(
    client: httpx.AsyncClient, url: str, key: str, semaphore: asyncio.Semaphore
) -> dict[str, Any]:
    payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
    async with semaphore:
        try:
            response = await client.post(
                _SCRAPE_URL,
                json=payload,
                headers={"Authorization": f"Bearer {key}"},
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            markdown = (data.get("data") or {}).get("markdown")
            return {"url": url, "ok": True, "markdown": markdown, "error": None}
        except httpx.HTTPStatusError as exc:
            return {"url": url, "ok": False, "markdown": None, "error": f"HTTP {exc.response.status_code}"}
        except Exception as exc:  # noqa: BLE001 — любая ошибка фетча фиксируется как провал
            return {"url": url, "ok": False, "markdown": None, "error": type(exc).__name__}


async def main() -> None:
    key = firecrawl_key()
    results = tavily_results()
    urls = [r["url"] for r in results]
    tavily_raw_len = {r["url"]: (len(r["raw_content"]) if r.get("raw_content") else 0) for r in results}

    semaphore = asyncio.Semaphore(_CONCURRENCY)
    async with httpx.AsyncClient() as client:
        scraped = await asyncio.gather(*(scrape_one(client, u, key, semaphore) for u in urls))

    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(scraped, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'N':>2} | {'firecrawl':>18} | {'tavily raw':>10} | domain")
    print("-" * 72)
    fc_lengths: list[int] = []
    fc_present = fc_fail = 0
    for i, (url, item) in enumerate(zip(urls, scraped), 1):
        domain = url.split("://", 1)[-1].split("/", 1)[0]
        t_len = tavily_raw_len[url]
        if item["ok"] and item["markdown"]:
            fc_len = len(item["markdown"])
            fc_lengths.append(fc_len)
            fc_present += 1
            fc_cell = f"md={fc_len}"
        else:
            fc_fail += 1
            fc_cell = f"FAIL {item['error'] or 'empty'}"
        t_cell = f"raw={t_len}" if t_len else "NULL"
        print(f"{i:>2} | {fc_cell:>18} | {t_cell:>10} | {domain}")

    t_present = sum(1 for v in tavily_raw_len.values() if v)
    t_lengths = [v for v in tavily_raw_len.values() if v]
    print("-" * 72)
    print(f"Firecrawl: контент у {fc_present}/{len(urls)}, провалов {fc_fail}")
    if fc_lengths:
        print(f"  markdown длины: min={min(fc_lengths)} median={int(statistics.median(fc_lengths))} max={max(fc_lengths)}")
    print(f"Tavily:    raw_content у {t_present}/{len(urls)}")
    if t_lengths:
        print(f"  raw длины: min={min(t_lengths)} median={int(statistics.median(t_lengths))} max={max(t_lengths)}")
    print(f"saved: {_OUT}")


if __name__ == "__main__":
    asyncio.run(main())
