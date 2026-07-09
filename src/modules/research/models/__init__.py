"""ORM-модели research. Импорт регистрирует таблицы в ``Base.metadata``."""

from src.modules.research.models.area import ResearchArea
from src.modules.research.models.note import ResearchNote
from src.modules.research.models.research import Research
from src.modules.research.models.source_document import ResearchSourceDocument
from src.modules.research.models.source_query import ResearchSourceQuery

__all__ = [
    "Research",
    "ResearchArea",
    "ResearchSourceQuery",
    "ResearchSourceDocument",
    "ResearchNote",
]
