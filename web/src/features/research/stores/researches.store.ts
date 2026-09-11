import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { DEFAULT_PAGE_SIZE } from '@/constants/pagination'
import { useUiStateStore } from '@/stores/ui-state'

import {
  listResearches,
  resolveResearchSortBy,
  resolveSortDir,
  type ResearchListRow,
  type ResearchSortBy,
  type SortDir,
} from '../api'

/** Слои поиска поверх основы — то, что переключают кнопки в поле запроса. */
export interface SearchScopes {
  inBody: boolean
  inAreasAndNotes: boolean
  inSources: boolean
}

// Список исследований. Фильтры — отдельные ref'ы; load() собирает params, пропуская
// пустые. Порядок стор не держит — он лежит в `ui-state` и переживает перезагрузку вкладки.
//
// Полка приходит с двух сторон, и это разные роли:
//   groupCode  — контекст страницы, из адреса (/research/researches/GROUP@…). Не сбрасывается
//                clearFilters и не считается активным фильтром — страница полки и есть полка.
//   groupFilter — выбор человека в панели фильтров реестра. Обычный фильтр.
// Одновременно они не встречаются (это разные страницы), а контекст сильнее выбора.
export const useResearchesStore = defineStore('research-researches', () => {
  const query = ref('')
  // Слои стога поверх основы (название + описание, они в поиске всегда). Все выключены: поиск по
  // умолчанию отвечает на «как называлось», и это самый частый вопрос. Каждый слой добавляет к
  // стогу материал, которого на экране не видно, — включают их осознанно, кнопками в самом поле.
  const inBody = ref(false)
  const inAreasAndNotes = ref(false)
  const inSources = ref(false)
  const groupCode = ref<string | null>(null)
  const groupFilter = ref<string | null>(null)
  // Порядок список не держит, а одалживает: он переживает перезагрузку вкладки, и его дом —
  // хранилище состояния интерфейсов. Наружу стор отдаёт те же две ручки, что и раньше.
  const ui = useUiStateStore()
  const sortBy = computed<ResearchSortBy>({
    get: () => resolveResearchSortBy(ui.researchSort.by),
    set: (value) => { ui.researchSort.by = value },
  })
  const sortDir = computed<SortDir>({
    get: () => resolveSortDir(ui.researchSort.dir),
    set: (value) => { ui.researchSort.dir = value },
  })
  const page = ref(1)
  const pageSize = ref(DEFAULT_PAGE_SIZE)

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
