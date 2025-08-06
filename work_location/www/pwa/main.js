import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { IonicVue } from '@ionic/vue'

// Import your views
// import Home from './views/Home.vue' 
import Checkin from './views/checkin.vue'

const routes = [
  // { path: '/', component: Home },
  { path: '/checkin', component: Checkin }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp({})
app.use(IonicVue)
app.use(router)
app.mount('#app')
