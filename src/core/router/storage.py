"""Зона ``storage`` — отдача файлов от корня (монтируется на ``/storage``).

Параллель ``src/core/router/internal.py``, но префикс — корневой ``/storage`` (не
``/internal/...``): клиент обращается к файлу по «чистому» URL, пригодному для
``<img src>`` и прямых ссылок. Состав — под-роутеры модулей (``Module.storage_router``);
защита — зон-guard с умолчанием ``STORAGE_DEFAULT_GUARDS`` (``auth`` — сессия проекта).

Только ``protected`` ходит через backend (проверка прав → ответ X-Accel-Redirect,
nginx стримит байты сам). ``public`` отдаёт nginx напрямую с диска, до backend не
доходит; ``private`` наружу закрыт (nginx ``deny all``).

Зона строится СВЕЖЕЙ на каждый ``create_app`` (как internal) — без синглтона.
"""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter

from src.core.module import Module

STORAGE_PREFIX = "/storage"
# Чистое ядро без auth-модуля — умолчание встроенный ``allow_all`` (см. INTERNAL_DEFAULT_GUARDS).
STORAGE_DEFAULT_GUARDS = ["allow_all"]


def build_storage_zone(modules: Sequence[Module]) -> APIRouter:
    """Свежий агрегатор зоны storage из ``storage_router`` модулей."""
    zone = APIRouter()
    for m in modules:
        if m.storage_router is not None:
            zone.include_router(
                m.storage_router, prefix=m.storage_router_prefix, tags=[m.name]
            )
    return zone


__all__ = ["STORAGE_DEFAULT_GUARDS", "STORAGE_PREFIX", "build_storage_zone"]
