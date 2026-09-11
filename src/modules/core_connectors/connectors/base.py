"""Базовый коннектор: паспорт полей + баланс + проверка; ниже — HTTP-обвязка.

От коннектора требуется немного: объявить паспорт (``FIELDS`` ядровыми классами полей,
``REQUIRED`` — без чего доступ не считается настроенным) и уметь отдать баланс. Доменная
работа (поиск, инференс, скрейп) добавляется методами по надобности — она нужна
потребителю, а не модулю доступов.

Экземпляр коннектора **связан с записью доступа**: значения приходят конструктором
(``AccessValues``), а не читаются из глобальных настроек по именам полей. Отсюда два
свойства даром — опечатка в имени поля невозможна (имени нет, есть само поле), а два
аккаунта одного сервиса были бы двумя экземплярами одного класса.

``HttpConnector`` добавляет общую HTTP-часть (склейка адреса, авторизация, таймаут,
единый ``_request``): все встроенные коннекторы ходят по HTTP. Отдельным файлом её нет
смысла держать, пока нет ни одного коннектора поверх сокета или локальной команды.
"""

from __future__ import annotations

import time
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import httpx

from src.core.settings import Field
from src.modules.core_connectors.connectors.passport import ConnectorBalance, ConnectorCheck

if TYPE_CHECKING:
    from src.modules.core_connectors.access.store import AccessValues


def failure_text(exc: Exception) -> str:
    """Короткая причина отказа для карточки сервиса.

    Многострочная трассировка httpx («For more information check…») в интерфейсе
    бесполезна: человеку нужен код ответа и хост, к которому не пустили.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code} от {exc.request.url.host}"
    if isinstance(exc, httpx.HTTPError):
        return f"Сервис недоступен: {type(exc).__name__}"
    return f"{type(exc).__name__}: {exc}"


class Connector(ABC):
    """Один внешний сервис: паспорт своих полей + обязательный баланс."""

    SERVICE: ClassVar[str]  # уникальный код в реестре
    NAME: ClassVar[str]
    DESCRIPTION: ClassVar[str] = ""
    GROUP: ClassVar[str] = ""  # код группы справочника; пусто — «Прочее» на странице
    FIELDS: ClassVar[tuple[Field, ...]] = ()  # паспорт доступа: секреты и параметры
    REQUIRED: ClassVar[tuple[str, ...]] = ()  # без этих полей доступ «не настроен»
    HAS_BALANCE: ClassVar[bool] = True  # минимум, требуемый от коннектора

    def __init__(self, access: "AccessValues") -> None:
        self.access = access

    async def balance(self) -> ConnectorBalance:
        """Остаток/лимиты/расход одним DTO со списком метрик. Общая часть — гейт по
        ``HAS_BALANCE`` и связка «запросить → разобрать»; сам запрос и маппинг задаёт
        подкласс (разделены, чтобы маппинг проверялся тестом без сети)."""
        if not self.HAS_BALANCE:
            raise NotImplementedError(f"{self.NAME} не отдаёт баланс")
        return self._parse_balance(await self._fetch_balance())

    async def _fetch_balance(self) -> dict[str, Any]:
        """Сырой ответ балансового эндпойнта (подкласс с ``HAS_BALANCE``)."""
        raise NotImplementedError

    def _parse_balance(self, raw: dict[str, Any]) -> ConnectorBalance:
        """Маппинг сырого ответа в ``ConnectorBalance`` (подкласс с ``HAS_BALANCE``)."""
        raise NotImplementedError

    async def check(self) -> ConnectorCheck:
        """Живая проверка доступа. По умолчанию — балансовый запрос как самый дешёвый
        из тех, что есть почти у каждого коннектора; переопределяется, если есть дешевле.

        Коннектор без баланса обязан дать свою пробу: иначе в карточке вместо диагноза
        появится «NotImplementedError», а это не ответ на вопрос «работает ли доступ».
        """
        if not self.HAS_BALANCE:
            return ConnectorCheck(
                ok=False, error=f"{self.NAME}: проверка не реализована (баланса у него нет)"
            )
        started = time.monotonic()
        try:
            result = await self.balance()
        except Exception as exc:  # noqa: BLE001 — проверка обязана вернуть диагноз, а не упасть
            return ConnectorCheck(ok=False, error=failure_text(exc))
        latency_ms = int((time.monotonic() - started) * 1000)
        if result.error:
            return ConnectorCheck(ok=False, latency_ms=latency_ms, error=result.error)
        return ConnectorCheck(ok=True, latency_ms=latency_ms)

    @classmethod
    def secret_keys(cls) -> frozenset[str]:
        """Ключи секретных полей паспорта — по ним шифруются и маскируются значения."""
        return frozenset(field.key for field in cls.FIELDS if field.is_secret())


class HttpConnector(Connector):
    """Коннектор поверх HTTP-API: адрес, авторизация Bearer, единый запрос."""

    BASE_URL: ClassVar[str]
    TIMEOUT: ClassVar[float] = 60.0
    KEY_FIELD: ClassVar[str] = "api_key"  # поле паспорта, из которого берётся токен

    @property
    def base_url(self) -> str:
        """Адрес сервиса: у облачных — константа класса, у локального демона — поле записи."""
        return self.BASE_URL

    def _auth_headers(self) -> dict[str, str]:
        """Заголовки авторизации. По умолчанию ``Authorization: Bearer``; подкласс
        переопределяет под свою схему (напр. заголовок с именем вендора вместо Bearer)."""
        return {"Authorization": f"Bearer {self.access.require(self.KEY_FIELD)}"}

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        base_url: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Запрос к сервису. ``base_url``/``headers`` переопределяются для второй
        поверхности того же вендора (напр. биллинг xAI на другом хосте и с другим ключом)."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.request(
                method,
                f"{base_url or self.base_url}{endpoint}",
                json=json,
                params=params,
                headers=headers or self._auth_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", endpoint, json=payload)


__all__ = ["Connector", "HttpConnector", "failure_text"]
