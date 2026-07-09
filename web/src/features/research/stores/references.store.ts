import { ref } from 'vue'
import { defineStore } from 'pinia'

import { resolveReferences } from '../api'

/**
 * Кэш «код сущности (TYPE@hash) → заголовок» для разрешения ссылок в телах.
 * Накапливается между страницами (дедуп по коду). `ensure(codes)` дозапрашивает только
 * отсутствующие; резолвнутый без заголовка кладётся как `''` (не перезапрашиваем).
 */
export const useReferencesStore = defineStore('research-references', () => {
  const labels = ref<Record<string, string>>({})
  const inflight = new Set<string>()

  async function ensure(codes: string[]): Promise<void> {
    const missing = [...new Set(codes)].filter(
      (c) => !(c in labels.value) && !inflight.has(c),
    )
    if (missing.length === 0) return
    missing.forEach((c) => inflight.add(c))
    try {
      const resolved = await resolveReferences(missing)
      const next = { ...labels.value }
      for (const r of resolved) next[r.code] = r.title ?? ''
      for (const c of missing) if (!(c in next)) next[c] = '' // unresolved — mark empty, don't refetch
      labels.value = next
    } finally {
      missing.forEach((c) => inflight.delete(c))
    }
  }

  return { labels, ensure }
})
