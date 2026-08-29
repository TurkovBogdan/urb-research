"""Каталог навыков — справка, которую агент забирает по требованию, а не носит в контексте.

Навык — папка ``skills/<name>/`` с файлом ``SKILL.md`` и необязательными разделами
``sections/<section>.md``. Первый уровень (имя + условие вызова) стоит десяток токенов,
тело приезжает только под задачу, раздел — только под ветку задачи.

Справка лежит файлами в самом модуле и версионируется тем же коммитом, что и код, который
описывает: разъехавшаяся справка вреднее отсутствующей, потому что агент считает её
авторитетной.

Имя навыка приходит от агента, поэтому путь из него не склеивается: открываем только те
папки, которые нашли на диске сами.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

_SKILL_FILE = "SKILL.md"
_SECTIONS_DIR = "sections"
_FRONTMATTER_FENCE = "---"


@dataclass(frozen=True)
class SkillSummary:
    """Строка каталога — всё, кроме текста."""

    name: str
    description: str
    sections: list[str]


@dataclass(frozen=True)
class SkillPage:
    """Прочитанный навык: тело целиком или один раздел (``section`` пуст у целого)."""

    name: str
    section: str
    description: str
    sections: list[str]
    text: str


def _skill_dirs() -> dict[str, Path]:
    if not SKILLS_DIR.is_dir():
        return {}
    return {
        candidate.name: candidate
        for candidate in sorted(SKILLS_DIR.iterdir())
        if (candidate / _SKILL_FILE).is_file()
    }


def _section_files(skill_dir: Path) -> dict[str, Path]:
    sections_dir = skill_dir / _SECTIONS_DIR
    if not sections_dir.is_dir():
        return {}
    return {section.stem: section for section in sorted(sections_dir.glob("*.md"))}


def _split_frontmatter(raw: str) -> tuple[str, str]:
    """Отделить ``description`` фронтматтера от тела; без фронтматтера — пустое описание."""
    if not raw.startswith(_FRONTMATTER_FENCE):
        return "", raw
    _, _, after_opening_fence = raw.partition("\n")
    frontmatter, closing_fence, body = after_opening_fence.partition(f"{_FRONTMATTER_FENCE}\n")
    if not closing_fence:
        return "", raw
    description = ""
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "description":
            description = value.strip()
    return description, body.lstrip("\n")


def _read_skill_file(skill_dir: Path) -> tuple[str, str]:
    return _split_frontmatter((skill_dir / _SKILL_FILE).read_text(encoding="utf-8"))


def list_skills() -> list[SkillSummary]:
    """Каталог навыков: имя, условие вызова, имена разделов — без текстов."""
    catalogue = []
    for name, skill_dir in _skill_dirs().items():
        description, _ = _read_skill_file(skill_dir)
        catalogue.append(
            SkillSummary(name=name, description=description, sections=list(_section_files(skill_dir)))
        )
    return catalogue


def read_skill(skill_name: str, section: str | None = None) -> SkillPage:
    """Вернуть навык целиком или один его раздел; неизвестное имя — ошибка со списком доступных."""
    skill_dirs = _skill_dirs()
    skill_dir = skill_dirs.get(skill_name)
    if skill_dir is None:
        available = ", ".join(skill_dirs) or "none"
        raise ValueError(f"Unknown skill {skill_name!r}. Available skills: {available}.")

    description, text = _read_skill_file(skill_dir)
    sections = _section_files(skill_dir)
    if section:
        section_file = sections.get(section)
        if section_file is None:
            known = ", ".join(sections) or "none — call it without a section"
            raise ValueError(f"Skill {skill_name!r} has no section {section!r}. Sections: {known}.")
        text = section_file.read_text(encoding="utf-8")

    return SkillPage(
        name=skill_name,
        section=section or "",
        description=description,
        sections=list(sections),
        text=text,
    )


__all__ = ["SKILLS_DIR", "SkillPage", "SkillSummary", "list_skills", "read_skill"]
