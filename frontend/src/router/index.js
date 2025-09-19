import { createRouter, createWebHistory } from 'vue-router'
import TasksView from '../views/TasksView.vue'
import ReportsView from '../views/ReportsView.vue'
import LoginPage from '../views/LoginPage.vue'
import HomeView from '../views/HomeView.vue' 

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: TasksView,
  },
  {
    path: '/reports',
    name: 'reports',
    component: ReportsView,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
