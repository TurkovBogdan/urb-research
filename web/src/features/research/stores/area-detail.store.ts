import { ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getArea,
  listAreaDocuments,
  listAreaQueries,
  renameArea,
  type AreaDetail,
  type SourceDocumentRow,
  type SourceQueryRow,
} from '../api'

// Деталка зоны: скан + бриф (objective/scope/expectations) + синтез (body) + её поиски и источники.
// Источники грузит стор, а не таблица: данными владеет страница, компонент их только показывает.
export const useAreaDetailStore = defineStore('research-area-detail', () => {
  const area = ref<AreaDetail | null>(null)
  const queries = ref<SourceQueryRow[]>([])
  const sources = ref<SourceDocumentRow[]>([])
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  let current = ''

  async function load(code: string) {
    current = code
    loading.value = true
    error.value = null
    try {
      const [areaData, queryRows, sourceRows] = await Promise.all([
        getArea(code),
        listAreaQueries(code),
        listAreaDocuments(code),
      ])
      if (current !== code) return
      area.value = areaData
      queries.value = queryRows
      sources.value = sourceRows
    } catch (e) {
      if (current !== code) return
      error.value = e
      area.value = null
      queries.value = []
      sources.value = []
    } finally {
      if (current === code) loading.value = false
    }
  }

  // Отказ переименования гасится здесь: клиент уже показал тост, а вся оставшаяся реакция — не
  // менять название, отчего правка остаётся открытой с набранным текстом (её закрывает приход
  // НОВОГО названия). Поле `error` не трогаем — оно про отказ чтения раздела.
  const renaming = ref(false)

  async function rename(title: string) {
    const code = area.value?.code
    if (!code) return
    renaming.value = true
    try {
      area.value = await renameArea(code, title)
    } catch {
      // см. выше
    } finally {
      renaming.value = false
    }
  }

  function reset() {
    area.value = null
    queries.value = []
    sources.value = []
    error.value = null
  }

  return { area, queries, sources, loading, error, renaming, load, rename, reset }
})
