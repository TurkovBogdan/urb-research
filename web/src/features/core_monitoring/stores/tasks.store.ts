import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchTasks, type TaskInfo } from '../api'

export interface TaskGroup {
  module: string
  tasks: TaskInfo[]
}

// Список задач кэшируем в localStorage (stale-while-revalidate): при возврате на
// страницу карточки рисуются мгновенно из кэша и обновляются в фоне без скелета и
// визуальных рывков. Кэшируем ТОЛЬКО список (детальные логи не кэшируются вовсе).
const CACHE_KEY = 'core.tasks.list'

interface TasksCache {
  tasks: TaskInfo[]
  loadedAt: number
}

function readCache(): TasksCache | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as TasksCache
    return Array.isArray(parsed.tasks) ? parsed : null
  } catch {
    return null
  }
}

function writeCache(cache: TasksCache): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
  } catch {
    /* quota / private mode — кэш необязателен */
  }
}

export const useTasksStore = defineStore('core-tasks', () => {
  const cached = readCache()

  const tasks      = ref<TaskInfo[]>(cached?.tasks ?? [])
  const loading    = ref(cached === null)   // скелет только при самом первом визите
  const refreshing = ref(false)             // фоновое обновление → спиннер на кнопке
  const error      = ref<string | null>(null)
  const loadedAt   = ref<number | null>(cached?.loadedAt ?? null)

  const search       = ref('')
  const statusFilter = ref<'all' | 'running' | 'errors'>('all')

  const filtered = computed<TaskInfo[]>(() => {
    const q = search.value.trim().toLowerCase()
    return tasks.value.filter(t => {
      if (statusFilter.value === 'running' && t.stats_24h.running === 0) return false
      if (statusFilter.value === 'errors' && t.stats_24h.error === 0) return false
      if (!q) return true
      return (
        t.name.toLowerCase().includes(q) ||
        t.code.toLowerCase().includes(q) ||
        t.module.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q)
      )
    })
  })

  // Группировка по модулям; порядок задаёт бэк (core → core_* → модули),
  // Map сохраняет порядок вставки.
  const grouped = computed<TaskGroup[]>(() => {
    const byModule = new Map<string, TaskInfo[]>()
    for (const t of filtered.value) {
      const list = byModule.get(t.module)
      if (list) list.push(t)
      else byModule.set(t.module, [t])
    }
    return [...byModule.entries()].map(([module, list]) => ({ module, tasks: list }))
  })

  const summary = computed(() => ({
    total:   tasks.value.length,
    enabled: tasks.value.filter(t => t.enabled).length,
    running: tasks.value.reduce((a, t) => a + t.stats_24h.running, 0),
    errors:  tasks.value.reduce((a, t) => a + t.stats_24h.error, 0),
  }))

  async function load() {
    refreshing.value = true
    try {
      tasks.value = await fetchTasks()
      error.value = null
      loadedAt.value = Date.now()
      writeCache({ tasks: tasks.value, loadedAt: loadedAt.value })
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      refreshing.value = false
      loading.value = false
    }
  }

  return {
    tasks, loading, refreshing, error, loadedAt,
    search, statusFilter,
    filtered, grouped, summary,
    load,
  }
})
