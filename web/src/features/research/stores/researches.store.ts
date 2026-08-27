import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { listResearches, type ResearchListRow, type ResearchSortBy, type SortDir } from '../api'

// Список исследований. Фильтры — отдельные ref'ы; load() собирает params, пропуская
// пустые. Новые сверху (sortDir=desc по created_at).
//
// Полка приходит с двух сторон, и это разные роли:
//   groupCode  — контекст страницы, из адреса (/research/researches/GROUP@…). Не сбрасывается
//                clearFilters и не считается активным фильтром — страница полки и есть полка.
//   groupFilter — выбор человека в панели фильтров реестра. Обычный фильтр.
// Одновременно они не встречаются (это разные страницы), а контекст сильнее выбора.
export const useResearchesStore = defineStore('research-researches', () => {
  const query = ref('')
  const groupCode = ref<string | null>(null)
  const groupFilter = ref<string | null>(null)
  const sortBy = ref<ResearchSortBy>('created_at')
  const sortDir = ref<SortDir>('desc')
  const page = ref(1)
  const pageSize = ref(50)

  const items = ref<ResearchListRow[]>([])
  const total = ref(0)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
  const hasActiveFilters = computed(() => !!query.value || groupFilter.value !== null)

  async function load() {
    loading.value = true
    error.value = null
    try {
      const res = await listResearches({
        query: query.value || undefined,
        group_code: groupCode.value ?? groupFilter.value ?? undefined,
        sort_by: sortBy.value,
        sort_dir: sortDir.value,
        page: page.value,
        page_size: pageSize.value,
      })
      items.value = res.items
      total.value = res.total
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  function resetPage() {
    page.value = 1
  }

  function clearFilters() {
    query.value = ''
    groupFilter.value = null
    resetPage()
  }

  return {
    query, groupCode, groupFilter, sortBy, sortDir, page, pageSize,
    items, total, loading, error,
    pageCount, hasActiveFilters,
    load, resetPage, clearFilters,
  }
})
