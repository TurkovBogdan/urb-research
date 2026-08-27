<script lang="ts">
import type { TablerIcon } from '@/shared/nav'

/**
 * Одна переключаемая область поиска: `key` уходит наружу в модель, `icon` рисуется на кнопке,
 * `label` — подсказка (текстом, потому что на кнопке ничего кроме глифа нет).
 */
export type SearchScope = {
  key: string
  icon: TablerIcon
  label: string
}
</script>

<script setup lang="ts">
// Поисковое поле с переключателями области прямо внутри рамки: одна строка запроса, а кнопки
// говорят, ГДЕ её искать. Переключатели живут в поле, а не рядом с ним, потому что они относятся
// к этому запросу и ни к чему больше — вынесенные в панель, они читались бы вторым фильтром.
//
// Разделение моделей: `v-model` — текст, `v-model:active-scopes` — ключи включённых областей
// (`scopes` пропом описывает сам набор, поэтому включённые названы отдельным именем). Обе модели
// меняются независимо (области переключают и с пустым полем), и потребитель сам решает, стоит ли
// перезапрашивать: смена области при пустом запросе ничего не меняет в выдаче.
import { IconSearch } from '@tabler/icons-vue'

withDefaults(defineProps<{
  /** Переключатели области; пустой набор — обычное поле поиска без кнопок. */
  scopes?: SearchScope[]
  label?: string
  placeholder?: string
  /**
   * Пояснение под полем — например, что именно входит в стог при включённых областях. Держится
   * на месте всегда: оно описывает текущую область поиска, а не подсказывает во время ввода, и
   * появляясь по фокусу дёргало бы вёрстку панели.
   */
  hint?: string
  density?: 'default' | 'comfortable' | 'compact'
  clearable?: boolean
}>(), {
  scopes: () => [],
  density: 'comfortable',
  clearable: true,
})

const query = defineModel<string>({ default: '' })
const activeScopes = defineModel<string[]>('activeScopes', { default: () => [] })

// Крестик очистки у VTextField отдаёт `null`, а наружу обещана строка: потребитель зовёт на
// запросе `trim()` и на пустом поле упал бы. Пустая строка — то же «ничего не введено».
function setQuery(value: string | null) {
  query.value = value ?? ''
}

function isActive(key: string): boolean {
  return activeScopes.value.includes(key)
}

// Новый массив, а не мутация на месте: наблюдатели потребителя следят за ссылкой.
function toggle(key: string) {
  activeScopes.value = isActive(key)
    ? activeScopes.value.filter((active) => active !== key)
    : [...activeScopes.value, key]
}
</script>

<template>
  <VTextField
    :model-value="query"
    :label="label"
    :placeholder="placeholder"
    :prepend-inner-icon="IconSearch"
    :density="density"
    :clearable="clearable"
    :hint="hint"
    :persistent-hint="!!hint"
    :hide-details="!hint"
    variant="outlined"
    class="search-field"
    @update:model-value="setQuery"
  >
    <template v-if="scopes.length" #append-inner>
      <!-- mousedown гасится, иначе нажатие кнопки уводит курсор из поля: пользователь щёлкает
           переключатель посреди набора запроса и продолжает печатать. -->
      <div class="search-field__scopes" @mousedown.prevent>
        <VDivider vertical class="search-field__divider" />
        <VBtn
          v-for="scope in scopes"
          :key="scope.key"
          :color="isActive(scope.key) ? 'primary' : undefined"
          :variant="isActive(scope.key) ? 'tonal' : 'text'"
          :aria-label="scope.label"
          :aria-pressed="isActive(scope.key)"
          size="x-small"
          icon
          density="comfortable"
          @click="toggle(scope.key)"
        >
          <component :is="scope.icon" :size="16" :stroke-width="1.7" />
          <VTooltip activator="parent" location="top">{{ scope.label }}</VTooltip>
        </VBtn>
      </div>
    </template>
  </VTextField>
</template>

<style scoped>
.search-field__scopes {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-inline-start: 2px;
}

/* Линейка отбивает переключатели от текста: без неё глифы читаются как продолжение запроса. */
.search-field__divider {
  margin-inline-end: 4px;
  height: 20px;
  align-self: center;
}
</style>
