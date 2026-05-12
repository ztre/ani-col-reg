import { createApp } from 'vue'

import App from './App.vue'
import elementPlusPlugin from './elementPlus'
import router from './router'
import './styles.css'

createApp(App).use(router).use(elementPlusPlugin).mount('#app')
