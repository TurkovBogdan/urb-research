import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { listPages, type WebSearchPageRow, type PageStatus, type SortDir } from '../api'

// Список страниц (web_search_page). Текстовый фильтр — по url. Сортировка серверная
// по клику на заголовок (sortBy=колонка, sortDir=направление); по умолчанию новые сверху.
export const usePagesStore = defineStore('web_search-pages', () => {
  const query = ref('')
  const status = ref<PageStatus | null>(null)
  const domain = ref<string | null>(null)
  const sortBy = ref('created_at')
  const sortDir = ref<SortDir>('desc')
  const page = ref(1)
  const pageSize = ref(50)

  const items = ref<WebSearchPageRow[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const hasActiveFilters = computed(
    () => !!query.value || !!status.value || !!domain.value,
  )

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await listPages({
        query: query.value || undefined,
        status: status.value,
        domain: domain.value,
        sort_by: sortBy.value,
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
    status.value = null
    domain.value = null
    resetPage()
  }

  return {
    query, status, domain, sortBy, sortDir, page, pageSize,
    items, total, loading, error,
    pageCount, hasActiveFilters,
    load, resetPage, clearFilters,
  }
})
