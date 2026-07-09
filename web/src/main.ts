import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './plugins/i18n'
import vuetify from './plugins/vuetify'
import './styles/main.scss'
import './styles/layout.scss'
import './styles/typography.scss'
import './styles/transitions.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(vuetify)

// Mount only after the initial navigation is fully resolved, so the destination
// route's `meta` (fullscreen/scroll) is already correct at first paint and the app
// chrome never flashes wrong. The static splash in index.html stays up until mount()
// replaces #app.
void router.isReady().then(() => app.mount('#app'))
