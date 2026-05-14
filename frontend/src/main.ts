import { createApp } from 'vue'

import App from './App.vue'
import elementPlusPlugin from './elementPlus'
import router from './router'
import { initializeThemeMode } from './theme'
import './styles.css'

initializeThemeMode()

createApp(App).use(router).use(elementPlusPlugin).mount('#app')
