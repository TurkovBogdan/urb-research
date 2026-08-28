<script setup lang="ts">
// Выбор полки: список с поиском, где каждый пункт назван своим видом — иконкой в цвете полки.
// Полку выбирают в трёх местах (фильтр реестра, привязка исследования, перевешивание при
// удалении), и раньше каждое само собирало пункты, само следило за загрузкой и само решало,
// как нарисовать вид полки. Здесь это один раз: место применения отдаёт значение и говорит,
// нужны ли ему псевдо-пункты.
//
// Набор берётся из справочника (`group-catalog.store`) и подгружается сам — месту применения
// не нужно знать, грузил ли кто-то полки до него.
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import VSelectSearch from '@/components/VSelectSearch.vue'

import GroupSwatch from './GroupSwatch.vue'
import { useGroupCatalogStore } from '../stores/group-catalog.store'
import { UNGROUPED_CODE } from '../api'

/** `null` — пункт «Все группы» (полка не выбрана). */
const model = defineModel<string | null>({ required: true })

const props = withDefaults(defineProps<{
  label?: string
  /** Пункт «Все группы» — снимает сужение по полке; нужен фильтрам, не нужен формам. */
  withAll?: boolean
  /** Пункт «Без группы» — только не разложенные (бэк читает пустой код именно так). */
  withUngrouped?: boolean
  /** Полка, которую выбрать нельзя: та, которую удаляют, или та, где исследование уже лежит. */
  exclude?: string | null
  density?: 'default' | 'comfortable' | 'compact'
  autofocus?: boolean
}>(), {
  label: undefined,
  withAll: false,
  withUngrouped: false,
  exclude: null,
  density: 'comfortable',
  autofocus: false,
})

const { t } = useI18n()
const catalog = useGroupCatalogStore()

onMounted(catalog.ensure)

interface GroupOption {
  title: string
  value: string | null
  icon: string
  color: string
  /** У псевдо-полки вида нет: цвет означал бы принадлежность к полке, которой не существует. */
  plain?: boolean
}

const options = computed<GroupOption[]>(() => {
  const pseudo: GroupOption[] = []
  if (props.withAll) {
    pseudo.push({ title: t('research.group.select.all'), value: null, icon: 'category', color: '', plain: true })
  }
  if (props.withUngrouped) {
    pseudo.push({ title: t('research.group.ungrouped.title'), value: UNGROUPED_CODE, icon: '', color: '', plain: true })
  }
  return [
    ...pseudo,
    ...catalog.items
      .filter((group) => group.code !== props.exclude)
      .map((group) => ({ title: group.title, value: group.code, icon: group.icon, color: group.color })),
  ]
})

// Пустой справочник и незагруженный — разные ответы: пока полки едут, «полок нет» было бы враньём.
const noDataText = computed(() =>
  catalog.loaded ? t('research.group.select.empty') : t('research.group.select.loading'),
)

// Крестик очистки — только там, где «пусто» есть само по себе значение: у фильтра это «Все
// группы» (`null`), и крестик возвращает его. В форме очищать не во что: полка либо выбрана,
// либо не выбрана, и снимают её отдельным действием, а не опустошением поля.
//
// На самих «Всех группах» крестика нет: Vuetify считает поле заполненным (пункт с `null` —
// такой же пункт списка), и без этой проверки на умолчании висела бы кнопка, которая ничего
// не делает.
const clearable = computed(() => props.withAll && model.value !== null)

// `VSelectSearch` отдаёт значение как `unknown`: обёртка не знает формы пунктов, её задаёт
// `options` парой строк выше. Очистка приходит тем же путём — как `null`.
function select(value: unknown) {
  model.value = (value ?? null) as string | null
}
</script>

<template>
  <!-- `:chips="false"` — с чипами (глобальный дефолт) Vuetify рисует `#chip` и молча
       игнорирует `#selection`, а выбранная полка обязана быть со своим видом. -->
  <VSelectSearch
    :model-value="model"
    :items="options"
    :label="props.label ?? t('research.group.select.label')"
    :loading="catalog.loading"
    :search-placeholder="t('research.group.select.search')"
    :no-data-text="noDataText"
    :density="props.density"
    :autofocus="props.autofocus"
    :clearable="clearable"
    :chips="false"
    variant="outlined"
    hide-details
    @update:model-value="select"
  >
    <!-- В слоты пунктов приезжает ИСХОДНЫЙ объект (`item`), обёртка — отдельным `internalItem`. -->
    <template #item="{ props: itemProps, item }">
      <VListItem v-bind="itemProps">
        <template #prepend>
          <GroupSwatch :icon="item.icon" :color="item.color" :plain="item.plain" />
        </template>
      </VListItem>
    </template>

    <template #selection="{ item }">
      <span class="group-select__value">
        <GroupSwatch :icon="item.icon" :color="item.color" :plain="item.plain" :size="18" />
        {{ item.title }}
      </span>
    </template>
  </VSelectSearch>
</template>

<style scoped>
/* Плашка и имя — одна строка выбранного значения; длинное имя режется, чтобы поле не
   расползалось шире соседей. */
.group-select__value {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>
