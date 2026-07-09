import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getSourceQuery, type SourceQueryDetail } from '../api'

// Деталка поиска (source-query): сам поиск + найденные источники (в порядке запуска).
export const useQueryDetailStore = defineStore('research-query-detail', () => {
  const query = ref<SourceQueryDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const documents = computed(() => query.value?.documents ?? [])
  const keptDocuments = computed(() => documents.value.filter((d) => d.status === 'kept'))
  const otherDocuments = computed(() => documents.value.filter((d) => d.status !== 'kept'))

  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const data = await getSourceQuery(code)
      if (current !== code) return
      query.value = data
    } catch (e) {
      if (current !== code) return
      error.value = e instanceof Error ? e.message : String(e)
      query.value = null
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    query.value = null
    error.value = null
  }

  return { query, documents, keptDocuments, otherDocuments, loading, error, load, reset }
})
