"""Сервис-коннекторы core_connectors: по папке на внешний сервис (тонкий коннектор к API).

``services/`` — раскладка файлов (по вендору: гейтвеи + их DTO), не домен. Домен —
«коннекторы»: реестр живёт в корне модуля (``core_connectors/registry.py``), read-DTO — в
``dto.py`` (``ConnectorInfo``/``ConnectorBalance``/``ConnectorView``).
"""

from src.modules.core_connectors.services.dto import (
    BalanceMetric,
    ConnectorBalance,
    ConnectorInfo,
    ConnectorView,
)

__all__ = ["ConnectorInfo", "BalanceMetric", "ConnectorBalance", "ConnectorView"]
