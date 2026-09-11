"""Динамический реестр коннекторов: что вообще бывает в этой установке.

Реестр хранит **классы**, а не экземпляры: экземпляр всегда связан с записью доступа и
рождается в фасаде. Регистрировать может любой модуль — своим ``configure()``, своим
``on_startup()`` или позже в runtime; состав виден следующему запросу без перезапуска.
Именно это требование и увело креды из статической схемы настроек в таблицу записей
(схемы регистрируются раньше любого ``configure()``).

Правила, которые реестр держит:
- ``owner`` — имя модуля-регистратора; едет в паспорт и объясняет, откуда взялся коннектор;
- перерегистрация того же кода **другим** классом или **чужим** модулем — ошибка, а не
  молчаливая замена: иначе чужой модуль незаметно перехватил бы чужие ключи;
- повтор той же пары (класс, владелец) — no-op: сборка приложения повторяется в тестах и
  при hot-reload, и это не попытка перехвата;
- снять регистрацию может только владелец;
- записи доступа переживают снятие: строки остаются, коннектор просто становится
  неизвестным реестру.

Единственное правило порядка: на сборке реестр нельзя **читать** — только пополнять. Пока
не отработали все ``configure()``, состав неполон, поэтому списки для формы и для настроек
потребителя строятся лениво, в момент запроса.
"""

from __future__ import annotations

from src.modules.core_connectors.connectors.base import Connector
from src.modules.core_connectors.connectors.passport import (
    ConnectorPassport,
    field_descriptors,
)
from src.modules.core_connectors.errors import UnknownConnector


class ConnectorsRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, type[Connector]] = {}
        self._owners: dict[str, str] = {}

    def register(self, connector: type[Connector], *, owner: str) -> None:
        service = connector.SERVICE
        registered = self._connectors.get(service)
        if registered is connector and self._owners[service] == owner:
            return
        if registered is not None:
            raise ValueError(
                f"Коннектор {service!r} уже зарегистрирован модулем {self._owners[service]!r}"
            )
        self._connectors[service] = connector
        self._owners[service] = owner

    def unregister(self, service: str, *, owner: str) -> None:
        if self._owners.get(service) != owner:
            raise ValueError(f"Коннектор {service!r} зарегистрирован не модулем {owner!r}")
        del self._connectors[service]
        del self._owners[service]

    def get(self, service: str) -> type[Connector]:
        try:
            return self._connectors[service]
        except KeyError:
            raise UnknownConnector(f"Неизвестный коннектор: {service!r}")

    def has(self, service: str) -> bool:
        return service in self._connectors

    def owner(self, service: str) -> str:
        self.get(service)
        return self._owners[service]

    def all(self) -> list[type[Connector]]:
        return [self._connectors[service] for service in sorted(self._connectors)]

    def services(self) -> list[str]:
        return sorted(self._connectors)

    def passport(self, service: str, *, is_set: frozenset[str] | None = None) -> ConnectorPassport:
        connector = self.get(service)
        return ConnectorPassport(
            service=connector.SERVICE,
            name=connector.NAME,
            description=connector.DESCRIPTION,
            group=connector.GROUP,
            owner=self._owners[service],
            has_balance=connector.HAS_BALANCE,
            fields=field_descriptors(connector.FIELDS, is_set=is_set),
        )

    def passports(self) -> list[ConnectorPassport]:
        return [self.passport(service) for service in self.services()]


connectors_registry = ConnectorsRegistry()


__all__ = ["ConnectorsRegistry", "connectors_registry"]
