import { createRouter, createWebHistory } from 'vue-router'
import TasksView from '../views/TasksView/TasksView.vue'
import TasksTimelineView from '../views/TasksTimelineView.vue'
import ReportsView from '../views/ReportsView.vue'
import LoginPage from '../views/LoginPage.vue'
import HomeView from '../views/HomeView.vue' 
import ProjectsView from '../views/ProjectsView.vue' 
import ProjectDetailView from '../views/ProjectDetailView.vue'
import ProjectTimelineView from '../views/ProjectTimelineView.vue'
import NotificationSettings from '../components/NotificationSettings.vue'


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
    path: '/tasks-timeline',
    name: 'tasks-timeline',
    component: TasksTimelineView,
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
  {
    path: '/projects/:id/timeline',
    name: 'project-timeline',
    component: ProjectTimelineView,
  },
  {
    path: '/timeline',
    name: 'timeline',
    component: ProjectTimelineView,
  },
  {
    path: '/settings/notifications',
    name: 'notification-settings',
    component: NotificationSettings,
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
