import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './plugins/i18n'
import vuetify from './plugins/vuetify'
import { useSettingsStore } from './stores/settings'
import { setShellError } from './composables/useShellError'
import './styles/fonts.scss'
import './styles/main.scss'
import './styles/layout.scss'
import './styles/typography.scss'
import './styles/transitions.scss'

const app = createApp(App)

// Последняя преграда перед белым экраном: необработанное исключение внутри вьюхи превращается
// в экран «что-то сломалось» с кнопкой повтора, а не в пустой #app. Ошибку всё равно печатаем —
// экран сообщает человеку, консоль сообщает разработчику.
app.config.errorHandler = (err) => {
  console.error(err)
  setShellError('failure')
}

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(vuetify)

// Instantiating the settings store paints the chosen font families onto <html> before
// the first frame — leaving it to the first component that happens to use the store
// would swap the typeface after mount, in full view.
useSettingsStore()

// Mount only after the initial navigation is fully resolved, so the destination
// route's `meta` (fullscreen/scroll) is already correct at first paint and the app
// chrome never flashes wrong. The static splash in index.html stays up until mount()
// replaces #app.
void router.isReady().then(() => app.mount('#app'))
