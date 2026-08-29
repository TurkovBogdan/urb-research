"""MCP-тулы справки — навыки, которые агент забирает перед работой, а не носит в контексте.

Два тула: каталог (имя + условие вызова, без текстов) и чтение — целиком или одним разделом.
Тексты лежат файлами в ``skills/`` и отдаются как есть; вся логика — в ``services/skills.py``.

Загрузку навыка ничем нельзя гарантировать: указание в описании конкурирует с уверенностью
модели, и клиент вправе его перевесить. Поэтому указатели стоят там, где справка нужна
(``body_add``/``body_edit`` и инструкции сервера), а на самом навыке ответственность не
заканчивается — то, что можно проверить, проверяется ошибкой тула.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.research.dto import AgentSkill, AgentSkillRow
from src.modules.research.services.skills import list_skills, read_skill

if TYPE_CHECKING:  # fork fastmcp — только backend (через mcp_server(ctx))
    from fastmcp import FastMCP


def register(mcp: "FastMCP") -> None:

    @mcp.tool()
    async def skills_list() -> list[AgentSkillRow]:
        """List the skills this server can teach you — name, when to use it, its sections.

        A skill is reference material the server keeps for you: the rules of a format it
        accepts, written out once so you do not have to guess them. Anything this app renders in
        its own way — body markup, diagrams — has a skill here, and reading it is the difference
        between output the app renders and output it silently mangles.

        Cheap to call — the catalogue carries no skill text, only names and the condition each
        one is for. Read one with skill_get(skill_name).
        """
        return [AgentSkillRow.model_validate(skill) for skill in list_skills()]

    @mcp.tool()
    async def skill_get(skill_name: str, section: str | None = None) -> AgentSkill:
        """Return a skill — the whole guide, or one section of it.

        Read it BEFORE the work it covers, not after the result comes back wrong. Your own
        knowledge of a format is not enough here: what matters is how THIS app renders it, and
        that is what the skill describes.

        The answer carries the skill's `sections`: take the whole guide first, then pull the
        section for the branch you are actually on.

        Args:
            skill_name: The skill to read — a name from skills_list.
            section: One name from that skill's `sections`; omit for the whole guide.
        """
        return AgentSkill.model_validate(read_skill(skill_name, section))
