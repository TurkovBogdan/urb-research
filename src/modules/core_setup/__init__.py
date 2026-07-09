"""core_setup — страница настроек, редактирующая ``.env`` и перезапускающая сервер.

Редактирует слой ENV/``Config`` (deploy-time: провайдер БД, коннект, порты, воркер);
изменения применяются рестартом процесса (``os.execv``). Отдельно от рантайм-настроек
(``core/settings`` → ``/core/settings``), которые применяются горячо.
"""

from src.modules.core_setup.module import CoreSetupModule

__all__ = ["CoreSetupModule"]
