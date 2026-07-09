"""core_connectors — инфраструктурный модуль-коннектор к внешним API.

Даёт тонкие коннекторы к внешним сервисам (Tavily, Firecrawl, …) и хранит их
креды как runtime-настройки (секретные поля, правятся на ``/core/settings``).
Своего домена, таблиц и оркестрации нет: только доступ к API + хранение ключей.
Сервис = папка в ``services/``; доменную форму ответа строит потребитель, не коннектор.
"""

from src.modules.core_connectors.module import CoreConnectorsModule

__all__ = ["CoreConnectorsModule"]
