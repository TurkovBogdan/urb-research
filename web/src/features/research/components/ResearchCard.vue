<script setup lang="ts">
// Плитка исследования: название, описание, полка и дата. Вынесена из списка, потому что раскладок
// с плитками две — общий поток и разложенные по полкам, — и обе показывают ровно одну и ту же
// плитку. Решения (куда вести, что перезагружать) остаются у списка: плитка только сообщает.
import { useI18n } from 'vue-i18n'

import { fmtDateTime } from '@/shared/utils/date'

import ResearchRowActions from './ResearchRowActions.vue'
import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'
import type { ResearchListRow } from '../api'

const DESCRIPTION_MAX = 128

const props = withDefaults(defineProps<{
  research: ResearchListRow
  /** Разложенным по полкам плашка не нужна: полку уже назвал заголовок раздела. */
  withGroup?: boolean
  /** Плашка полки — ещё и фильтр; там, где список уже сужен полкой, она просто метка. */
  groupFilterable?: boolean
}>(), {
  withGroup: true,
  groupFilterable: false,
})

const emit = defineEmits<{
  open: []
  rename: []
  group: []
  detach: []
  remove: []
  'filter-group': [string]
}>()

const { t } = useI18n()

const truncate = (s: string, n: number) => (s.length > n ? s.slice(0, n) + '…' : s)
</script>

<template>
  <!-- Цвет полки лежит на самой плитке: им красится и плашка полки, и обводка на наведении —
       исследование выделяется цветом того, где оно лежит. Без полки переменных нет, и запасной
       путь оставляет акцент. -->
  <VCard
    variant="outlined"
    rounded="lg"
    class="card color-tones"
    :style="groupColorVars(props.research.group_color)"
    @click="emit('open')"
  >
    <div class="card__head">
      <h3 class="card__title">{{ props.research.title }}</h3>
      <ResearchRowActions
        :research="props.research"
        @rename="emit('rename')"
        @group="emit('group')"
        @detach="emit('detach')"
        @remove="emit('remove')"
      />
    </div>

    <p v-if="props.research.description" class="card__desc">
      {{ truncate(props.research.description, DESCRIPTION_MAX) }}
    </p>

    <!-- Полка своей плашкой, как на карточке самой полки: иконка в цвете группы плюс имя.
         Без полки подвал несёт только дату — пустой плашки «без группы» тут не нужно, её
         отсутствие и есть ответ. -->
    <footer class="card__foot">
      <button
        v-if="props.withGroup && props.research.group_code"
        type="button"
        class="card__group"
        :class="{ 'card__group--filter': props.groupFilterable }"
        :disabled="!props.groupFilterable"
        :title="props.groupFilterable
          ? t('research.research.action.filter_group', { title: props.research.group_name })
          : undefined"
        @click.stop="emit('filter-group', props.research.group_code)"
      >
        <span class="card__group-icon">
          <component :is="groupIcon(props.research.group_icon)" :size="14" :stroke-width="1.7" />
        </span>
        {{ props.research.group_name }}
      </button>
      <span class="card__date">{{ fmtDateTime(props.research.updated_at) }}</span>
    </footer>
  </VCard>
</template>

<style scoped>
/* Плитка одной высоты с соседками по ряду, а дата и группа прижаты к её низу: иначе подвал
   гулял бы по вертикали от длины описания, и ряд читался бы как набор разных карточек. */
.card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  transition: border-color 0.12s ease, background 0.12s ease;
}

/* Обводка на наведении — цвет полки; без полки остаётся акцент (тот же запасной путь, что у
   кликабельных карточек в main.scss). */
.card:hover {
  border-color: var(--gc-ink, var(--accent));
  background: var(--surface-hi);
}

/* Действия прижаты к правому краю и выровнены по ПЕРВОЙ строке названия: у длинного заголовка
   центрирование увело бы их в середину плитки. */
.card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
}

.card__desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-muted);
}

/* Подвал прижат к низу плитки: описание бывает и в строку, и в три, а ряд плиток должен
   заканчиваться одной линией. */
.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border-soft);
}

/* Полка названа иконкой в своём цвете + именем. Цвет несёт только иконка: именем он читался бы
   как выделение, а плашка на всё имя спорила бы с рамкой самой плитки. */
.card__group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  font-size: 11px;
  text-align: left;
  color: var(--text-muted);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Плашка-фильтр отзывается на наведение — иначе её от простой метки не отличить. */
.card__group--filter {
  cursor: pointer;
}

.card__group--filter:hover {
  color: var(--text);
}

.card__group-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  flex: none;
  /* Цвет полки, а без него — акцент: тот же запасной путь, что у карточки самой полки. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
}

.card__date {
  margin-left: auto;
  font-size: 11px;
  white-space: nowrap;
  color: var(--text-faint);
}
</style>
