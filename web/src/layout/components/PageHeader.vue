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
  <div class="page-header">
    <div v-if="$slots.before || backTo" class="page-header__before">
      <slot name="before">
        <VBtn
          :icon="IconArrowLeft"
          variant="tonal"
          density="default"
          rounded="0"
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
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: nowrap;
}

.page-header__before {
  display: flex;
  align-items: center;
  flex-shrink: 0;
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
