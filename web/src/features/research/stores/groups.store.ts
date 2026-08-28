import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  listGroups,
  listResearches,
  searchGroups,
  UNGROUPED_CODE,
  type GroupListRow,
  type GroupSortBy,
  type SortDir,
} from '../api'
import { useGroupCatalogStore } from './group-catalog.store'

// Полки реестра. Список короткий и без пагинации, а порядок задаёт бэк (сортировка — его белый
// список ключей), поэтому стор сам ничего не сортирует: он лишь помнит выбор и перезапрашивает.
//
// Псевдо-полка «Без группы» строкой в БД не существует: её счётчик — это total того же списка
// исследований с фильтром «не разложенные», поэтому берётся вторым запросом рядом со списком.
//
// Поиск сужает набор карточек, а не подменяет его: полки лежат в `items` целиком, а совпавшие
// коды приходят отдельно и работают маской (`visibleItems`). Поэтому сброс строки поиска ничего
// не перезагружает, а счётчик на карточке остаётся счётчиком полки, а не находок.
export const useGroupsStore = defineStore('research-groups', () => {
  const catalog = useGroupCatalogStore()

  const items = ref<GroupListRow[]>([])
  const ungroupedCount = ref(0)
  const loading = ref(true)
  const error = ref<unknown>(null)

  // Умолчание зеркалит бэк: сверху та полка, где недавно работали.
  const sortBy = ref<GroupSortBy>('research_updated_at')
  const sortDir = ref<SortDir>('desc')

  const query = ref('')
  // Глубина поиска: включено — стог считает и весь текст лежащих на полке исследований,
  // выключено — только текст самих полок. Умолчание совпадает с прежним поведением.
  const inResearches = ref(true)
  const searching = ref(false)
  // null — поиска нет, показываем всё; иначе маска: коды совпавших полок + признак «Без группы».
  const matches = ref<{ codes: Set<string>; ungrouped: boolean } | null>(null)

  const visibleItems = computed(() => {
    const mask = matches.value
    return mask === null ? items.value : items.value.filter((g) => mask.codes.has(g.code))
  })

  const ungroupedVisible = computed(() => matches.value?.ungrouped ?? true)

  const isEmpty = computed(() => !visibleItems.value.length && !ungroupedVisible.value)

  async function load() {
    error.value = null
    try {
      // `report: false` — отказ чтения раздела показывает сама страница (SectionError);
      // тост поверх него был бы вторым сообщением об одном и том же.
      const [groups, ungrouped] = await Promise.all([
        listGroups({ sort_by: sortBy.value, sort_dir: sortDir.value }, { report: false }),
        listResearches({ group_code: UNGROUPED_CODE, page_size: 1 }, { report: false }),
      ])
      items.value = groups
      ungroupedCount.value = ungrouped.total
      // Полки уже здесь — справочник забирает их без второго запроса; он же переживёт уход
      // со страницы и накормит окна и фильтры (`group-catalog.store`).
      catalog.adopt(groups)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  // Пустая строка снимает маску, не спрашивая бэк: «ничего не набрано» — это отсутствие поиска,
  // а не поиск с пустым результатом.
  async function search(text: string) {
    query.value = text
    if (!text.trim()) {
      matches.value = null
      searching.value = false
      return
    }
    searching.value = true
    try {
      const found = await searchGroups(text, { in_researches: inResearches.value })
      // Ответ мог прийти после того, как строку успели сменить: применяем только свежий.
      if (query.value !== text) return
      matches.value = { codes: new Set(found.codes), ungrouped: found.ungrouped }
    } catch {
      // Об отказе уже сказал тост клиента. Маску снимаем: показать всё честнее, чем оставить
      // выдачу от предыдущей строки — она выглядела бы ответом на текущую.
      if (query.value === text) matches.value = null
    } finally {
      if (query.value === text) searching.value = false
    }
  }

  // Глубина меняет стог, а не строку: перезапрашивать есть смысл только с непустым запросом,
  // иначе маски и так нет.
  function searchDeeper(enabled: boolean) {
    inResearches.value = enabled
    if (query.value.trim()) return search(query.value)
  }

  // Порядок задаёт бэк, поэтому смена ключа — это перезапрос, а не пересортировка на месте.
  // Маска поиска при этом остаётся: она про то, ЧТО показывать, а не в каком порядке.
  function sort(by: GroupSortBy, dir: SortDir) {
    sortBy.value = by
    sortDir.value = dir
    return load()
  }

  return {
    items,
    ungroupedCount,
    loading,
    error,
    sortBy,
    sortDir,
    sort,
    query,
    inResearches,
    searchDeeper,
    searching,
    visibleItems,
    ungroupedVisible,
    isEmpty,
    load,
    search,
  }
})
