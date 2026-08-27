<script setup lang="ts">
import { computed } from 'vue'

// Заголовок секции — внутристраничный родственник PageHeader: заголовок и необязательное
// описание слева, необязательный слот справа (счётчик, кнопка, бейдж). `level` задаёт И
// семантический тег (h1…h6), И кегль, поэтому вложенные секции дают правильную структуру
// документа, а не набор одинаковых строк.
//
// Кнопку «назад» сюда НЕ кладут: она принадлежит странице, а не секции внутри неё, и живёт
// в PageHeader — тот собран поверх этого же компонента (level 1), чтобы анатомия заголовка
// была одна на оба уровня.
const props = withDefaults(defineProps<{
  title?: string
  description?: string
  level?: 1 | 2 | 3 | 4 | 5 | 6
  /** Число рядом с заголовком: сколько всего элементов в секции. */
  count?: number
  /** Данные ещё едут — вместо заголовка и описания идут плейсхолдеры их размера. */
  loading?: boolean
}>(), {
  title: '',
  description: undefined,
  level: 2,
  count: undefined,
  loading: false,
})

const tag = computed(() => `h${props.level}` as const)
</script>

<template>
  <div class="section-header" :class="`section-header--l${level}`">
    <div class="section-header__text">
      <template v-if="loading">
        <VSkeletonLoader type="heading" class="section-header__skel section-header__skel--title" />
        <VSkeletonLoader type="text" class="section-header__skel section-header__skel--desc" />
      </template>

      <template v-else>
        <!-- `title` — слот на случай, когда заголовок не текст, а свой компонент. Замещается
             ВЕСЬ элемент вместе с тегом: такому компоненту нужна полная власть над метрикой,
             иначе <h*> навяжет ему свой кегль и отступы. -->
        <slot name="title">
          <component :is="tag" class="section-header__title">
            {{ title }}
            <span v-if="count !== undefined" class="section-header__count">{{ count }}</span>
          </component>
        </slot>
        <p v-if="description || $slots.description" class="section-header__desc">
          <slot name="description">{{ description }}</slot>
        </p>
      </template>
    </div>

    <div v-if="$slots.right" class="section-header__right">
      <slot name="right" />
    </div>
  </div>
</template>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.section-header__text {
  min-width: 0;
}

.section-header__title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--text);
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.3;
}

/* Отбивка секции внутри страницы. Первому уровню её не даём: там расстоянием до содержимого
   распоряжается шапка страницы, и вторая величина в том же месте разъехалась бы с первой. */
.section-header:not(.section-header--l1) {
  margin: 4px 0 10px;
}

/* Кегль — функция уровня: семантика и вес задаются одной ручкой. */
.section-header--l1 .section-header__title { font-size: 18px; }
.section-header--l2 .section-header__title { font-size: 14px; }
.section-header--l3 .section-header__title { font-size: 13px; }
.section-header--l4 .section-header__title,
.section-header--l5 .section-header__title,
.section-header--l6 .section-header__title { font-size: 12px; }

.section-header__count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-faint);
}

.section-header__desc {
  margin: 3px 0 0;
  max-width: 640px;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.5;
}

.section-header__right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Плейсхолдеры повторяют метрику заголовка и описания. Ширину костей Vuetify ставит инлайном
   (100% загрузчика), поэтому ограничиваем корень, а у кости трогаем только высоту и отступ. */
.section-header__skel { padding: 0; background: transparent; }
.section-header__skel--title { width: 280px; max-width: 55%; }
.section-header__skel--desc  { width: 180px; max-width: 38%; }
.section-header__skel--title :deep(.v-skeleton-loader__bone) { height: 16px; margin: 3px 0; }
.section-header__skel--desc  :deep(.v-skeleton-loader__bone) { height: 10px; margin: 8px 0 0; }

/* На самых узких экранах правая часть уходит под текст. */
@media (max-width: 599px) {
  .section-header {
    flex-wrap: wrap;
    align-items: flex-start;
  }
  .section-header__right {
    width: 100%;
  }
}
</style>
