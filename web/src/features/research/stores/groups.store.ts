import { ref } from 'vue'
import { defineStore } from 'pinia'

import { listGroups, listResearches, UNGROUPED_CODE, type GroupListRow } from '../api'

// Полки реестра. Список короткий и без пагинации — бэк уже отдаёт его в порядке показа
// (больший sort выше), поэтому стор ничего не сортирует.
//
// Псевдо-полка «Без группы» строкой в БД не существует: её счётчик — это total того же списка
// исследований с фильтром «не разложенные», поэтому берётся вторым запросом рядом со списком.
export const useGroupsStore = defineStore('research-groups', () => {
  const items = ref<GroupListRow[]>([])
  const ungroupedCount = ref(0)
  const loading = ref(true)
  const error = ref<unknown>(null)

  async function load() {
    error.value = null
    try {
      // `report: false` — отказ чтения раздела показывает сама страница (SectionError);
      // тост поверх него был бы вторым сообщением об одном и том же.
      const [groups, ungrouped] = await Promise.all([
        listGroups({ report: false }),
        listResearches({ group_code: UNGROUPED_CODE, page_size: 1 }, { report: false }),
      ])
      items.value = groups
      ungroupedCount.value = ungrouped.total
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { items, ungroupedCount, loading, error, load }
})
