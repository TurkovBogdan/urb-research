"""Коннектор OpenAI: тонкий клиент к Admin Costs API — только расход (не инференс)."""

from src.modules.core_connectors.services.openai.gateway import OpenAIGateway

__all__ = ["OpenAIGateway"]
