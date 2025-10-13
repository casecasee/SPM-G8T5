// import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import 'primeicons/primeicons.css'
import 'primevue/resources/themes/nova/theme.css' // or any other theme 
import 'primevue/resources/primevue.css'
import './assets/global.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// const downloadBtn = document.querySelector(".download-btn");



  

app.use(createPinia())
app.use(PrimeVue)
app.use(router)

app.mount('#app')
