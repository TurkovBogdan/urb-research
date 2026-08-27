import { IconAlertTriangle, IconError404, IconLock, IconWifiOff, type Icon } from '@tabler/icons-vue'

// Каталог отказов, при которых смотреть на странице нечего и вместо содержимого показывается
// экран. Отказ ОПЕРАЦИИ (кнопка не сработала) сюда не входит никогда — там ответ идёт рядом с
// действием, экран отбирать нельзя. «Сущности нет» — тоже не экран, а состояние внутри раздела.

export type ErrorKind = 'not-found' | 'forbidden' | 'failure' | 'offline'

/** Выходы с экрана. Последний в списке рисуется главным действием. */
export type ErrorAction = 'back' | 'home' | 'retry'

export interface ErrorKindSpec {
  icon: Icon
  /** Код ответа; у отказа без ответа (нет связи) его нет. */
  code: string | null
  /** Ветка словаря `common.errors.<key>` с заголовком и описанием. */
  key: string
  actions: ErrorAction[]
}

export const ERROR_KINDS: Record<ErrorKind, ErrorKindSpec> = {
  'not-found': { icon: IconError404, code: null, key: 'notFound', actions: ['back', 'home'] },
  forbidden: { icon: IconLock, code: '403', key: 'forbidden', actions: ['back', 'home'] },
  failure: { icon: IconAlertTriangle, code: '500', key: 'failure', actions: ['home', 'retry'] },
  offline: { icon: IconWifiOff, code: null, key: 'offline', actions: ['retry'] },
}
