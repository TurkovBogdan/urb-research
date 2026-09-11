"""Справочник групп: чем внешний сервис является по своей природе.

Группа отвечает на вопрос «что это за сервис» (поисковый API, скрапер, провайдер моделей),
а не «зачем он нам сегодня»: роль в конвейере у вендора бывает не одна (Firecrawl и ищет, и
забирает страницы) и меняется вместе с настройками, природа сервиса — нет.

Справочник закрытый и лежит в коде рядом с реестром: группа — это способ разложить карточки
на странице, а не пользовательская сущность. Группа у коннектора **одна и может быть пустой** —
незнакомый или пустой код интерфейс сводит в «Прочее», поэтому чужой модуль со своей группой
ничего не ломает.

Тексты — русские литералы, переводятся на фронте по опознанию (``core_connectors.group.<code>``),
как имена полей настроек; своей системы i18n на бэке нет. ``icon`` — kebab-имя tabler: превратить
его в рисунок умеет зеркальный реестр фронта (``web/src/shared/icons.ts``), потому что иконки
попадают в бандл только явными импортами.

Порядок кортежа — порядок групп на странице.
"""

from __future__ import annotations

from pydantic import BaseModel

GROUP_SEARCH = "search"
GROUP_SCRAPING = "scraping"
GROUP_MODELS = "models"


class ConnectorGroup(BaseModel):
    code: str
    name: str
    description: str
    icon: str  # kebab-имя tabler из зеркального реестра фронта


CONNECTOR_GROUPS: tuple[ConnectorGroup, ...] = (
    ConnectorGroup(
        code=GROUP_SEARCH,
        name="Поиск",
        description="Поисковые API: по запросу отдают ссылки.",
        icon="search",
    ),
    ConnectorGroup(
        code=GROUP_SCRAPING,
        name="Скрапинг",
        description="Обход сайтов и извлечение содержимого страниц.",
        icon="sitemap",
    ),
    ConnectorGroup(
        code=GROUP_MODELS,
        name="Модели",
        description="Провайдеры языковых моделей и шлюзы к ним.",
        icon="brain",
    ),
)

_BY_CODE = {group.code: group for group in CONNECTOR_GROUPS}


def groups() -> list[ConnectorGroup]:
    return list(CONNECTOR_GROUPS)


def group(code: str) -> ConnectorGroup | None:
    return _BY_CODE.get(code)


__all__ = [
    "CONNECTOR_GROUPS",
    "GROUP_MODELS",
    "GROUP_SCRAPING",
    "GROUP_SEARCH",
    "ConnectorGroup",
    "group",
    "groups",
]
