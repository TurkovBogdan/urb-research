"""Типизированные отказы модуля доступов.

Потребитель просит доступ и получает либо коннектор, либо **различимую** причину отказа —
чтобы «не вставлен токен» не выглядело как сбой внешнего сервиса. Причин четыре, и каждая
ведёт к своему действию: завести коннектор в реестре, заполнить поля записи, включить
запись, разобраться с мастер-ключом.
"""

from __future__ import annotations


class ConnectorsError(Exception):
    """Общий предок отказов модуля — потребитель может ловить одним except."""


class UnknownConnector(ConnectorsError):
    """Коннектора с таким кодом нет в реестре (не зарегистрирован или снят)."""


class AccessNotConfigured(ConnectorsError):
    """Записи доступа нет либо не заполнены обязательные поля паспорта."""


class ConnectorDisabled(ConnectorsError):
    """Запись доступа выключена пользователем."""


class AccessUndecryptable(ConnectorsError):
    """Значение не разворачивается: ключа нет, ключ не тот или шифртекст испорчен."""


__all__ = [
    "ConnectorsError",
    "UnknownConnector",
    "AccessNotConfigured",
    "ConnectorDisabled",
    "AccessUndecryptable",
]
