"""Имя файла архива из названия исследования.

Название — человеческий текст: в нём бывают слэши, двоеточия, кавычки, эмодзи, перевод строки
и точка в конце. Файл при этом ложится на чужую файловую систему, поэтому имя обеззараживается
до общего знаменателя Windows и POSIX, а от исследования остаётся ровно его название — так
просил владелец.
"""

from __future__ import annotations

import re

from src.modules.research.transfer.constants import ARCHIVE_EXTENSION

# Разделители путей и символы, запрещённые в именах файлов Windows, плюс управляющие.
_UNSAFE = re.compile(r'[\x00-\x1f<>:"/\\|?*]+')
_SPACES = re.compile(r"\s+")

# Длина считается по code points, а не по байтам: в UTF-8 кириллица весит вдвое, и байтовый
# предел резал бы русские названия вдвое короче английских.
MAX_STEM_LENGTH = 80


def archive_file_name(title: str, code: str) -> str:
    """``<обеззараженное название>.urch``; пустой остаток — ``research-<код>.urch``."""
    stem = _SPACES.sub(" ", _UNSAFE.sub("-", title)).strip()
    # Windows не открывает файл, имя которого кончается точкой или пробелом.
    stem = stem[:MAX_STEM_LENGTH].rstrip(" .")
    # Название из одних запрещённых символов превращается в частокол дефисов: связи с
    # исследованием в таком имени нет, и код опознаётся лучше, чем «-».
    if not stem.strip("-. "):
        stem = ""
    return f"{stem or f'research-{code}'}{ARCHIVE_EXTENSION}"


__all__ = ["MAX_STEM_LENGTH", "archive_file_name"]
