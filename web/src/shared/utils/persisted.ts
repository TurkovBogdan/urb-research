// Ref, переживающий перезагрузку страницы: значение лежит в localStorage, в состоянии — обычный
// типизированный ref, а перевод между ними делает кодек.
//
// Значение, равное умолчанию, НЕ пишется (ключ удаляется): в хранилище остаются только
// осознанные отклонения, и смена умолчания в коде доезжает до всех, кто его не трогал.
//
// Живёт отдельно от `stores/settings`, потому что домов у такого ref'а два: настройки человека и
// состояние интерфейсов (`stores/ui-state`). Общий помощник в одном из них означал бы, что второй
// импортирует чужой стор ради строчки кода.
//
// Настройки интерфейса берут отсюда `synced` (соседний файл): там же хранилище становится кешем
// поверх базы. Здесь остаётся то, что живёт только в браузере.
import { ref, watch, type Ref } from 'vue'

export interface Codec<T> {
  parse: (raw: string) => T
  serialize: (value: T) => string
}

export const boolCodec: Codec<boolean> = {
  parse: (raw) => raw === '1',
  serialize: (v) => (v ? '1' : '0'),
}

export const strCodec: Codec<string> = { parse: (raw) => raw, serialize: (v) => v }

export const intCodec: Codec<number> = {
  parse: (raw) => Number.parseInt(raw, 10),
  serialize: (v) => String(v),
}

export function persisted<T>(key: string, def: T, codec: Codec<T>): Ref<T> {
  const has = typeof localStorage !== 'undefined'
  const raw = has ? localStorage.getItem(key) : null
  const state = ref(raw === null ? def : codec.parse(raw)) as Ref<T>
  watch(state, (v) => {
    if (!has) return
    if (v === def) localStorage.removeItem(key)
    else localStorage.setItem(key, codec.serialize(v))
  })
  return state
}
