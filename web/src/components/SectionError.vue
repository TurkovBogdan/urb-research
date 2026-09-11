<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconAlertTriangle, IconSearchOff } from '@tabler/icons-vue'
import { ApiError } from '@/api/client/internal'
import { errorText } from '@/api/errorText'

// Отказ ЧТЕНИЯ раздела: сущности нет, список не загрузился. Экран во весь шелл здесь не даётся
// — навигация жива, человек пришёл по верному адресу, и меню с шапкой обязаны остаться на месте.
// Показывается на месте содержимого: почему пусто и что делать дальше.
//
// Отказ ОПЕРАЦИИ сюда не попадает никогда — он всплывает сообщением рядом с действием.

const props = defineProps<{ error: unknown }>()

const { t } = useI18n()

const missing = computed(() => props.error instanceof ApiError && props.error.status === 404)

// Заголовок общий, предметное существительное приносит сам ответ бэкенда («Исследование не
// найдено») — оно и печатается строкой ниже, поэтому дублировать его пропом незачем.
const title = computed(() => (
  missing.value ? t('common.errors.section.missing') : t('common.errors.section.failed')
))
</script>

<template>
  <div class="section-error" role="alert" aria-live="polite">
    <component
      :is="missing ? IconSearchOff : IconAlertTriangle"
      class="section-error__icon"
      :size="40"
      stroke="1.5"
    />
    <p class="section-error__title">{{ title }}</p>
    <p class="section-error__text">{{ errorText(error) }}</p>
    <slot name="actions" />
  </div>
</template>

<style scoped>
.section-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  padding: 48px 24px;
}

.section-error__icon {
  color: var(--text-faint);
  margin-bottom: 6px;
}

.section-error__title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.section-error__text {
  margin: 0;
  max-width: 420px;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
