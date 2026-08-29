import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  editAreaDescription,
  getArea,
  listAreaDocuments,
  listAreaQueries,
  renameArea,
  type AreaDetail,
  type SourceDocumentRow,
  type SourceQueryRow,
} from '../api'
import { matchesQuery, normalizeQuery } from '../search'

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

  // ── Поиск по деталке ────────────────────────────────────────────────────────
  // Одна строка на всё содержимое зоны — то же обещание, что и на исследовании. Догоняющей
  // половины здесь нет и не нужно: у зоны на клиенте лежит ВСЁ, по чему ищут, включая синтез и
  // разбор источников, — за ответом бэкенда идут только там, где тела остались на сервере.
  const search = ref('')
  const needle = computed(() => normalizeQuery(search.value))
  const searching = computed(() => needle.value.length > 0)

  // Описание и постановка — две карточки и две находки: «о чём зона» своими словами и заполненный
  // агентом бриф. Ищутся порознь, ровно так же, как порознь и показываются.
  const briefMatches = computed(() =>
    matchesQuery([area.value?.title, area.value?.description], needle.value),
  )
  const taskMatches = computed(() =>
    matchesQuery(
      [area.value?.objective, area.value?.scope, area.value?.expectations],
      needle.value,
    ),
  )
  const bodyMatches = computed(() => matchesQuery([area.value?.body], needle.value))

  const filteredQueries = computed(() =>
    queries.value.filter((query) => matchesQuery([query.query], needle.value)),
  )

  // У источника смотрим и `summary`/`note` — в таблице их не видно, но это и есть разбор
  // источника: вопрос «где в зоне про X» без них отвечался бы неполно.
  const filteredSources = computed(() =>
    sources.value.filter((source) =>
      matchesQuery([source.title, source.url, source.summary, source.note], needle.value),
    ),
  )

  const matchCount = computed(
    () =>
      Number(briefMatches.value) +
      Number(taskMatches.value) +
      Number(bodyMatches.value) +
      filteredQueries.value.length +
      filteredSources.value.length,
  )

  let current = ''

  async function load(code: string) {
    // Запрос переживает обновление той же страницы, но не переход на другую зону: унесённая
    // строка искала бы в чужих данных.
    if (code !== current) search.value = ''
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

  // Правка описания живёт по тем же правилам, что и переименование: свой флаг «в полёте», отказ
  // гасится тостом клиента. Ответ — удалось или нет: правку закрывает владелец поля, и «текст
  // сохранён» он иначе не отличит от «текст сохранён тот же самый».
  const describing = ref(false)

  async function saveDescription(description: string): Promise<boolean> {
    const code = area.value?.code
    if (!code) return false
    describing.value = true
    try {
      area.value = await editAreaDescription(code, description)
      return true
    } catch {
      return false
    } finally {
      describing.value = false
    }
  }

  function reset() {
    area.value = null
    queries.value = []
    sources.value = []
    search.value = ''
    error.value = null
  }

  return {
    area, queries, sources, loading, error, renaming, describing,
    search, searching, briefMatches, taskMatches, bodyMatches,
    filteredQueries, filteredSources, matchCount,
    load, rename, saveDescription, reset,
  }
})
