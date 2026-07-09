"""Определить баланс/лимиты каждого сервиса живьём: снять сырой JSON read-эндпойнтов.

Дёргает read-only «сколько осталось»-поверхности всех коннекторов и складывает сырой
ответ в ``tmp/balance_<service>.json`` — чтобы увидеть фактическую форму (какие поля =
остаток кредитов, какие = лимиты плана/период). Ничего не тратит (только GET).

    uv run python -m dev.bench.core_connectors.run_balances
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

from dev.bench.core_connectors.xai.bootstrap import load_gateway_store
from src.core.database import close_database
from src.modules.core_connectors.registry import connectors_registry
from src.modules.core_connectors.services.firecrawl import FirecrawlGateway
from src.modules.core_connectors.services.tavily import TavilyGateway
from src.modules.core_connectors.services.xai import XaiGateway, XaiManagementGateway

OUT_DIR = Path(__file__).resolve().parent / "tmp"


async def _probe(label: str, call: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any] | None:
    """Вызвать один read-эндпойнт, вернуть JSON (или None при ошибке) и напечатать статус."""
    try:
        data = await call()
    except httpx.HTTPStatusError as exc:
        print(f"  {label}: HTTP {exc.response.status_code} — {exc.response.text[:120]}")
        return None
    except Exception as exc:  # noqa: BLE001 — бенч: любую ошибку зова показываем и идём дальше
        print(f"  {label}: {type(exc).__name__}: {exc}")
        return None
    print(f"  {label}: top-level keys = {sorted(data) if isinstance(data, dict) else type(data).__name__}")
    return data


def _save(service: str, payload: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"balance_{service}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  saved: {path}")


async def tavily() -> None:
    print("\n===== Tavily =====")
    gw = TavilyGateway()
    usage = await _probe("GET /usage", gw.usage)
    if usage is not None:
        _save("tavily", usage)


async def firecrawl() -> None:
    print("\n===== Firecrawl =====")
    gw = FirecrawlGateway()
    bundle: dict[str, Any] = {}
    credit = await _probe("GET /v2/team/credit-usage", gw.usage)
    if credit is not None:
        bundle["credit_usage"] = credit
    token = await _probe("GET /v2/team/token-usage", lambda: gw._request("GET", "/v2/team/token-usage"))
    if token is not None:
        bundle["token_usage"] = token
    queue = await _probe("GET /v2/team/queue-status", lambda: gw._request("GET", "/v2/team/queue-status"))
    if queue is not None:
        bundle["queue_status"] = queue
    if bundle:
        _save("firecrawl", bundle)


async def xai() -> None:
    print("\n===== xAI (inference api.x.ai) =====")
    gw = XaiGateway()
    bundle: dict[str, Any] = {}
    info = await _probe("GET /v1/api-key", gw.api_key_info)
    if info is not None:
        bundle["api_key"] = info
    models = await _probe("GET /v1/models", gw.models)
    if models is not None:
        bundle["models"] = models

    print("\n===== xAI Management (management-api.x.ai) =====")
    team_id = (info or {}).get("team_id")
    if not team_id:
        print("  team_id недоступен (нет inference-ключа) — management пропущен")
    else:
        mgmt = XaiManagementGateway()
        balance = await _probe(
            f"GET /v1/billing/teams/{team_id}/prepaid/balance",
            lambda: mgmt.prepaid_balance(team_id),
        )
        if balance is not None:
            bundle["prepaid_balance"] = balance
        limits = await _probe(
            f"GET /v1/billing/teams/{team_id}/postpaid/spending-limits",
            lambda: mgmt.spending_limits(team_id),
        )
        if limits is not None:
            bundle["spending_limits"] = limits

    if bundle:
        _save("xai", bundle)


async def registry() -> None:
    """Паспорт + баланс по всем коннекторам — через реестр (with_balance=True)."""
    print("\n===== ConnectorsRegistry.connectors(with_balance=True) =====")
    for view in await connectors_registry.connectors(with_balance=True):
        info, bal = view.info, view.balance
        print(f"  {info.service:10} {info.name} — {info.description} (enabled={info.enabled})")
        if bal is None:
            continue
        if bal.error:
            print(f"      баланс: ERROR {bal.error}")
        for m in bal.metrics:
            if m.amount is not None:
                print(f"      {m.label}: {m.amount} {m.currency}")
            else:
                print(f"      {m.label}: {m.used} / {m.total} {m.unit} ({m.used_percent}%)")


async def main() -> None:
    await load_gateway_store()
    try:
        await tavily()
        await firecrawl()
        await xai()
        await registry()
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
