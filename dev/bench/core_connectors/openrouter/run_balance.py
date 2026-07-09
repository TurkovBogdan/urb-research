"""Упрощённый шлюз OpenRouter для верстака: только баланс (без инференса).

Полный ``OpenRouterProvider`` из semaphore-core (чат-комплишены, роутинг, structured
output, каталог моделей) в коннекторы **не** тянем — для мониторинга нужен лишь остаток
кредитов. Здесь минимальный httpx-клиент: пробуем ``GET /api/v1/key`` (лимит/остаток/расход)
и исторический ``GET /api/v1/credits`` (total_credits/total_usage), смотрим реальную форму.

Ключ — из env ``OPENROUTER_API_KEY`` (у OpenRouter креды планируем держать в ENV на уровне
модуля коннекторов, не в runtime-настройках). Сырьё — в ``tmp/balance.json``.

    OPENROUTER_API_KEY=... uv run python -m dev.bench.core_connectors.openrouter.run_balance
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

BASE_URL = "https://openrouter.ai/api/v1"
OUT_DIR = Path(__file__).resolve().parent / "tmp"


class OpenRouterGateway:
    """Тонкий клиент к OpenRouter — только read-методы баланса. Auth — ``Bearer``."""

    def __init__(self, api_key: str, *, timeout: float = 30.0) -> None:
        self._key = api_key
        self._timeout = timeout

    async def _get(self, endpoint: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{BASE_URL}{endpoint}", headers={"Authorization": f"Bearer {self._key}"}
            )
            response.raise_for_status()
            return response.json()

    async def key_info(self) -> dict[str, Any]:
        """``GET /api/v1/key`` — лимит/остаток/расход ключа."""
        return await self._get("/key")

    async def credits(self) -> dict[str, Any]:
        """``GET /api/v1/credits`` — total_credits/total_usage (историческая поверхность)."""
        return await self._get("/credits")


async def _probe(label: str, coro: Any) -> dict[str, Any] | None:
    try:
        data = await coro
    except httpx.HTTPStatusError as exc:
        print(f"  {label}: HTTP {exc.response.status_code} — {exc.response.text[:120]}")
        return None
    except Exception as exc:  # noqa: BLE001 — бенч: показать ошибку и идти дальше
        print(f"  {label}: {type(exc).__name__}: {exc}")
        return None
    print(f"  {label}: keys = {sorted(data)}")
    return data


async def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY не задан в окружении")
    gw = OpenRouterGateway(key)
    bundle: dict[str, Any] = {}

    print("===== OpenRouter =====")
    key_info = await _probe("GET /api/v1/key", gw.key_info())
    if key_info is not None:
        bundle["key"] = key_info
        data = key_info.get("data") or {}
        print(
            f"  → usage={data.get('usage')} limit={data.get('limit')} "
            f"remaining={data.get('limit_remaining')} free_tier={data.get('is_free_tier')}"
        )

    credits = await _probe("GET /api/v1/credits", gw.credits())
    if credits is not None:
        bundle["credits"] = credits
        data = credits.get("data") or {}
        total, used = data.get("total_credits"), data.get("total_usage")
        balance = None if total is None or used is None else round(total - used, 4)
        print(f"  → total_credits={total} total_usage={used} balance={balance} USD")

    if bundle:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "balance.json"
        path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  saved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
