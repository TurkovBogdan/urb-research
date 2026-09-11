// Ref настройки интерфейса: то же, что `persisted`, плюс отправка в базу.
//
// Кеш ведёт `persisted` (значение, равное умолчанию, из него удаляется), а здесь добавлены две
// вещи: регистрация ключа в механизме обмена и постановка изменения в очередь на отправку.
//
// Наблюдатель синхронный намеренно: флаг «применяем извне» снимается сразу после присваивания,
// и отложенный наблюдатель увидел бы уже снятый флаг — значение, только что прочитанное из базы,
// уехало бы в неё обратно.
import { watch, type Ref } from 'vue'

import type { SettingValue } from '@/api/interface-settings'
import { persisted, type Codec } from './persisted'
import { enqueue, isApplyingExternal, registerSetting } from './settings-sync'

export function synced<T extends SettingValue>(key: string, def: T, codec: Codec<T>): Ref<T> {
  const state = persisted(key, def, codec)
  registerSetting(key, state, def, codec)
  watch(
    state,
    () => {
      if (!isApplyingExternal()) enqueue(key)
    },
    { flush: 'sync' },
  )
  return state
}
