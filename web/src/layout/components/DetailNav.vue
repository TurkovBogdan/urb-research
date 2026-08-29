<script setup lang="ts">
// Навигация страницы-деталки: первая плашка липкой колонки.
//
// Стоит на месте, которое у списков занимает шапка, и держится на экране всю длину документа —
// поэтому доступна из любой точки чтения, а не только с начала страницы.
//
// Своё дело у неё одно — уйти отсюда; действия над объектом живут рядом с его именем в содержимом.
// Но плашка принимает и то, чем страница пользуется на всей длине чтения (поиск по документу):
// такие инструменты стоят ПОД выходом в той же карточке, а не отдельной рамкой под ней — две
// плашки подряд читаются как два разных блока, хотя дело у них одно, колонка.
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconChevronLeft, IconSettings } from '@tabler/icons-vue'

import { useNavigationHistory } from '@/composables/useNavigationHistory'

import DocumentAppearance from './DocumentAppearance.vue'

const props = withDefaults(defineProps<{
  /** Куда уйти, когда истории нет: ближайший родитель в дереве. */
  parent: string
  /** Имя запасного места — «К списку исследований». Стоит на кнопке только тогда, когда уходить
      придётся туда: при заходе по прямой ссылке. Без него всегда «Назад». */
  label?: string
  /** Страница показывает документ: в строке выхода появляется шестерёнка его оформления. */
  appearance?: boolean
}>(), {
  label: '',
  appearance: false,
})

const { t } = useI18n()
const router = useRouter()
const { goBack, hasHistory } = useNavigationHistory()

// Подпись называет то, что кнопка сделает. По истории она возвращает «туда, откуда пришли» — это
// и есть «Назад», а обещать при этом список исследований нельзя: пришли-то могли из зоны. Имя
// места остаётся за запасным адресом, по которому уходят при заходе по прямой ссылке.
const backLabel = computed(() =>
  hasHistory.value ? t('common.action.back') : props.label || t('common.action.back'),
)

// Выход один на страницу: откуда пришли, туда и уходим. Списка мест выше по дереву нет — путь
// наверх проходится теми же нажатиями, каждое из которых снимает один уровень. Прямой заход
// истории не оставляет, и тогда «назад» означает «на уровень выше».
function back(): void {
  goBack(router, props.parent)
}

// Поля оформления закрыты по умолчанию и разворачиваются в колонке, а не в окне: их крутят,
// глядя на текст рядом, и окно закрывало бы ровно то, ради чего их и трогают.
const appearanceOpen = ref(false)
</script>

<template>
  <VCard variant="outlined" rounded="lg" class="detail-nav">
    <div class="detail-nav__row">
      <!-- Уголок на своей плашке: одна линия без древка — на 28px стрелка с хвостом читается как
           чертёж, а «влево» она говорит и без него. Плашка и подпись — один элемент, а не кнопка
           рядом с текстом: дело у них одно, и двумя остановками табуляции оно бы не стало понятнее. -->
      <button type="button" class="detail-nav__back" @click="back">
        <span class="detail-nav__glyph"><IconChevronLeft :size="18" :stroke-width="1.6" /></span>
        {{ backLabel }}
      </button>

      <!-- Шестерёнка без подписи: она не про эту страницу, а про то, КАК её показывать, и
           подпись поставила бы её в один ряд с выходом. Открытое состояние держит сама кнопка. -->
      <VBtn
        v-if="appearance"
        icon
        variant="text"
        class="detail-nav__gear"
        :active="appearanceOpen"
        :title="t('settings.interface.group.document.title')"
        @click="appearanceOpen = !appearanceOpen"
      >
        <IconSettings :size="18" :stroke-width="1.6" />
      </VBtn>
    </div>

    <!-- Линейка отделяет выход от инструментов чтения: одно уводит со страницы, другое работает
         внутри неё. Концы уходят под отбивку — она делит карточку, а не лежит в ней. -->
    <template v-if="$slots.default">
      <VDivider class="detail-nav__rule" />
      <slot />
    </template>
  </VCard>

  <!-- Поля оформления — отдельная карточка ПОД плашкой, а не в ней: они появляются и уходят, и
       внутри общей рамки это выглядело бы как выросшая навигация. -->
  <VExpandTransition>
    <DocumentAppearance v-if="appearance && appearanceOpen" />
  </VExpandTransition>
</template>

<style scoped>
.detail-nav {
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  flex: none;
}

.detail-nav__rule {
  margin: 0 -12px;
}

/* Выход занимает строку, шестерёнка прижата к её правому краю: она не второй выход, а настройка
   показа, и стоит там же, где действия страницы в шапке содержимого. */
.detail-nav__row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.detail-nav__row .detail-nav__back {
  flex: 1;
}

/* Коробка задана здесь, а не пропсами: у иконочной кнопки Vuetify считает сторону как
   `--v-btn-height + 12px`, а density правит только высоту (см. docs/frontend/vuetify-css-patterns).
   Сторона — те же 28px, что у плашки выхода напротив. */
.detail-nav__gear {
  width: 28px;
  min-width: 28px;
  height: 28px;
  flex: none;
  color: var(--text-faint);
}

.detail-nav__gear:hover {
  color: var(--text);
}

/* Сброс оформления кнопки: браузер рисует ей серую плашку с рамкой, а нужен ряд «фигура + текст». */
.detail-nav__back {
  appearance: none;
  border: 0;
  background: transparent;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-family: var(--font);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  text-align: left;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.14s ease;
}

.detail-nav__back:hover {
  color: var(--text);
}

/* Та же фигура, что у возврата в `PageHeader` (`variant="tonal"` = свой цвет под 8%), только на
   28px вместо 32: в колонке она стоит рядом с текстом, а не одна перед заголовком страницы. */
.detail-nav__glyph {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex: none;
  border-radius: var(--radius-sm);
  background: color-mix(in oklab, currentColor 8%, transparent);
  transition: background-color 0.14s ease;
}
</style>
