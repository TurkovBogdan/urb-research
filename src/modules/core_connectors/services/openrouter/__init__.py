"""Коннектор OpenRouter: тонкий клиент к API — только баланс/лимиты ключа."""

from src.modules.core_connectors.services.openrouter.gateway import OpenRouterGateway

__all__ = ["OpenRouterGateway"]
