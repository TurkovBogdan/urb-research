<script setup lang="ts">
// Шапка содержимого деталки: имя объекта слева, действия над ним справа.
//
// Общая на все деталки ради одного: действия стоят в ОДНОМ И ТОМ ЖЕ месте на каждой странице —
// у правого края первой строки содержимого. Кнопка, которая переезжает от страницы к странице,
// каждый раз ищется заново; кнопка на своём месте не ищется вовсе.
//
// Само имя компонент не рисует: у исследования это правка на месте, у источника — заголовок с
// адресом, у заметки — имя с видом. Он владеет строкой и её правым краем, а что стоит слева —
// дело страницы.
import { useI18n } from 'vue-i18n'
import { IconDotsVertical, IconRefresh } from '@tabler/icons-vue'

import CopyCodeButton from '@/components/CopyCodeButton.vue'

withDefaults(defineProps<{
  /** Код объекта. Пока его нет (страница грузится), кнопки копирования нет. */
  code?: string
  /** Перечитывание в полёте: кнопка заперта, иконка вращается. */
  loading?: boolean
}>(), {
  code: '',
  loading: false,
})

const emit = defineEmits<{ refresh: [] }>()

const { t } = useI18n()
</script>

<template>
  <header class="detail-head">
    <!-- Над именем — где объект лежит: полка исследования, а у вложенных объектов их место в
         дереве. Пусто — строки нет вовсе. -->
    <div class="detail-head__above">
      <slot name="above" />
    </div>

    <div class="detail-head__name">
      <slot />
    </div>

    <!-- Действия страницы стоят справа от её заголовка — то же место и та же кнопка, что в
         `PageHeader` у списков (`variant="text"`, кегль по умолчанию, иконка 16): деталка и список
         различаются содержимым, а не тем, где искать «Обновить».
         Порядок слева направо — от объекта к странице: сначала «забрать код», потом «перечитать». -->
    <div class="detail-head__actions">
      <slot name="actions" />
      <CopyCodeButton v-if="code" :code="code" />
      <VBtn variant="text" :disabled="loading" @click="emit('refresh')">
        <template #prepend>
          <IconRefresh :size="16" :class="{ 'icon-spin': loading }" />
        </template>
        {{ t('common.action.refresh') }}
      </VBtn>

      <!-- Последней — редкое: то, что делают раз в жизнь объекта, не заслуживает собственной
           кнопки в шапке, но и прятать его в неподписанное многоточие незачем. Кнопку и список
           держит компонент, пункты кладёт страница — их набор знает только она. -->
      <VMenu v-if="$slots.more" location="bottom end" :offset="4">
        <template #activator="{ props: menu }">
          <VBtn v-bind="menu" variant="text">
            <template #prepend><IconDotsVertical :size="16" /></template>
            {{ t('common.action.more') }}
          </VBtn>
        </template>
        <VList density="compact">
          <slot name="more" />
        </VList>
      </VMenu>
    </div>
  </header>
</template>

<style scoped>
/* Две колонки: слева объект (где лежит и как называется), справа действия над ним. Действия —
   колонка, а не ячейка первой строки: они относятся ко всей шапке, и приклеенные к строке полки
   они выравнивались бы по мелкой надписи над именем, а не по самому имени. */
/* Строки объявлены явно: без них сетка неявная, и `grid-row: 1 / -1` у действий ссылается на
   последнюю линию ЯВНОЙ сетки — то есть на первую же, — отчего они молча прилипают к строке полки
   вместо того, чтобы встать на всю высоту. */
/* У имени есть нижняя граница ширины: без неё колонка действий (три подписанных кнопки) отбирала
   всё, и на окне 1233px имени оставалось 144px — заголовок рассыпался на пять строк. Упёршись в
   эту границу, переносятся кнопки, а не имя: их две-три, и второй ряд читается, а имя в пять
   строк — нет. */
.detail-head {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto;
  grid-template-rows: auto auto;
  column-gap: 12px;
  row-gap: 2px;
  min-width: 0;
  margin-bottom: 16px;
}

.detail-head__above {
  grid-column: 1;
  min-width: 0;
  display: flex;
}

.detail-head__name {
  grid-column: 1;
  min-width: 0;
}

/* Место названо явно: в разметке действия идут ПОСЛЕ имени (сначала о чём страница, потом что с
   ней делать — так её читает и скринридер), а стоят справа во всю высоту шапки. */
.detail-head__actions {
  grid-row: 1 / -1;
  grid-column: 2;
  align-self: center;
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
