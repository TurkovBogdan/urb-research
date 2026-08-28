<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import VSelectSearch from '@/components/VSelectSearch.vue'
import {
  IconSearch,
  IconMapPin,
  IconUser,
  IconSortAscending,
  IconSortDescending,
  IconTable,
  IconLayoutGrid,
  IconFolders,
  IconServer,
  IconCoin,
  IconMessage,
} from '@tabler/icons-vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const items   = ['Moscow', 'Saint Petersburg', 'Kazan', 'Novosibirsk', 'Yekaterinburg']
const objects = [
  { title: 'Manager', value: 'manager' },
  { title: 'Developer', value: 'developer' },
  { title: 'Designer', value: 'designer' },
  { title: 'Analyst', value: 'analyst' },
]

const v1 = ref<string | null>(null)
const v2 = ref<string | null>(null)
const v3 = ref<string | null>(null)
const v4 = ref<string | null>(null)
const v5 = ref<string | null>(null)
const v6 = ref<string | null>(null)
const v7 = ref<string | null>(null)
const v8 = ref<string | null>(null)
const v9 = ref<string[]>([])
const v10 = ref<string | null>(null)

// Search-inside-dropdown demo. The pattern lives in the reusable VSelectSearch
// component (drop-in for VSelect); the page only wires items + v-model.
const cities = [
  'Moscow', 'Saint Petersburg', 'Novosibirsk', 'Yekaterinburg', 'Kazan',
  'Nizhny Novgorod', 'Chelyabinsk', 'Samara', 'Omsk', 'Rostov-on-Don',
  'Ufa', 'Krasnoyarsk', 'Voronezh', 'Perm', 'Volgograd',
]
const v11 = ref<string | null>(null)

const searchSnippet = `<script setup lang="ts">
import VSelectSearch from '@/components/VSelectSearch.vue'
import { ref } from 'vue'

const cities = ['Moscow', 'Saint Petersburg', 'Novosibirsk', /* … */]
const value = ref<string | null>(null)
<\/script>

<template>
  <VSelectSearch
    v-model="value"
    :items="cities"
    label="City"
    variant="outlined"
  />
</template>`

// Иконки в пунктах. Штатный путь — `props.prependIcon` у самого пункта; своя разметка (плашка
// в цвете, две строки, счётчик) — слоты `#item` / `#selection`.
const viewOptions = [
  { title: 'Таблица', value: 'table', props: { prependIcon: IconTable } },
  { title: 'Плитки', value: 'cards', props: { prependIcon: IconLayoutGrid } },
  { title: 'Плитки по группам', value: 'grouped', props: { prependIcon: IconFolders } },
]
const viewValue = ref('table')

const shelfOptions = [
  { title: 'DevOps: настройка сервера', value: 'devops', icon: IconServer, tone: '#0994BA' },
  { title: 'Финансы, налоги и право', value: 'finance', icon: IconCoin, tone: '#928A07' },
  { title: 'Командные коммуникации', value: 'chat', icon: IconMessage, tone: '#A35DE4' },
]
const shelfValue = ref('devops')

const iconsSnippet = `<template>
  <!-- Штатный путь: иконка задаётся самим пунктом -->
  <VSelect :items="[{ title: 'Таблица', value: 'table', props: { prependIcon: IconTable } }]" />

  <!-- Своя разметка пункта и выбранного значения.
       :chips="false" обязателен: с чипами (глобальный дефолт) Vuetify рисует #chip,
       а #selection молча игнорирует. В слот приезжает ИСХОДНЫЙ объект пункта — не item.raw. -->
  <VSelect :items="shelves" :chips="false">
    <template #item="{ props: itemProps, item }">
      <VListItem v-bind="itemProps">
        <template #prepend><ShelfSwatch :icon="item.icon" :tone="item.tone" /></template>
      </VListItem>
    </template>
    <template #selection="{ item }">
      <ShelfSwatch :icon="item.icon" :tone="item.tone" /> {{ item.title }}
    </template>
  </VSelect>
</template>`

// Селект с приросшей кнопкой — на примере сортировки: поле выбирает, по чему сортировать,
// кнопка переключает направление, и порознь они не читаются.
const sortFields = ['Дата создания', 'Дата обновления', 'Название']
const sortBy = ref(sortFields[0])
const sortDir = ref<'asc' | 'desc'>('desc')
const sortBy2 = ref(sortFields[0])
const sortDir2 = ref<'asc' | 'desc'>('desc')

// Классы глобальные (main.scss) — своего CSS месту применения не нужно.
const groupSnippet = `<template>
  <div class="field-group">
    <VSelect v-model="sortBy" :items="fields" label="Сортировка"
      variant="outlined" density="comfortable" hide-details />
    <VBtn variant="outlined" density="comfortable" icon class="field-group__btn"
      :aria-label="label" @click="toggleDir">
      <IconSortAscending v-if="dir === 'asc'" :size="16" />
      <IconSortDescending v-else :size="16" />
    </VBtn>
  </div>
</template>`

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.selects.title')" :description="t('design-system.page.selects.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VSelect v-model="v1" :items="items" label="City" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">primary</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">filled</span>
          <div class="ds-controls">
            <VSelect v-model="v2" :items="items" label="City" variant="filled" hide-details />
          </div>
          <span class="ds-spec">with background</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">plain</span>
          <div class="ds-controls">
            <VSelect v-model="v3" :items="items" placeholder="City" variant="plain" hide-details />
          </div>
          <span class="ds-spec">no border · label not used</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">clearable</span>
          <div class="ds-controls">
            <VSelect v-model="v4" :items="items" label="City" variant="outlined" clearable hide-details />
          </div>
          <span class="ds-spec">clearable</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">loading</span>
          <div class="ds-controls">
            <VSelect v-model="v5" :items="items" label="City" variant="outlined" loading hide-details />
          </div>
          <span class="ds-spec">loading</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VSelect :items="items" label="City" variant="outlined" model-value="Moscow" disabled hide-details />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <VSelect :items="items" label="City" variant="outlined" :error-messages="['This field is required']" />
          </div>
          <span class="ds-spec">:error-messages</span>
        </div>

      </div>
    </section>

    <!-- With icons -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.withIcons') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">prepend-inner</span>
          <div class="ds-controls">
            <VSelect v-model="v6" :items="items" label="City" variant="outlined"
              :prepend-inner-icon="IconMapPin" hide-details />
          </div>
          <span class="ds-spec">:prepend-inner-icon</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">prepend</span>
          <div class="ds-controls">
            <VSelect v-model="v7" :items="items" label="City" variant="outlined"
              :prepend-icon="IconUser" hide-details />
          </div>
          <span class="ds-spec">:prepend-icon</span>
        </div>

      </div>
    </section>

    <!-- Objects -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.objects') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">items objects</span>
          <div class="ds-controls">
            <VSelect v-model="v8" :items="objects" item-title="title" item-value="value"
              label="Position" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">item-title / item-value</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">multiple</span>
          <div class="ds-controls">
            <VSelect v-model="v9" :items="items" label="Cities" variant="outlined" multiple hide-details />
          </div>
          <span class="ds-spec">chips by default</span>
        </div>

      </div>

      <p class="ds-note">
        Чипы для мультиселектов включены глобально (chips / closable-chips в defaults
        Vuetify) — отдельный <code>multiple</code> уже рендерит выбранное чипами в стиле
        дизайн-системы. Одиночный выбор остаётся простым текстом. Нужен компактный
        вид (счётчик «+N» через слот <code>#selection</code>) — отключите чипы
        пропом <code>:chips="false"</code>.
      </p>
    </section>

    <!-- VAutocomplete -->
    <section class="ds-section">
      <h6 class="mb-3">Autocomplete</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">autocomplete</span>
          <div class="ds-controls">
            <VAutocomplete v-model="v10" :items="items" label="Search city" variant="outlined"
              :prepend-inner-icon="IconSearch" clearable hide-details />
          </div>
          <span class="ds-spec">VAutocomplete</span>
        </div>

      </div>
    </section>

    <!-- Search inside dropdown -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.searchInDropdown') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">VSelectSearch</span>
          <div class="ds-controls">
            <VSelectSearch v-model="v11" :items="cities" label="City" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">drop-in for VSelect</span>
        </div>

      </div>

      <p class="ds-note">
        VSelectSearch — a drop-in wrapper over VSelect that pins a search row atop the open
        menu (#prepend-item) and filters items in place. VAutocomplete merges the query into
        the field; this keeps the field display intact. Props/slots pass through to VSelect.
      </p>

      <CodeBlock :code="searchSnippet" lang="vue" variant="icon" class="mt-3" />
    </section>

    <!-- Icons inside items -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.itemIcons') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">prependIcon</span>
          <div class="ds-controls">
            <VSelect
              v-model="viewValue"
              :items="viewOptions"
              label="Список исследований"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </div>
          <span class="ds-spec">props.prependIcon у пункта</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">#item · #selection</span>
          <div class="ds-controls">
            <VSelect
              v-model="shelfValue"
              :items="shelfOptions"
              :chips="false"
              label="Полка"
              variant="outlined"
              density="comfortable"
              hide-details
            >
              <template #item="{ props: itemProps, item }">
                <VListItem v-bind="itemProps">
                  <template #prepend>
                    <span class="swatch" :style="{ '--tone': item.tone }">
                      <component :is="item.icon" :size="14" :stroke-width="1.7" />
                    </span>
                  </template>
                </VListItem>
              </template>

              <template #selection="{ item }">
                <span class="swatch-line">
                  <span class="swatch" :style="{ '--tone': item.tone }">
                    <component :is="item.icon" :size="14" :stroke-width="1.7" />
                  </span>
                  {{ item.title }}
                </span>
              </template>
            </VSelect>
          </div>
          <span class="ds-spec">своя плашка · :chips="false"</span>
        </div>

      </div>

      <p class="ds-note">
        Отбивка иконки от подписи нормализована глобально: Vuetify держит
        <code>--v-list-prepend-gap</code> в 32px — место под аватарку, которой в выпадающих
        списках не бывает, — и на этой ширине иконки с подписями читаются как два несвязанных
        столбца. В <code>main.scss</code> для списков внутри меню и селектов зазор задан в 10px,
        поэтому месту применения ничего править не нужно.
      </p>

      <p class="ds-note">
        Своя разметка пункта — слот <code>#item</code>, своя разметка выбранного значения —
        <code>#selection</code>. Две ловушки: в слот приезжает <strong>исходный</strong> объект
        пункта (<code>item.tone</code>, а не <code>item.raw.tone</code>), а
        <code>#selection</code> работает только при <code>:chips="false"</code> — с чипами
        (глобальный дефолт) Vuetify рисует <code>#chip</code> и молча игнорирует его.
      </p>

      <CodeBlock :code="iconsSnippet" lang="vue" variant="icon" class="mt-3" />
    </section>

    <!-- Select + attached button -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.withButton') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">comfortable</span>
          <div class="ds-controls">
            <div class="field-group">
              <VSelect
                v-model="sortBy"
                :items="sortFields"
                label="Сортировка"
                variant="outlined"
                density="comfortable"
                hide-details
              />
              <VBtn
                variant="outlined"
                density="comfortable"
                icon
                class="field-group__btn"
                :aria-label="sortDir === 'asc' ? 'По возрастанию' : 'По убыванию'"
                @click="sortDir = sortDir === 'asc' ? 'desc' : 'asc'"
              >
                <IconSortAscending v-if="sortDir === 'asc'" :size="16" />
                <IconSortDescending v-else :size="16" />
              </VBtn>
            </div>
          </div>
          <span class="ds-spec">32px · фильтры страниц</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <div class="field-group">
              <VSelect
                v-model="sortBy2"
                :items="sortFields"
                label="Сортировка"
                variant="outlined"
                hide-details
              />
              <VBtn
                variant="outlined"
                icon
                class="field-group__btn"
                :aria-label="sortDir2 === 'asc' ? 'По возрастанию' : 'По убыванию'"
                @click="sortDir2 = sortDir2 === 'asc' ? 'desc' : 'asc'"
              >
                <IconSortAscending v-if="sortDir2 === 'asc'" :size="18" />
                <IconSortDescending v-else :size="18" />
              </VBtn>
            </div>
          </div>
          <span class="ds-spec">36px · формы</span>
        </div>

      </div>

      <p class="ds-note">
        Поле и кнопка, которые читаются как одна ручка: направление сортировки бессмысленно
        без поля, по которому сортируют, а отдельная кнопка рядом выглядит как самостоятельное
        действие. Срастание делает вёрстка, а не компонент: пара классов
        <code>.field-group</code> / <code>.field-group__btn</code> лежит глобально в
        <code>main.scss</code> — у поля срезано правое скругление, у кнопки левое, и кнопка
        сдвинута на пиксель, чтобы граница на стыке не удвоилась. Коробка кнопки следует за её
        <code>density</code>: та правит только высоту, а сторону иконочной кнопки Vuetify
        считает от неё же и без ширины даёт прямоугольник. Так собраны фильтры сортировки в
        реестре исследований и в списке групп.
      </p>

      <CodeBlock :code="groupSnippet" lang="vue" variant="icon" class="mt-3" />
    </section>

    <!-- Sizes (density axis) -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.selects.sizes') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VSelect :items="items" label="City" variant="outlined" hide-details />
          </div>
          <span class="ds-spec">density="default" · 36px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">comfortable</span>
          <div class="ds-controls">
            <VSelect :items="items" label="City" variant="outlined" density="comfortable" hide-details />
          </div>
          <span class="ds-spec">density="comfortable" · 32px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact</span>
          <div class="ds-controls">
            <VSelect :items="items" label="City" variant="outlined" density="compact" hide-details />
          </div>
          <span class="ds-spec">density="compact" · 28px</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact plain</span>
          <div class="ds-controls">
            <VSelect :items="items" placeholder="City" variant="plain" density="compact" hide-details />
          </div>
          <span class="ds-spec">inline / filters · 28px</span>
        </div>

      </div>

      <p class="ds-note">
        Размер поля задаётся осью <code>density</code> — это единственный нативный
        механизм высоты у Vuetify-полей (проп <code>size</code>, как у кнопок, тут
        отсутствует). Высоты заданы глобально в <code>main.scss</code> и едины для всех
        полей (селекты, ввод, числа, дата): <code>default</code> 36px ·
        <code>comfortable</code> 32px · <code>compact</code> 28px. По семантике Vuetify
        <code>default</code> — самый высокий, ступени уменьшают высоту и вертикальные
        отступы синхронно.
      </p>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }

.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
}

.ds-controls {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.v-select, .v-autocomplete {
  min-width: 220px;
  max-width: 280px;
}

/* Плашка пункта: иконка в цвете сущности — так полка узнаётся в реестре исследований. */
.swatch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  flex: none;
  color: var(--tone);
  background: color-mix(in srgb, var(--tone) 14%, transparent);
}

.swatch-line {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ds-note {
  margin-top: 14px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-muted);
}
</style>
