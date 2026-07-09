import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { listResearches, type ResearchListRow, type SortDir } from '../api'

// Список исследований. Фильтры — отдельные ref'ы; load() собирает params, пропуская
// пустые. Новые сверху (sortDir=desc по created_at).
export const useResearchesStore = defineStore('research-researches', () => {
  const query = ref('')
  const sortDir = ref<SortDir>('desc')
  const page = ref(1)
  const pageSize = ref(50)

  const items = ref<ResearchListRow[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const hasActiveFilters = computed(() => !!query.value)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await listResearches({
        query: query.value || undefined,
        sort_dir: sortDir.value,
        page: page.value,
        page_size: pageSize.value,
      })
      items.value = res.items
      total.value = res.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  function resetPage() {
    page.value = 1
  }

  function clearFilters() {
    query.value = ''
    resetPage()
  }

  return {
    query, sortDir, page, pageSize,
    items, total, loading, error,
    pageCount, hasActiveFilters,
    load, resetPage, clearFilters,
  }
})
