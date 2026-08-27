<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconArrowLeft, IconHome, IconRefresh, type Icon } from '@tabler/icons-vue'
import type { ErrorAction } from '@/constants/errors'

// Экран отказа: показывается ВМЕСТО содержимого, на том же адресе. Доступность —
// заголовок забирает фокус (иначе виртуальный курсор остаётся на ссылке, по которой кликнули,
// и «ничего не произошло» становится буквальным) и живой регион объявляет смену содержимого;
// `document.title` меняет вызывающий (гвард роутера).

const props = withDefaults(defineProps<{
  code?: string | null
  icon: Icon
  title: string
  description: string
  /** Выходы с экрана; последний рисуется главным действием. */
  actions?: ErrorAction[]
}>(), {
  code: null,
  actions: () => ['back', 'home'],
})

const router = useRouter()
const { t } = useI18n()

const headingRef = ref<HTMLElement | null>(null)
onMounted(() => headingRef.value?.focus())

const glyphs: Record<ErrorAction, Icon> = {
  back: IconArrowLeft,
  home: IconHome,
  retry: IconRefresh,
}

// Повтор — перезагрузка текущего адреса: сбой рендера или упавший бэкенд лечится свежим
// стартом, а не повторной навигацией внутри уже сломанного приложения.
const handlers: Record<ErrorAction, () => void> = {
  back: () => router.back(),
  home: () => router.push('/home'),
  retry: () => window.location.reload(),
}

function isPrimary(action: ErrorAction): boolean {
  return action === props.actions[props.actions.length - 1]
}
</script>

<template>
  <div class="error-state" role="alert" aria-live="polite">
    <component :is="icon" class="error-state__icon" :size="56" stroke="1.5" />
    <span v-if="code" class="error-state__code">{{ code }}</span>
    <h1 ref="headingRef" tabindex="-1" class="error-state__title">{{ title }}</h1>
    <p class="error-state__text">{{ description }}</p>

    <div class="error-state__actions">
      <VBtn
        v-for="action in actions"
        :key="action"
        :color="isPrimary(action) ? 'primary' : undefined"
        :variant="isPrimary(action) ? 'flat' : 'outlined'"
        size="large"
        @click="handlers[action]()"
      >
        <template #prepend>
          <component :is="glyphs[action]" :size="18" />
        </template>
        {{ t(`common.errors.action.${action}`) }}
      </VBtn>
    </div>
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 100%;
  padding: 24px;
}

.error-state__icon {
  color: var(--text-faint);
}

.error-state__code {
  margin-top: 12px;
  font-family: var(--font-mono);
  font-size: 56px;
  font-weight: 600;
  line-height: 1;
  color: var(--text);
}

.error-state__title {
  margin: 8px 0 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
}

/* Заголовок получает фокус программно, поэтому кольца ему не рисуем: человек с мышью его не
   вызывал, а для клавиатуры сразу следом идут настоящие кнопки. */
.error-state__title:focus {
  outline: none;
}

.error-state__text {
  margin: 8px 0 0;
  max-width: 420px;
  font-size: 14px;
  color: var(--text-muted);
}

.error-state__actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}
</style>
