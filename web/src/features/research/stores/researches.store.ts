import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { RESEARCH_PAGE_SIZES } from '@/constants/lists'

import { listResearches, type ResearchListRow, type ResearchSortBy, type SortDir } from '../api'

/** Слои поиска поверх основы — то, что переключают кнопки в поле запроса. */
export interface SearchScopes {
  inBody: boolean
  inAreasAndNotes: boolean
  inSources: boolean
}

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
  // Слои стога поверх основы (название + описание, они в поиске всегда). Материал источников
  // выключен: он на порядок больше всего написанного руками, и включают его осознанно.
  const inBody = ref(true)
  const inAreasAndNotes = ref(true)
  const inSources = ref(false)
  const groupCode = ref<string | null>(null)
  const groupFilter = ref<string | null>(null)
  const sortBy = ref<ResearchSortBy>('created_at')
  const sortDir = ref<SortDir>('desc')
  const page = ref(1)
  const pageSize = ref(RESEARCH_PAGE_SIZES[0])

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
        in_body: inBody.value,
        in_areas_and_notes: inAreasAndNotes.value,
        in_sources: inSources.value,
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

  // Слои меняют стог, а не строку: с пустым запросом список и так не сужен, перезапрашивать
  // нечего. Страница сбрасывается — набор строк другой, и третья страница прежней выдачи к нему
  // отношения не имеет.
  function searchScopes(next: Partial<SearchScopes>) {
    if (next.inBody !== undefined) inBody.value = next.inBody
    if (next.inAreasAndNotes !== undefined) inAreasAndNotes.value = next.inAreasAndNotes
    if (next.inSources !== undefined) inSources.value = next.inSources
    if (!query.value.trim()) return
    resetPage()
    return load()
  }

  function clearFilters() {
    query.value = ''
    groupFilter.value = null
    resetPage()
  }

  return {
    query, inBody, inAreasAndNotes, inSources, groupCode, groupFilter, sortBy, sortDir,
    page, pageSize,
    items, total, loading, error,
    pageCount, hasActiveFilters,
    load, resetPage, searchScopes, clearFilters,
  }
})
