<script setup lang="ts">
// Шапка модального окна: заголовок, необязательное описание, крестик и линия к контенту — по
// образцу формы оплаты. Линию держит шапка, а не контент: контентных блоков у окна бывает
// несколько (колонки чекаута, вкладки), шапка одна, и линия не должна зависеть от того, что под ней.
import { IconX } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

// Крестик рисуется ВСЕГДА и пропом не выключается: выход из окна не бывает необязательным, а
// у блокирующего он и вовсе единственный. Родитель обязан слушать `close`.
withDefaults(defineProps<{
  title: string
  /** Подзаголовок под заголовком. Без него шапка однострочная, линия остаётся. */
  description?: string
  /** Линия к контенту. Снимать только у окна БЕЗ контентного блока (`ConfirmDialog`). */
  rule?: boolean
  /** Идёт работа: закрывать нельзя, но крестик остаётся видимым. */
  closeDisabled?: boolean
}>(), {
  description: undefined,
  rule: true,
  closeDisabled: false,
})

const emit = defineEmits<{ (e: 'close'): void }>()

const { t } = useI18n()
</script>

<template>
  <header class="dlg-head" :class="{ 'dlg-head--rule': rule }">
    <div class="dlg-head__text">
      <h2 class="dlg-head__title">{{ title }}</h2>
      <p v-if="description" class="dlg-head__description">{{ description }}</p>
    </div>

    <VBtn
      icon
      variant="text"
      class="dlg-head__close"
      :disabled="closeDisabled"
      :title="t('common.action.close')"
      @click="emit('close')"
    >
      <IconX :size="18" />
    </VBtn>
  </header>
</template>

<style scoped>
/* Отступы и кегль сняты с формы оплаты — она и была образцом. */
.dlg-head {
  /* Крестик выше строки заголовка и без описания растил бы шапку на пустое место. Обе величины
     держим рядом: бокс кнопки задан явно, отрицательные поля ровно на разницу выводят её из
     расчёта высоты. Крестик встаёт по центру строки заголовка, высоту шапки задаёт текст. */
  --dlg-close-size: 42px;
  --dlg-title-line: 24px;
  --dlg-pad-y: 22px;
  --dlg-pad-x: 24px;
  --dlg-close-shift: calc((var(--dlg-title-line) - var(--dlg-close-size)) / 2);

  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: var(--dlg-pad-y) var(--dlg-pad-x) 18px;
}

.dlg-head--rule { border-bottom: 1px solid var(--border-soft); }

.dlg-head__title {
  margin: 0;
  font-size: 18px;
  line-height: var(--dlg-title-line);
  font-weight: 700;
  color: var(--text);
}

.dlg-head__description { margin: 4px 0 0; font-size: 13px; color: var(--text-muted); }

.dlg-head__close {
  flex: none;
  width: var(--dlg-close-size);
  height: var(--dlg-close-size);
  margin-block: var(--dlg-close-shift);
  /* Вправо ровно настолько, чтобы кромка кнопки отстояла от правого края так же, как от
     верхнего: сверху её положение уже сдвинуто на --dlg-close-shift. */
  margin-right: calc(var(--dlg-pad-y) + var(--dlg-close-shift) - var(--dlg-pad-x));
}
</style>
