import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

import {
  getResearch,
  listResearchDocuments,
  renameResearch,
  searchResearchBodies,
  type ResearchDetail,
  type SourceDocumentRow,
} from '../api'
import { MIN_DEEP_QUERY_LENGTH, matchesQuery, normalizeQuery } from '../search'

// Деталка исследования: тело + области и заметки (скан-слой). Поиски страница не показывает —
// они принадлежат области, там их и видно (`/research/areas/…`); ответ бэкенда их всё ещё несёт.
export const useResearchDetailStore = defineStore('research-research-detail', () => {
  const research = ref<ResearchDetail | null>(null)
  const loading = ref(false)
  // Держим сам отказ, а не его текст: показ (`SectionError`) отличает «сущности нет» от сбоя
  // по статусу ответа, а формулировку берёт из `errorText`.
  const error = ref<unknown>(null)

  const areas = computed(() => research.value?.areas ?? [])
  // Свежие сверху — порядок страницы, а не бэкенда: агенту заметки отдаются в порядке появления
  // (рабочий журнал), человеку нужен срез «что надумано последним». Даты приходят SQL-строкой
  // (`YYYY-MM-DD HH:MM:SS`), у которой лексикографический порядок совпадает с хронологическим.
  const notes = computed(() =>
    [...(research.value?.notes ?? [])].sort((a, b) => b.updated_at.localeCompare(a.updated_at)),
  )

  // Источники грузятся сюда, а не в таблицу: глобальный поиск ищет по ним наравне с зонами и
  // заметками, а фильтровать в сторе то, чем владеет компонент, нельзя.
  const sources = ref<SourceDocumentRow[]>([])

  // ── Глобальный поиск по деталке ─────────────────────────────────────────────
  // Одна строка на все связанные элементы. У источника смотрим и `summary`/`note` — в таблице
  // их не видно, но это и есть разбор источника: вопрос «где в исследовании про X» без них
  // отвечался бы неполно. (Собственный фильтр таблицы — наоборот, ищет только видимое.)
  const search = ref('')
  const needle = computed(() => normalizeQuery(search.value))
  const searching = computed(() => needle.value.length > 0)

  // Само исследование — тоже документ, который ищут: описание и основной документ участвуют
  // наравне со связанными элементами и на пустой запрос попадают в выборку сами.
  const briefMatches = computed(() =>
    matchesQuery([research.value?.title, research.value?.description], needle.value),
  )
  const bodyMatches = computed(() => matchesQuery([research.value?.body], needle.value))

  // ── Догоняющая половина поиска ──────────────────────────────────────────────
  // Тела зон и заметок и материал источников сюда не приезжают (у одного исследования это до
  // полутора десятков мегабайт), поэтому по ним ищет бэк и присылает только коды. Клиент
  // показывает свои совпадения сразу, а эти дорисовывает, когда ответ придёт.
  const deepAreas = ref(new Set<string>())
  const deepNotes = ref(new Set<string>())
  const deepSources = ref(new Set<string>())
  const deepSearching = ref(false)

  // Запрос уходит не на каждую букву: набор идёт быстрее ответа, и без паузы каждый промежуточный
  // запрос читал бы все тела впустую.
  const DEEP_DEBOUNCE_MS = 350
  let deepTimer: ReturnType<typeof setTimeout> | undefined
  let deepRun: AbortController | undefined

  function forgetDeep() {
    deepAreas.value = new Set()
    deepNotes.value = new Set()
    deepSources.value = new Set()
  }

  function cancelDeep() {
    clearTimeout(deepTimer)
    deepRun?.abort()
    deepRun = undefined
    deepSearching.value = false
  }

  async function runDeep(code: string, query: string) {
    const run = new AbortController()
    deepRun = run
    deepSearching.value = true
    try {
      // `report: false` — отказ догоняющей половины не тост: мгновенные совпадения на экране,
      // и «не удалось» поверх них сбивало бы с толку. Молча остаёмся с ними.
      const found = await searchResearchBodies(code, query, { signal: run.signal, report: false })
      if (deepRun !== run) return
      deepAreas.value = new Set(found.areas)
      deepNotes.value = new Set(found.notes)
      deepSources.value = new Set(found.sources)
    } catch {
      if (deepRun === run) forgetDeep()
    } finally {
      if (deepRun === run) {
        deepRun = undefined
        deepSearching.value = false
      }
    }
  }

  watch([needle, () => research.value?.code], ([query, code]) => {
    cancelDeep()
    forgetDeep()
    if (!code || query.length < MIN_DEEP_QUERY_LENGTH) return
    deepSearching.value = true
    deepTimer = setTimeout(() => runDeep(code, query), DEEP_DEBOUNCE_MS)
  })

  const filteredAreas = computed(() =>
    areas.value.filter(
      (area) =>
        matchesQuery([area.title, area.description], needle.value) || deepAreas.value.has(area.code),
    ),
  )
  const filteredNotes = computed(() =>
    notes.value.filter(
      (note) =>
        matchesQuery([note.title, note.description], needle.value) || deepNotes.value.has(note.code),
    ),
  )
  const filteredSources = computed(() =>
    sources.value.filter(
      (source) =>
        matchesQuery([source.title, source.url, source.summary, source.note], needle.value) ||
        deepSources.value.has(source.code),
    ),
  )

  // Описание и основной документ считаются наравне с элементами: строка «найдено» отвечает
  // «сколько мест в исследовании про это», а они такие же места.
  const matchCount = computed(
    () =>
      Number(briefMatches.value) +
      Number(bodyMatches.value) +
      filteredAreas.value.length +
      filteredNotes.value.length +
      filteredSources.value.length,
  )

  // Latest-navigation-wins: a slower earlier response for a stale code is dropped, so
  // rapid page-to-page navigation always settles on the current route's data.
  let current = ''

  async function load(code: string) {
    // Запрос переживает обновление той же страницы, но не переход на другое исследование:
    // унесённая строка искала бы в чужих данных.
    if (code !== current) search.value = ''
    current = code
    loading.value = true
    error.value = null
    try {
      const [data, sourceRows] = await Promise.all([
        getResearch(code),
        listResearchDocuments(code),
      ])
      if (current !== code) return
      research.value = data
      sources.value = sourceRows
    } catch (e) {
      if (current !== code) return
      error.value = e
      research.value = null
      sources.value = []
    } finally {
      if (current === code) loading.value = false
    }
  }

  // Переименование не трогает `error`: раздел прочитан и на экране, а отказ записи показывает
  // тост клиента. Иначе неудачная правка стёрла бы страницу под собой.
  //
  // Отказ здесь и гасится: сообщение уже показано, а вся оставшаяся реакция — не менять название.
  // Правка от этого остаётся открытой с набранным текстом (её закрывает приход НОВОГО названия),
  // то есть человек попадает ровно туда, откуда повторит попытку.
  const renaming = ref(false)

  async function rename(title: string) {
    const code = research.value?.code
    if (!code) return
    renaming.value = true
    try {
      research.value = await renameResearch(code, title)
    } catch {
      // см. выше
    } finally {
      renaming.value = false
    }
  }

  function reset() {
    cancelDeep()
    forgetDeep()
    research.value = null
    sources.value = []
    search.value = ''
    error.value = null
  }

  return {
    research, areas, notes, sources, loading, error, renaming,
    search, searching, deepSearching, briefMatches, bodyMatches,
    filteredAreas, filteredNotes, filteredSources, matchCount,
    load, rename, reset,
  }
})
