<script setup lang="ts">
/**
 * VSelect с кнопками «предыдущий» / «следующий» по бокам.
 *
 * Нужен там, где варианты стоят в осмысленном порядке (кегль, вес, высота, шаг страниц) и
 * соседний перебирают подряд, сравнивая результат: открывать список ради шага на один пункт —
 * три движения вместо одного. Список при этом остаётся: прыжок к далёкому варианту кнопками
 * был бы долгим.
 *
 * Края не заворачиваются: за последним пунктом идёт не первый, а погашенная кнопка — иначе
 * человек, жмущий на шаг, проскакивает границу набора и не замечает этого. Когда не выбрано
 * ничего, шаг вперёд берёт первый пункт, назад — последний.
 *
 * Всё остальное — проходной VSelect: `$attrs` и слоты уезжают в него, поэтому замена
 * VSelect → VSelectStepper ничего больше не требует.
 */
import { computed, useAttrs, useSlots } from 'vue'
import { IconChevronLeft, IconChevronRight } from '@tabler/icons-vue'

const model = defineModel<unknown>()

const props = withDefaults(defineProps<{
  items: unknown[]
  /** Поле объекта, которое уезжает в модель (зеркало `item-value` у VSelect). */
  itemValue?: string
  /** Плотность задаётся здесь, а не атрибутом: её держат и поле, и обе кнопки. */
  density?: 'default' | 'comfortable' | 'compact'
  prevLabel?: string
  nextLabel?: string
}>(), {
  itemValue: 'value',
  density: 'default',
  prevLabel: 'Предыдущий',
  nextLabel: 'Следующий',
})

defineOptions({ inheritAttrs: false })

const NOTHING_SELECTED = -1

function valueOf(item: unknown): unknown {
  if (item !== null && typeof item === 'object') {
    return (item as Record<string, unknown>)[props.itemValue]
  }
  return item
}

const index = computed(() => props.items.findIndex((item) => valueOf(item) === model.value))

const lastIndex = computed(() => props.items.length - 1)

const atFirst = computed(() => index.value === 0)
const atLast = computed(() => index.value === lastIndex.value)

function step(delta: number): void {
  if (lastIndex.value < 0) return
  const target =
    index.value === NOTHING_SELECTED
      ? (delta > 0 ? 0 : lastIndex.value)
      : Math.min(Math.max(index.value + delta, 0), lastIndex.value)
  model.value = valueOf(props.items[target])
}

const iconSize = computed(() => (props.density === 'default' ? 18 : 16))

const slots = useSlots()
const forwardedSlots = computed(() => Object.keys(slots))

// Оформление места применения принадлежит тройке целиком (ширина, отступы), а остальные
// атрибуты — полю: без этого деления класс с шириной уехал бы на поле внутри и кнопки встали
// бы за его границами.
const attrs = useAttrs()
const groupClass = computed(() => attrs.class)
const groupStyle = computed(() => attrs.style)
const selectAttrs = computed(() => {
  const { class: _class, style: _style, ...rest } = attrs
  return rest
})
</script>

<template>
  <div class="field-group" :class="groupClass" :style="groupStyle">
    <VBtn
      variant="outlined"
      :density="density"
      icon
      class="field-group__btn field-group__btn--before"
      :aria-label="prevLabel"
      :disabled="atFirst"
      @click="step(-1)"
    >
      <IconChevronLeft :size="iconSize" />
    </VBtn>

    <VSelect
      v-bind="selectAttrs"
      v-model="model"
      :items="items"
      :item-value="itemValue"
      :density="density"
    >
      <template v-for="name in forwardedSlots" #[name]="slotProps" :key="name">
        <slot :name="name" v-bind="slotProps ?? {}" />
      </template>
    </VSelect>

    <VBtn
      variant="outlined"
      :density="density"
      icon
      class="field-group__btn"
      :aria-label="nextLabel"
      :disabled="atLast"
      @click="step(1)"
    >
      <IconChevronRight :size="iconSize" />
    </VBtn>
  </div>
</template>

<style scoped>
/* Ширину тройке задаёт место применения — целиком, а не полю внутри: кнопки по краям занимают
   свою коробку, поле забирает остаток. `min-width: 0` обязателен, иначе поле упирается в
   собственную минимальную ширину и выталкивает кнопку за край. */
.v-select {
  flex: 1 1 auto;
  min-width: 0;
}
</style>
