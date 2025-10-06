import { createRouter, createWebHistory } from 'vue-router'
import TasksView from '../views/TasksView.vue'
import ReportsView from '../views/ReportsView.vue'
import LoginPage from '../views/LoginPage.vue'
import HomeView from '../views/HomeView.vue' 
import ProjectsView from '../views/ProjectsView.vue' 
import ProjectDetailView from '../views/ProjectDetailView.vue'


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
  {
    path: '/projects',
    name: 'projects',
    component: ProjectsView,
  },
  {
    path: '/projects/:id',
    name: 'project-detail',
    component: ProjectDetailView,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  // Check if the user is logged in by verifying the presence of employee_id in sessionStorage
  const isLoggedIn = sessionStorage.getItem("employee_id") !== null
  
  // Allow the login page to be accessed without coming from another route
  if (to.name !== 'login' && !isLoggedIn) {
    next({ name: 'login' })
  } else {
    next()
  }
})


export default router
