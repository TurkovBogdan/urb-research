<script setup lang="ts">
import { onActivated, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  IconCheck,
  IconCopy,
  IconDotsVertical,
  IconPencil,
  IconPlus,
  IconRefresh,
  IconTrash,
} from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import { useClipboard } from '@/composables/useClipboard'
import { groupColorVars } from '../constants/groupColors'
import { GROUP_ICON_FALLBACK, groupIcon } from '../constants/groupIcons'
import GroupFormDialog from '../components/GroupFormDialog.vue'
import GroupDeleteDialog from '../components/GroupDeleteDialog.vue'
import { useGroupsStore } from '../stores/groups.store'
import { UNGROUPED_CODE, type GroupListRow } from '../api'

const { t } = useI18n()
const store = useGroupsStore()

// Копируется код с префиксом (GROUP@…) — ровно в таком виде его понимают MCP-тулы, ради них
// кнопка и нужна: полка заводится руками, а сослаться на неё надо из переписки с агентом.
const { copy, isCopied } = useClipboard()

onActivated(store.load)

// Код приходит уже с типовым префиксом (GROUP@…) — он и есть сегмент адреса полки; у
// псевдо-полки «Без группы» хеш пустой, путь тот же. Кодировать код НЕЛЬЗЯ: `@` в пути
// разрешён (RFC 3986), а `%40` не совпадает с регуляркой маршрута `GROUP@.*` — адрес тогда
// уходит во вьюху исследования. Ссылка, а не обработчик клика: карточка обязана быть <a>,
// иначе нет ни средней кнопки, ни «открыть в новой вкладке».
const groupPath = (code: string) => `/research/researches/${code}`

const editing = ref<GroupListRow | null>(null)
const removing = ref<GroupListRow | null>(null)
const formOpen = ref(false)
const deleteOpen = ref(false)

// Создание и правка — одно окно: пустая карточка отличается от заполненной только тем,
// что группы у неё пока нет.
function create() {
  editing.value = null
  formOpen.value = true
}

function edit(group: GroupListRow) {
  editing.value = group
  formOpen.value = true
}

function remove(group: GroupListRow) {
  removing.value = group
  deleteOpen.value = true
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.group.list.title')"
      :description="t('research.group.list.description')"
    >
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="store.load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
        <VBtn color="primary" variant="flat" @click="create">
          <template #prepend><IconPlus :size="16" /></template>
          {{ t('research.group.list.add') }}
        </VBtn>
      </template>
    </PageHeader>

    <div v-if="store.loading" class="group-grid">
      <VCard v-for="n in 3" :key="n" variant="flat" class="group-card skel-card">
        <VSkeletonLoader type="heading, text, text" />
      </VCard>
    </div>

    <SectionError v-else-if="store.error" :error="store.error" />

    <div v-else class="group-grid">
      <VCard
        v-for="group in store.items"
        :key="group.code"
        variant="flat"
        class="group-card"
        :to="groupPath(group.code)"
      >
        <header class="group-card__header">
          <span class="group-card__icon color-tones" :style="groupColorVars(group.color)">
            <component :is="groupIcon(group.icon)" :size="20" :stroke-width="1.6" />
          </span>
          <h3 class="group-card__title">{{ group.title }}</h3>

          <!-- Кнопки внутри ссылки-карточки: без остановки события клик уводил бы на полку. -->
          <VBtn
            icon
            variant="text"
            class="group-card__action"
            :title="isCopied(group.code) ? t('research.group.card.copied') : t('research.group.card.copy')"
            @click.stop.prevent="copy(group.code)"
          >
            <IconCheck
              v-if="isCopied(group.code)"
              :size="16"
              :stroke-width="1.6"
              class="group-card__action--done"
            />
            <IconCopy v-else :size="16" :stroke-width="1.6" />
          </VBtn>

          <VMenu location="bottom end" :offset="4">
            <template #activator="{ props: menu }">
              <VBtn
                v-bind="menu"
                icon
                variant="text"
                class="group-card__action group-card__action--last"
                :title="t('research.group.card.actions')"
                @click.stop.prevent
              >
                <IconDotsVertical :size="16" :stroke-width="1.6" />
              </VBtn>
            </template>

            <VList density="compact" class="group-card__menu-list">
              <VListItem :prepend-icon="IconPencil" @click="edit(group)">
                <VListItemTitle>{{ t('common.action.edit') }}</VListItemTitle>
              </VListItem>
              <VListItem :prepend-icon="IconTrash" class="group-card__menu-danger" @click="remove(group)">
                <VListItemTitle>{{ t('research.group.card.delete') }}</VListItemTitle>
              </VListItem>
            </VList>
          </VMenu>
        </header>

        <p class="group-card__desc">{{ group.description }}</p>

        <footer class="group-card__footer">
          <span class="group-card__count">{{ group.research_count }}</span>
          <span class="group-card__count-label">{{ t('research.group.card.researches') }}</span>
        </footer>
      </VCard>

      <!-- Полка, которой нет в БД: сюда попадает всё, что не разложено. Всегда последняя и
           приглушена — это не выбор пользователя, а остаток. -->
      <VCard
        variant="flat"
        class="group-card group-card--auto"
        :to="groupPath(UNGROUPED_CODE)"
      >
        <header class="group-card__header">
          <span class="group-card__icon">
            <component :is="GROUP_ICON_FALLBACK" :size="20" :stroke-width="1.6" />
          </span>
          <h3 class="group-card__title">{{ t('research.group.ungrouped.title') }}</h3>
        </header>

        <p class="group-card__desc">{{ t('research.group.ungrouped.description') }}</p>

        <footer class="group-card__footer">
          <span class="group-card__count">{{ store.ungroupedCount }}</span>
          <span class="group-card__count-label">{{ t('research.group.card.researches') }}</span>
        </footer>
      </VCard>
    </div>

    <GroupFormDialog v-model="formOpen" :group="editing" @saved="store.load" />
    <GroupDeleteDialog
      v-model="deleteOpen"
      :group="removing"
      :groups="store.items"
      @deleted="store.load"
    />
  </PageLayout>
</template>

<style scoped>
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}

.skel-card { min-height: 132px; }
.skel-card :deep(.v-skeleton-loader) { width: 100%; padding: 0; }

.group-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  cursor: pointer;
  transition: background-color 120ms ease;
}

.group-card:hover { background: var(--surface-hi); }

/* Автоматическая полка отличается от настоящих: пунктир вместо заливки-плашки у иконки. */
.group-card--auto .group-card__icon {
  color: var(--text-muted);
  background: transparent;
  border: 1px dashed var(--border);
}

.group-card--auto .group-card__title { color: var(--text-muted); }

.group-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  /* Цвет полки, а без него — акцент: у псевдо-полки «Без группы» его и не может быть. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
  flex: none;
}

.group-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

/* Коробка задана здесь, а не пропсами `size`/`density`: у иконочной кнопки Vuetify считает сторону
   как `--v-btn-height + 12px`, а density правит только высоту — обе ручки дают то прямоугольник,
   то размер крупнее исходного. Незаслоённое правило перебивает `@layer vuetify-components`
   (см. docs/frontend/vuetify-css-patterns), поэтому хватает обычного объявления.
   Крайняя правая утоплена вбок: иначе её кромка съезжает вправо от края текста. */
.group-card__action {
  width: 26px;
  min-width: 26px;
  height: 26px;
  color: var(--text-faint);
}

.group-card__action--last { margin-right: -4px; }

/* Отбивка шапки (10px) разделяет заголовок и кнопки, но между собой кнопки — одна группа
   управления, и та же величина рвала бы её надвое. */
.group-card__action + .group-card__action {
  margin-left: -6px;
}

.group-card__action:hover { color: var(--text); }

/* Отметка «скопировано» держится полторы секунды — цвет успеха отличает её от обычного ховера. */
.group-card__action--done { color: var(--success); }

/* Vuetify отбивает иконку пункта от подписи на 32px (`--v-list-prepend-gap` по умолчанию, под
   аватарки) — в узком выпадающем меню это читается как два несвязанных столбца. Десять — как
   в боковом меню, которое ту же отбивку правит у себя (`main.scss`). */
.group-card__menu-list {
  --v-list-prepend-gap: 10px;
}

.group-card__menu-danger :deep(.v-list-item-title) { color: var(--error); }
.group-card__menu-danger :deep(.v-list-item__prepend) { color: var(--error); }

/* Счётчик прижат к низу карточки — карточки в ряду выравниваются по нижней границе. */
.group-card__footer {
  display: flex;
  align-items: baseline;
  gap: 6px;
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: auto;
}

.group-card__count {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  line-height: 1;
}

.group-card__count-label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

/* Описание фиксировано на две строки: короткие резервируют высоту, длинные обрезаются
   многоточием — карточки в ряду выравниваются по высоте (как на /connectors). */
.group-card__desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: -6px 0 0;
  min-height: calc(1.5em * 2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
