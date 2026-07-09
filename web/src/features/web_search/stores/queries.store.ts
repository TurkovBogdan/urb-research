import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  createQuery,
  listEngines,
  listQueries,
  type CreateQueryBody,
  type QueryRow,
  type QueryStatus,
  type SortDir,
} from '../api'

// Список запросов поиска (web_search_query). Фильтры — отдельные ref'ы; load()
// собирает params, пропуская пустые. Сортировка серверная по клику на заголовок
// (sortBy=колонка, sortDir=направление); по умолчанию новые сверху (created_at desc).
export const useQueriesStore = defineStore('web_search-queries', () => {
  const query = ref('')
  const status = ref<QueryStatus | null>(null)
  const searchEngine = ref<string | null>(null)
  const sortBy = ref('created_at')
  const sortDir = ref<SortDir>('desc')
  const page = ref(1)
  const pageSize = ref(50)

  const items = ref<QueryRow[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Движки для формы создания (грузятся один раз): доступные коды по ролям + дефолты.
  const engines = ref<{
    search: string[]
    fetch: string[]
    searchDefault: string
    fetchDefault: string
  } | null>(null)
  const creating = ref(false)

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const hasActiveFilters = computed(
    () => !!query.value || !!status.value || !!searchEngine.value,
  )

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await listQueries({
        query: query.value || undefined,
        status: status.value,
        search_engine: searchEngine.value,
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

  async function loadEngines() {
    if (engines.value) return
    const info = await listEngines()
    engines.value = {
      search: info.search,
      fetch: info.fetch,
      searchDefault: info.search_default,
      fetchDefault: info.fetch_default,
    }
  }

  // Fire-and-forget: бэк ставит поиск в фон (клиент не ждёт), затем обновляем список.
  async function create(body: CreateQueryBody) {
    creating.value = true
    try {
      await createQuery(body)
      resetPage()
      await load()
    } finally {
      creating.value = false
    }
  }

  function resetPage() {
    page.value = 1
  }

  function clearFilters() {
    query.value = ''
    status.value = null
    searchEngine.value = null
    resetPage()
  }

  return {
    query, status, searchEngine, sortBy, sortDir, page, pageSize,
    items, total, loading, error,
    engines, creating,
    pageCount, hasActiveFilters,
    load, loadEngines, create, resetPage, clearFilters,
  }
})
