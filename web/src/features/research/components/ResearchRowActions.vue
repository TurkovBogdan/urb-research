<script setup lang="ts">
// Действия над исследованием: меню и копирование кода. Вынесено из списка, потому что обе его
// раскладки — строка таблицы и карточка — предлагают ровно один и тот же набор.
//
// Компонент только спрашивает: окна держит список (одна пара на весь список, а не на строку),
// а отвязку он же и выполняет. Сюда приходит лишь признак «эта строка сейчас отвязывается».
import { useI18n } from 'vue-i18n'
import {
  IconCheck,
  IconCopy,
  IconDotsVertical,
  IconFileText,
  IconFolderPlus,
  IconFolderX,
  IconLayoutGrid,
  IconTrash,
} from '@tabler/icons-vue'

import { useClipboard } from '@/composables/useClipboard'

import type { ResearchListRow } from '../api'

const props = defineProps<{
  research: ResearchListRow
  /** Отвязка ИМЕННО этого исследования в полёте: пункт заперт от второго клика. */
  detaching?: boolean
}>()

const emit = defineEmits<{ group: []; detach: []; remove: [] }>()

const { t } = useI18n()
const { copy, isCopied } = useClipboard()

// Один сегмент на оба кода: RESEARCH@ открывает карточку исследования, GROUP@ — список группы
// (маршруты разведены префиксом, см. routes.ts).
const researchesPath = (code: string) => `/research/researches/${code}`
</script>

<template>
  <!-- Клик по действиям не должен уводить на карточку исследования: и строка, и плитка целиком
       являются ссылкой на неё. -->
  <div class="row-actions" @click.stop>
    <VMenu location="bottom start" :offset="4">
      <template #activator="{ props: menu }">
        <VBtn
          v-bind="menu"
          icon
          variant="text"
          class="row-actions__btn"
          :title="t('research.research.action.actions')"
        >
          <IconDotsVertical :size="16" :stroke-width="1.6" />
        </VBtn>
      </template>

      <VList density="compact" class="row-actions__menu">
        <VListItem :prepend-icon="IconFileText" :to="researchesPath(props.research.code)">
          <VListItemTitle>{{ t('research.research.action.open_card') }}</VListItemTitle>
        </VListItem>
        <VListItem
          :prepend-icon="IconLayoutGrid"
          :disabled="!props.research.group_code"
          :to="props.research.group_code ? researchesPath(props.research.group_code) : undefined"
        >
          <VListItemTitle>{{ t('research.research.action.open_group') }}</VListItemTitle>
        </VListItem>

        <VDivider class="my-1" />

        <!-- Привязать и сменить — одно окно: у них общее поле, разный только заголовок. -->
        <VListItem :prepend-icon="IconFolderPlus" @click="emit('group')">
          <VListItemTitle>
            {{ props.research.group_code
              ? t('research.research.action.move_group')
              : t('research.research.action.set_group') }}
          </VListItemTitle>
        </VListItem>
        <VListItem
          v-if="props.research.group_code"
          :prepend-icon="IconFolderX"
          :disabled="props.detaching"
          @click="emit('detach')"
        >
          <VListItemTitle>{{ t('research.research.action.unset_group') }}</VListItemTitle>
        </VListItem>

        <VDivider class="my-1" />

        <VListItem
          :prepend-icon="IconTrash"
          class="row-actions__danger"
          @click="emit('remove')"
        >
          <VListItemTitle>{{ t('research.research.action.delete') }}</VListItemTitle>
        </VListItem>
      </VList>
    </VMenu>

    <VBtn
      icon
      variant="text"
      class="row-actions__btn"
      :title="isCopied(props.research.code)
        ? t('research.research.action.copied')
        : t('research.research.action.copy')"
      @click="copy(props.research.code)"
    >
      <IconCheck
        v-if="isCopied(props.research.code)"
        :size="16"
        :stroke-width="1.6"
        class="row-actions__btn--done"
      />
      <IconCopy v-else :size="16" :stroke-width="1.6" />
    </VBtn>
  </div>
</template>

<style scoped>
/* Обе кнопки — одна группа управления, поэтому между собой они теснее, чем до края ячейки. */
.row-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* Коробка задана здесь, а не пропсами `size`/`density`: у иконочной кнопки Vuetify считает сторону
   как `--v-btn-height + 12px`, а density правит только высоту. Незаслоённое правило перебивает
   `@layer vuetify-components` (см. docs/frontend/vuetify-css-patterns). */
.row-actions__btn {
  width: 26px;
  min-width: 26px;
  height: 26px;
  color: var(--text-faint);
}

.row-actions__btn:hover { color: var(--text); }

.row-actions__btn--done { color: var(--success); }

/* Vuetify отбивает иконку пункта от подписи на 32px (под аватарки) — в узком меню это читается
   как два несвязанных столбца. */
.row-actions__menu {
  --v-list-prepend-gap: 10px;
}

/* Необратимый пункт назван цветом ещё до нажатия — иконка тоже, иначе подпись выглядит
   подкрашенной по ошибке. */
.row-actions__danger {
  color: var(--error);
}
</style>
