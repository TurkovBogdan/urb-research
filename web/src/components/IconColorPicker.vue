<script setup lang="ts">
// Выбор иконки и цвета одной панелью: рисунок и тон — не два независимых поля, а одна плашка,
// и оценивают её целиком. Поэтому вверху предпросмотр — та самая плашка, что окажется на
// карточке, — рядом с ним палитра, а под линейкой набор иконок с поиском.
//
// Собран из двух примитивов в режиме `bare`: лоток здесь один, общий на оба выбора; каждый со
// своим лотком читался бы как два окна, поставленных рядом.
//
// Цвет доходит до иконок сам: роли `--gc-ink` / `--gc-fill` объявлены на корне (`.color-tones`)
// и наследуются, поэтому выбранная плитка иконки красится выбранным цветом — связь между двумя
// половинами панели видна без единого пропа между ними.
import { computed } from 'vue'

import ColorPicker from '@/components/ColorPicker.vue'
import IconPicker from '@/components/IconPicker.vue'
import type { ColorToneVars } from '@/shared/colorTones'
import type { TablerIcon } from '@/shared/nav'

const icon = defineModel<string | null>('icon', { default: null })
const color = defineModel<string | null>('color', { default: null })

const props = withDefaults(defineProps<{
  /** Полный набор кодов иконок в порядке показа. */
  icons: string[]
  /** Полный набор имён цветов в порядке показа. */
  colors: string[]
  /** Код → компонент иконки; `null` — иконка не выбрана (резолвер отдаёт запасную). */
  resolveIcon: (name: string | null) => TablerIcon
  /** Имя → ступени цвета переменными; `null` — цвет не выбран (резолвер отдаёт запасной тон). */
  resolveColor: (name: string | null) => ColorToneVars
  /** Высота области иконок; за ней она прокручивается. */
  height?: number | string
  /** Разрешить «без цвета» — плитка сброса в палитре. */
  clearable?: boolean
}>(), {
  height: 200,
  clearable: false,
})

const tones = computed(() => props.resolveColor(color.value))
</script>

<template>
  <div class="icon-color-picker color-tones" :style="tones">
    <div class="icon-color-picker__head">
      <span class="icon-color-picker__preview">
        <component :is="props.resolveIcon(icon)" :size="18" :stroke-width="1.6" />
      </span>
      <ColorPicker
        v-model="color"
        :colors="props.colors"
        :resolve="props.resolveColor"
        :clearable="props.clearable"
        :size="26"
        bare
      />
    </div>

    <div class="icon-color-picker__rule" />

    <IconPicker
      v-model="icon"
      :icons="props.icons"
      :resolve="props.resolveIcon"
      :height="props.height"
      bare
    />
  </div>
</template>

<style scoped>
/* Лоток тот же, что у одиночных пикеров, — панель утоплена, содержимое лежит на ней. */
.icon-color-picker {
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  background: var(--surface-sunken);
  border: 1px solid var(--border-sunken);
  overflow: hidden;
}

/* Предпросмотр и палитра в одной полосе: цвет выбирают, глядя на плашку, а не на плитку. */
.icon-color-picker__head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
}

/* Та же плашка, что на карточке: результат обоих выборов, а не образец цвета. */
.icon-color-picker__preview {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  color: var(--gc-ink);
  background: var(--gc-fill);
}

/* Палитра занимает остаток полосы: плитки тянутся, и десять помещаются в один ряд. */
.icon-color-picker__head :deep(.color-picker) {
  flex: 1;
  min-width: 0;
}

/* Линейка во всю ширину лотка — та же роль, что у линии под шапкой окна: отделяет полосу
   выбора цвета от набора иконок. Отступы живут в полосах, а не на панели. */
.icon-color-picker__rule {
  height: 1px;
  background: var(--border);
}
</style>
