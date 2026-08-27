<script setup lang="ts">
import { IconArrowLeft } from '@tabler/icons-vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'
import { useNavigationHistory } from '@/composables/useNavigationHistory'
import SectionHeader from '@/components/SectionHeader.vue'

// Шапка страницы = кнопка «назад» + заголовок первого уровня. Сам заголовок рисует
// SectionHeader: анатомия (заголовок, описание, правая часть, плейсхолдеры) одна на страницу
// и на секцию внутри неё, а странице принадлежит только возврат.
const props = defineProps<{
  title: string
  description?: string
  backTo?: RouteLocationRaw
  loading?: boolean
}>()

const router = useRouter()
const { goBack } = useNavigationHistory()
</script>

<template>
  <!-- Наличие описания читается ПРЯМО В РАЗМЕТКЕ, а не через computed поверх `useSlots()`: слоты
       не являются реактивной зависимостью, и computed, посчитанный на первом кадре (когда данных
       ещё нет и слот с `v-if` пуст), таким и остался бы навсегда. Разметка же пересчитывается
       на каждый рендер. -->
  <div class="page-header" :class="{ 'page-header--single-line': !(description || $slots.description) }">
    <div v-if="$slots.before || backTo" class="page-header__before">
      <slot name="before">
        <VBtn
          :icon="IconArrowLeft"
          variant="tonal"
          density="comfortable"
          rounded="0"
          class="page-header__back"
          @click="goBack(router, props.backTo!)"
        />
      </slot>
    </div>

    <SectionHeader :level="1" :title="title" :description="description" :loading="loading">
      <!-- Заголовок целиком отдаётся своему компоненту (правка названия на месте): пробрасываем
           слот SectionHeader как есть — метрику такой компонент задаёт себе сам. -->
      <template v-if="$slots.title" #title>
        <slot name="title" />
      </template>
      <template v-if="$slots.description" #description>
        <slot name="description" />
      </template>
      <template v-if="$slots.actions" #right>
        <slot name="actions" />
      </template>
    </SectionHeader>
  </div>
</template>

<style scoped>
/* Выравнивание зависит от того, есть ли под заголовком описание. С описанием — по ВЕРХУ: по центру
   кнопка уезжала бы к середине абзаца, то есть переставала бы стоять рядом с заголовком, к которому
   относится. Без описания строка одна, и верх ей не нужен: кнопка выше строки текста, и прижатый к
   её верхнему краю заголовок висел бы над серединой кнопки. */
.page-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: nowrap;
}

.page-header--single-line {
  align-items: center;
}

.page-header__before {
  display: flex;
  flex-shrink: 0;
}

/* Коробка задана здесь, а не пропом `size`: у иконочной кнопки Vuetify считает сторону как
   `--v-btn-height + 12px`, а `density` правит только высоту — обе ручки дают то прямоугольник, то
   размер крупнее нужного. Незаслоённое правило перебивает `@layer vuetify-components`
   (docs/frontend/vuetify-css-patterns). */
.page-header__back {
  width: 32px;
  min-width: 32px;
  height: 32px;
}

/* Заголовок подтягивается к кнопке: у неё своя внутренняя рамка отступа. */
.page-header__before + * {
  margin-left: -8px;
}

@media (max-width: 959px) {
  .page-header {
    flex-wrap: wrap;
  }
}
</style>
