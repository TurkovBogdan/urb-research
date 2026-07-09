import { ref } from 'vue'
import { defineStore } from 'pinia'

import { getArea, listAreaQueries, type AreaDetail, type SourceQueryRow } from '../api'

// Деталка области: скан + бриф (objective/scope/expectations) + синтез (body) + её поиски.
export const useAreaDetailStore = defineStore('research-area-detail', () => {
  const area = ref<AreaDetail | null>(null)
  const queries = ref<SourceQueryRow[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const [areaData, queryRows] = await Promise.all([getArea(code), listAreaQueries(code)])
      if (current !== code) return
      area.value = areaData
      queries.value = queryRows
    } catch (e) {
      if (current !== code) return
      error.value = e instanceof Error ? e.message : String(e)
      area.value = null
      queries.value = []
    } finally {
      if (current === code) loading.value = false
    }
  }

  function reset() {
    area.value = null
    queries.value = []
    error.value = null
  }

  return { area, queries, loading, error, load, reset }
})
