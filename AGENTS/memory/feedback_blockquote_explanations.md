---
name: feedback_blockquote_explanations
description: "User wants explanatory/definitional asides formatted as `>` blockquotes — in chat replies and in research notes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cf027c02-eb3e-4d8e-bbce-ddfc232a1885
---

Оформляй **пояснения** (определения, «что это такое», оговорки-каверзы, обоснования «почему») цитатой Markdown `>` — и в ответах в чате, и в телах заметок urb-research (NOTE@/RESEARCH@/AREA@).

**Why:** визуально отделяет пояснительный текст от основного содержания (шагов плана, выводов, действий).

**How to apply:** заворачивай в `>` только чисто пояснительные абзацы (определения терминов, каверзы-предпосылки, «почему так»); НЕ заворачивай шаги плана, чек-листы, списки действий — они остаются обычным текстом/списками. В заметках правь точечно через `body_edit replace`, не переписывая всю заметку. Пример: блок «Что такое УКЭП» в [[NOTE-ip-chelyabinsk-plan]] обёрнут в `>`.
