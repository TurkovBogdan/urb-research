"""Чтение значений записи доступа: единственный путь от строки к рабочему токену.

Между таблицей и всем остальным стоит один сервис — ``AccessStore``. Он читает строку (по
идентификатору или по признаку «по умолчанию для коннектора»), разворачивает значения,
держит кеш по записи и считает статус **без единого сетевого вызова**. Вызывающий про
шифртекст не знает вовсе.

Отказ типизирован и различим: записи нет или пусты обязательные поля —
``AccessNotConfigured``, запись выключена — ``ConnectorDisabled``, значение не
разворачивается — ``AccessUndecryptable``. Смысл разделения прикладной: пользователь,
забывший вставить токен, должен видеть «не настроено», а не отказ внешнего сервиса.

Отдаёт store не словарь, а ``AccessValues`` — обёртку с маскирующим ``__repr__``. Это не
косметика: именно через отладочный вывод и трассировку исключения секрет утекает мимо
всего шифрования — значение уже расшифровано и лежит в памяти, а печатает его случайная
строка отладки.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.modules.core_connectors.access import crud, crypto
from src.modules.core_connectors.access.model import (
    ACCESS_STATUS_DISABLED,
    ACCESS_STATUS_OK,
    ACCESS_STATUS_UNCONFIGURED,
    ACCESS_STATUS_UNDECRYPTABLE,
    AccessStatus,
    CoreConnectorsAccess,
)
from src.modules.core_connectors.connectors.registry import connectors_registry
from src.modules.core_connectors.errors import (
    AccessNotConfigured,
    AccessUndecryptable,
    ConnectorDisabled,
)


@dataclass(frozen=True)
class AccessValues:
    """Развёрнутые значения одной записи. Секреты наружу печатаются только как ``***``."""

    access_id: int
    service: str
    values: dict[str, str] = field(default_factory=dict)
    secret_keys: frozenset[str] = frozenset()

    def get(self, key: str) -> str | None:
        return self.values.get(key) or None

    def require(self, key: str) -> str:
        value = self.get(key)
        if value is None:
            raise AccessNotConfigured(f"{self.service}: не заполнено поле {key!r}")
        return value

    def __repr__(self) -> str:
        shown = {
            key: ("***" if key in self.secret_keys else value)
            for key, value in self.values.items()
        }
        return f"AccessValues(service={self.service!r}, id={self.access_id}, values={shown})"


class AccessStore:
    """Чтение значений и статуса записи, с кешем по записи."""

    def __init__(self) -> None:
        self._cache: dict[int, AccessValues] = {}

    async def values(self, access_id: int) -> AccessValues:
        """Развёрнутые значения записи. Выключенная запись и незаполненные обязательные
        поля — типизированный отказ, а не пустые значения."""
        cached = self._cache.get(access_id)
        if cached is not None:
            return cached
        row = await crud.access_get(access_id)
        if row is None:
            raise AccessNotConfigured(f"Записи доступа {access_id} нет")
        values = self._unseal(row)
        self._cache[access_id] = values
        return values

    async def default_values(self, service: str) -> AccessValues:
        """Значения записи по умолчанию для коннектора."""
        row = await crud.access_default_for(service)
        if row is None:
            raise AccessNotConfigured(f"{service}: нет записи доступа")
        return await self.values(row.id)

    async def status(self, access_id: int) -> AccessStatus:
        """Диагноз записи без сети: выключено → не настроено → не расшифровывается → готово."""
        row = await crud.access_get(access_id)
        if row is None:
            return AccessStatus(status=ACCESS_STATUS_UNCONFIGURED, detail="Подключения нет")
        return self.row_status(row)

    def row_status(self, row: CoreConnectorsAccess) -> AccessStatus:
        """Тот же диагноз по уже прочитанной строке — списку не нужен второй проход в базу."""
        if not row.enabled:
            return AccessStatus(status=ACCESS_STATUS_DISABLED, detail="Подключение выключено")
        try:
            values = self._unseal(row)
        except AccessUndecryptable as exc:
            return AccessStatus(status=ACCESS_STATUS_UNDECRYPTABLE, detail=str(exc))
        except Exception as exc:  # noqa: BLE001 — коннектор снят с регистрации и т.п.
            return AccessStatus(status=ACCESS_STATUS_UNCONFIGURED, detail=str(exc))
        missing = self._missing_required(row.connector, values)
        if missing:
            return AccessStatus(
                status=ACCESS_STATUS_UNCONFIGURED,
                detail=f"Не заполнено: {', '.join(missing)}",
            )
        return AccessStatus(status=ACCESS_STATUS_OK)

    def invalidate(self, access_id: int) -> None:
        """Сбросить кеш записи — вызывается после любой записи в неё."""
        self._cache.pop(access_id, None)

    def clear(self) -> None:
        self._cache.clear()

    def _unseal(self, row: CoreConnectorsAccess) -> AccessValues:
        connector_cls = connectors_registry.get(row.connector)
        secret_keys = connector_cls.secret_keys()
        stored: dict[str, Any] = dict(row.values or {})
        data_key = (
            crypto.unwrap_data_key(row.data_key, row.key_version or "")
            if row.data_key
            else None
        )
        values: dict[str, str] = {}
        for key, value in stored.items():
            if key in secret_keys and crypto.is_encrypted(str(value)):
                if data_key is None:
                    raise AccessUndecryptable(
                        f"{row.connector}: значение {key!r} зашифровано, а ключа записи нет"
                    )
                values[key] = crypto.decrypt_value(
                    str(value), data_key=data_key, access_id=row.id, field_key=key
                )
            else:
                values[key] = str(value)
        return AccessValues(
            access_id=row.id,
            service=row.connector,
            values=values,
            secret_keys=secret_keys,
        )

    @staticmethod
    def _missing_required(service: str, values: AccessValues) -> list[str]:
        connector_cls = connectors_registry.get(service)
        return [key for key in connector_cls.REQUIRED if values.get(key) is None]

    async def ready_values(self, row: CoreConnectorsAccess) -> AccessValues:
        """Значения записи, готовой к работе; иначе — отказ с точной причиной."""
        if not row.enabled:
            raise ConnectorDisabled(f"{row.connector}: запись доступа выключена")
        values = await self.values(row.id)
        missing = self._missing_required(row.connector, values)
        if missing:
            raise AccessNotConfigured(f"{row.connector}: не заполнено {', '.join(missing)}")
        return values


access_store = AccessStore()


__all__ = ["AccessValues", "AccessStore", "access_store"]
