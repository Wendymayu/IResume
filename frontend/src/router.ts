import { createRouter, createWebHistory } from 'vue-router'
import ProfileView from './views/ProfileView.vue'
import ResumeView from './views/ResumeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/profile' },
    { path: '/profile', component: ProfileView },
    { path: '/resume', component: ResumeView },
  ],
})

export default router
