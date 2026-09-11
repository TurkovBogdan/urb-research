<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
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

// Выравнивание решает не разметка, а замер: заголовок бывает с надзаголовком, с описанием и
// просто длинным — на глаз эти случаи не различить, а правило одно. Пока текст умещается в
// высоту соседа, обе коробки центруются друг по другу; как только текст соседа перерос (вторая
// строка, надзаголовок, описание), он читается сверху вниз, и сосед встаёт по его верхней кромке.
//
// Сосед — кнопка «назад», а если её нет, мерка сама строка заголовка: на странице без возврата
// вопрос стоит уже не про кнопку, а про действия справа, и «текст перерос своё имя» — это ровно
// «под именем что-то есть».
//
// Меряется текстовая половина, а не заголовок целиком: правая часть с действиями одна сделала бы
// «переросшим» любой заголовок. Классы чужие (`SectionHeader`), но эти двое и так одна анатомия —
// шапка собрана поверх него.
const root = ref<HTMLElement | null>(null)
const textFitsItsNeighbour = ref(true)

let sizeWatcher: ResizeObserver | undefined

function measuredParts(): { text: HTMLElement; reference: HTMLElement } | null {
  const text = root.value?.querySelector('.section-header__text')
  const reference =
    root.value?.querySelector('.page-header__before') ??
    root.value?.querySelector('.section-header__title')
  if (!(text instanceof HTMLElement) || !(reference instanceof HTMLElement)) return null
  return { text, reference }
}

function syncAlignment(): void {
  const parts = measuredParts()
  if (!parts) return
  textFitsItsNeighbour.value = parts.text.offsetHeight <= parts.reference.offsetHeight
}

onMounted(() => {
  const parts = measuredParts()
  if (!parts) return

  sizeWatcher = new ResizeObserver(syncAlignment)
  sizeWatcher.observe(parts.text)
  sizeWatcher.observe(parts.reference)
  syncAlignment()
})

onBeforeUnmount(() => sizeWatcher?.disconnect())
</script>

<template>
  <div ref="root" class="page-header" :class="{ 'page-header--single-line': textFitsItsNeighbour }">
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
/* По умолчанию — по ВЕРХУ: заголовок с надзаголовком, описанием или просто переносом читается
   сверху вниз, и кнопка принадлежит его первой строке, а не середине абзаца. Исключение считает
   скрипт: пока текст умещается в высоту кнопки, они центруются друг по другу — прижатая к верху
   одинокая строка висела бы над серединой кнопки. */
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
