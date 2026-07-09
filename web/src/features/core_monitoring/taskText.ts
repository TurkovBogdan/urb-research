import { useI18n } from 'vue-i18n'
import type { TaskInfo } from './api'

type Identity = Pick<TaskInfo, 'module' | 'code'>
type Field = 'name' | 'short' | 'description'

// Название/описание задачи живут на бэке (`NAME`/`DESCRIPTION` класса задачи) и
// приходят в payload. КЛЮЧ перевода выводится из стабильной пары `(module, code)` —
// бэк отдельный ключ не шлёт.
//
// Порядок поиска по полю:
//   1. `<module>.task.<code>.<field>` — словарь самой фичи модуля
//   2. `core_monitoring.catalog.<module>.<code>.<field>` — catch-all для модулей без фронт-фичи (напр. `core`)
//   3. литерал с бэка (`info.name` / `info.description`) — чтобы непереведённые/новые
//      задачи рисовались, а не текли сырым ключом
export function useTaskText() {
  const { t, te } = useI18n()

  function pick(id: Identity, field: Field, fallback: string): string {
    const own = `${id.module}.task.${id.code}.${field}`
    if (te(own)) return t(own)
    const catalog = `core_monitoring.catalog.${id.module}.${id.code}.${field}`
    if (te(catalog)) return t(catalog)
    return fallback
  }

  return {
    taskName: (info: Identity & Pick<TaskInfo, 'name'>) => pick(info, 'name', info.name),
    taskNameShort: (info: Identity & Pick<TaskInfo, 'name'>) =>
      pick(info, 'short', pick(info, 'name', info.name)),
    taskDescription: (info: Identity & Pick<TaskInfo, 'description'>) =>
      pick(info, 'description', info.description),
  }
}
