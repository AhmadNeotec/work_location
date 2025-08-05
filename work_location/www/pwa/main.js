import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { IonicVue } from '@ionic/vue'
import Checkin from './views/checkin.vue'

const routes = [
    { path: '/', component: Home },
  { path: '/checkin', component: Checkin },
  // Add other routes (e.g., home) if needed
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp({})
app.use(IonicVue)
app.use(router)
app.mount('#app')