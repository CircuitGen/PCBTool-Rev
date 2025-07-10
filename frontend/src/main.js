import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Root from './Root.vue'
import router from './router'

import './assets/main.css'
import './assets/auth.css' // Add a new CSS file for auth forms

const app = createApp(Root)

app.use(createPinia())
app.use(router)

app.mount('#app')
