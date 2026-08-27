"""Палитра иконок группы — фиксированный набор имён tabler.

Иконка группы не может быть произвольной строкой: фронт импортирует иконки tabler **компонентами**
(6147 штук, 71 МБ — рантайм-резолв по имени утащил бы в бандл весь пакет), поэтому имя должно
попасть в реестр, где для него есть явный импорт. Этот список — канонический источник такого
набора: бэк отдаёт его как палитру для пикера, фронт держит зеркальную мапу «имя → компонент».

Имена — kebab-форма без префикса ``Icon``, ровно как в каталоге на tabler.io и в именах файлов
``@tabler/icons/icons/outline/*.svg`` (по ним набор и сверялся). Порядок тематический, а не
алфавитный: пикер показывает палитру как есть, и рядом должны стоять близкие по смыслу иконки.

Значение колонки ``research_group.icon`` в БД **не** валидируется по этому набору: список нужен
двум сторонам сразу, и жёсткая проверка на бэке превратила бы расширение палитры в правку двух
файлов в двух языках. Незнакомое имя фронт рисует запасной иконкой.
"""

from __future__ import annotations

_SCIENCE_AND_TECH = (
    "atom",
    "math-function",
    "math-pi",
    "flask",
    "test-pipe",
    "microscope",
    "dna",
    "virus",
    "vaccine",
    "stethoscope",
    "planet",
    "satellite",
    "mountain",
    "world",
    "code",
    "terminal-2",
    "git-branch",
    "bug",
    "robot",
    "binary-tree",
    "database",
    "chart-histogram",
    "chart-pie",
    "server",
    "cloud-computing",
    "network",
    "shield-lock",
    "key",
    "fingerprint",
    "cpu",
    "device-laptop",
    "bolt",
    "battery",
    "solar-panel",
    "building-factory-2",
    "cube",
    "vector-bezier",
    "ruler-measure",
    "gauge",
    "scale",
)

_BUSINESS_AND_LIFE = (
    "briefcase",
    "target-arrow",
    "presentation-analytics",
    "coins",
    "pig-money",
    "building-bank",
    "shopping-cart",
    "building-store",
    "tag",
    "speakerphone",
    "gavel",
    "license",
    "school",
    "books",
    "news",
    "microphone",
    "messages",
    "mail",
    "palette",
    "brush",
    "music",
    "camera",
    "feather",
    "notebook",
    "article",
    "building-skyscraper",
    "hammer",
    "crane",
    "truck-delivery",
    "ship",
    "plane",
    "compass",
    "tools-kitchen-2",
    "wheat",
    "tractor",
    "barbell",
    "ball-football",
    "home",
    "tree",
    "paw",
    "flower",
    "device-gamepad-2",
    "masks-theater",
    "users-group",
    "building-castle",
)

_ABSTRACT_MARKERS = (
    "folder",
    "box",
    "file-text",
    "notes",
    "book-2",
    "bookmark",
    "star",
    "flag",
    "pin",
    "archive",
    "search",
    "telescope",
    "bulb",
    "brain",
    "puzzle",
    "trophy",
    "rocket",
    "calendar",
    "clock",
    "hourglass",
    "route",
    "timeline",
    "sitemap",
    "tools",
    "hexagon",
    "diamond",
    "cloud",
    "sun",
    "mood-smile",
    "heart",
    "grid-dots",
    "layers-linked",
    "package",
    "stack-2",
    "category",
)

GROUP_ICONS: tuple[str, ...] = _SCIENCE_AND_TECH + _BUSINESS_AND_LIFE + _ABSTRACT_MARKERS


def group_icons() -> list[str]:
    """Палитра иконок группы в порядке показа."""
    return list(GROUP_ICONS)


__all__ = ["GROUP_ICONS", "group_icons"]
