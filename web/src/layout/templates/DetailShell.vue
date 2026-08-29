<script setup lang="ts">
// Рамка всех деталок сразу: колонка навигации слева, содержимое справа.
//
// Стоит на маршруте-родителе, поэтому переход с исследования на его зону не пересобирает страницу
// целиком — уезжает и приезжает только правая половина, а колонка остаётся на месте и
// перестраивается: подпись выхода, поиск и оглавление приходят из реестра (`detailRail`), который
// заполняет пришедшая страница. Раньше колонку рисовала каждая вьюха сама, и на каждом переходе
// она исчезала вместе с содержимым — при том, что показывала почти то же самое.
//
// Прокрутка и отбивки по-прежнему у `PageLayout`; `nested` говорит ему, что смена адреса внутри
// этой рамки — начало новой страницы, а не переход на другую рамку.
import { IconSearch } from '@tabler/icons-vue'

import PageLayout from './PageLayout.vue'
import DetailLayout from './DetailLayout.vue'
import DetailNav from '../components/DetailNav.vue'
import SectionNav from '@/components/SectionNav.vue'
import { detailRail } from '../detailRail'
import { endRouteTransition } from '@/composables/useRouteTransition'

const rail = detailRail()
</script>

<template>
  <PageLayout nested>
    <DetailLayout>
      <template #rail>
        <template v-if="rail">
          <DetailNav :parent="rail.parent" :label="rail.label" :appearance="rail.appearance">
            <template v-if="rail.search">
              <VTextField
                :model-value="rail.search.value"
                :label="rail.search.label"
                :prepend-inner-icon="IconSearch"
                variant="outlined"
                density="comfortable"
                hide-details
                clearable
                @update:model-value="rail.search.update($event ?? '')"
              />
              <p v-if="rail.search.summary" class="rail-search__summary">
                {{ rail.search.summary }}
                <span v-if="rail.search.pending" class="rail-search__pending">
                  <VProgressCircular indeterminate size="11" width="2" />
                  {{ rail.search.pending }}
                </span>
              </p>
            </template>
          </DetailNav>

          <!-- Оглавление есть не у всякой страницы и приезжает вместе с её данными, поэтому
               появляется и уходит оно тоже движением: мигнувшая плашка читалась бы как сбой. -->
          <Transition name="rail-card" mode="out-in">
            <SectionNav v-if="rail.sections?.length" :sections="rail.sections" />
          </Transition>
        </template>
      </template>

      <!-- Тот же переход, что и у смены страницы целиком, но только над содержимым: колонка вне
           его и не мигает. Конец въезда снимается здесь же — переход между вложенными адресами
           верхний `Transition` в `App.vue` не запускает, а тяжёлое содержимое ждёт именно его. -->
      <RouterView v-slot="{ Component }">
        <Transition
          name="page"
          mode="out-in"
          @after-enter="endRouteTransition"
          @enter-cancelled="endRouteTransition"
        >
          <KeepAlive>
            <component :is="Component" />
          </KeepAlive>
        </Transition>
      </RouterView>
    </DetailLayout>
  </PageLayout>
</template>

<style scoped>
.rail-search__summary {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}

/* Плашка оглавления гаснет вместе со схлопыванием: высота едет по `interpolate-size` (auto ↔ 0),
   `min-height: 0` нужен, чтобы элемент колонки-флекса вообще мог сжаться ниже содержимого. */
.rail-card-enter-active,
.rail-card-leave-active {
  overflow: hidden;
  min-height: 0;
  interpolate-size: allow-keywords;
  transition: opacity 0.18s ease, height 0.18s ease;
}

.rail-card-enter-from,
.rail-card-leave-to {
  opacity: 0;
  height: 0;
}

@media (prefers-reduced-motion: reduce) {
  .rail-card-enter-active,
  .rail-card-leave-active {
    transition: none;
  }
}

/* Догоняющая половина поиска: строкой рядом со счётчиком, а не отдельным местом — она уточняет
   именно его число. */
.rail-search__pending {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 6px;
  color: var(--text-faint);
}
</style>
