/**
 * Клиент раздела «О приложении» (бэк: /internal/core/update).
 *
 * Три вызова с разной ценой: `installation` читает локальные факты и отвечает мгновенно, `check`
 * ходит к remote (POST, потому что меняет tracking-ссылки чекаута, и может занять секунды),
 * `start` передаёт установку скрипту обновления и отвечает ДО того, как бэкенд погаснет.
 *
 * Всё неизвестное приходит как `null`: без каталога `.git` установка не знает ни коммита, ни
 * чистоты дерева, а ветка без манифеста не имеет версии. Ноль на этом месте был бы утверждением.
 */

import { internalApi } from '@/api/client/internal'

const BASE = '/core/update'

/** Что стоит здесь: выпуск, сборка под ним и причина, по которой обновление откажется идти. */
export interface Installation {
  version: string | null
  release_date: string | null
  /** Ветка, за которой следует установка (`UPDATE_BRANCH`). */
  followed_branch: string
  checked_out_branch: string | null
  branch_matches: boolean
  commit: string | null
  /** `git describe`: выпуск, расстояние до него и сборка одной строкой. */
  describes_as: string | null
  dirty: boolean | null
  /** Код причины, по которой обновление откажется идти (`about.refusal.*`), или `null`. */
  refusal: 'dirty_tree' | 'branch_mismatch' | null
}

/** Что предлагает ветка и как мы стоим относительно неё. */
export interface UpstreamHead {
  branch: string
  version: string | null
  commit: string
  behind: number | null
  /** Локальные коммиты, которых нет на remote: fast-forward на них сломается. */
  ahead: number | null
}

export interface StartedUpdate {
  status: string
  pid: number
  log: string
}

export const updateApi = {
  installation: () => internalApi.get<Installation>(BASE),
  check: () => internalApi.post<UpstreamHead>(`${BASE}/check`),
  start: () => internalApi.post<StartedUpdate>(`${BASE}/start`),
}
