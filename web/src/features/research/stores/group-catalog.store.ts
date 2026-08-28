import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { listGroups, type GroupRow } from '../api'

/**
 * Справочник полок: код, название и вид (иконка + цвет) — всё, что нужно, чтобы полку ВЫБРАТЬ.
 *
 * Отдельно от `groups.store`, потому что роли разные: тот держит страницу полок (порядок, поиск,
 * счётчики) и живёт её жизнью, а справочник переживает страницы и нужен любому месту, где полку
 * выбирают, — фильтру реестра, окну привязки, окну удаления.
 *
 * Набор попадает сюда с двух сторон: `adopt` — когда список полок уже пришёл на страницу (второй
 * раз спрашивать бэк незачем), `ensure` — когда полки понадобились месту, которое их не грузило.
 * `loaded` отличает «ещё не спрашивали» от «спросили, и полок нет»: без этого пустой справочник
 * перезапрашивался бы при каждом открытии окна.
 */
export const useGroupCatalogStore = defineStore('research-group-catalog', () => {
  const items = ref<GroupRow[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  // Один запрос на всех: два окна, открытых подряд, ждут общий, а не шлют по своему.
  let inflight: Promise<void> | null = null

  const isEmpty = computed(() => loaded.value && !items.value.length)

  function adopt(groups: GroupRow[]): void {
    items.value = [...groups]
    loaded.value = true
  }

  async function ensure(): Promise<void> {
    if (loaded.value) return
    if (inflight) return inflight
    loading.value = true
    inflight = (async () => {
      try {
        // `report: false` — молчаливый отказ: справочник грузится фоном под чужим полем, и тост
        // о нём человек не связал бы с тем, что делает. Пустой список честнее ложного набора.
        adopt(await listGroups({}, { report: false }))
      } catch {
        items.value = []
      } finally {
        loading.value = false
        inflight = null
      }
    })()
    return inflight
  }

  /** Набор устарел (полку завели, переименовали или снесли) — следующий `ensure` перечитает. */
  function invalidate(): void {
    loaded.value = false
  }

  return { items, loading, loaded, isEmpty, adopt, ensure, invalidate }
})
