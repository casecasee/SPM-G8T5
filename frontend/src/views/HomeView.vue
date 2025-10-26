<!-- src/views/HomeView.vue -->
<template>
  <main class="dashboard">
    <!-- Welcome Header -->
    <div class="dashboard-header">
      <div class="welcome-section">
        <h1>Welcome back, {{ getUserName() }}!</h1>
        <p class="welcome-subtitle">{{ getGreeting() }} • {{ getCurrentDate() }}</p>
      </div>
      <div class="quick-actions">
        <RouterLink to="/tasks" class="quick-action-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 11l3 3 8-8" stroke="currentColor" stroke-width="2"/>
            <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="currentColor" stroke-width="2"/>
          </svg>
          My Tasks
        </RouterLink>
        <RouterLink to="/projects" class="quick-action-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2"/>
          </svg>
          Projects
        </RouterLink>
      </div>
    </div>

    <!-- Metrics Cards -->
    <div class="metrics-grid">
      <RouterLink to="/projects" class="metric-card">
      <!-- <div class="metric-card"> -->
        <div class="metric-icon projects">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="metric-content">
          <h3>{{ projectStats.total }}</h3>
          <p>Total Projects</p>
          <!-- <div class="metric-details">
            <span class="active">{{ projectStats.active }} active</span>
            <span class="on-hold">{{ projectStats.onHold }} on hold</span>
          </div> -->
          <!-- <p>Due This Week</p> -->
          <div class="metric-details">
            <span class="urgent" v-if="overdue > 0">{{ overdue }} overdue</span>
          </div>
        </div>
      <!-- </div> -->
      </RouterLink>

      <RouterLink to="/tasks" class="metric-card">
        <div class="metric-icon tasks">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 11l3 3 8-8" stroke="currentColor" stroke-width="2"/>
            <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="metric-content">
          <h3>{{ taskStats.total }}</h3>
          <p>My Tasks</p>
          <div class="metric-details">
            <span class="completed">{{ taskStats.completed }} done</span>
            <span class="ongoing">{{ taskStats.ongoing }} ongoing</span>
          </div>
        </div>
      </RouterLink>

      <div class="metric-card">
        <div class="metric-icon progress">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="metric-content">
          <h3>{{ overallProgress }}%</h3>
          <p>Overall Progress</p>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: overallProgress + '%' }"></div>
          </div>
        </div>
      </div>

      <RouterLink to="/tasks" class="metric-card">
        <div class="metric-icon deadline">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="metric-content">
          <h3>{{ upcomingDeadlines }}</h3>
          <p>Due This Week</p>
          <div class="metric-details">
            <span class="urgent" v-if="overdueTasks > 0">{{ overdueTasks }} overdue</span>
          </div>
        </div>
      </RouterLink>
    </div>

    <!-- Main Content Grid -->
    <div class="dashboard-grid">
      <!-- My Recent Tasks -->
      <div class="dashboard-section">
        <div class="section-header">
          <h2>My Recent Tasks</h2>
          <RouterLink to="/tasks" class="view-all-link">View All</RouterLink>
        </div>
        <div class="tasks-list">
          <div v-if="loading" class="loading">Loading tasks...</div>
          <div v-else-if="myRecentTasks.length === 0" class="empty-state">
            <p>No tasks assigned to you yet.</p>
            <RouterLink to="/tasks" class="btn-primary">Create Task</RouterLink>
          </div>
          <div v-else>
            <div v-for="task in myRecentTasks" :key="task.id" class="task-item" @click="openTaskDetails(task)">
              <div class="task-info">
                <h4>{{ task.name }}</h4>
                <p class="task-description">{{ task.description }}</p>
                <div class="task-meta">
                  <span class="task-status" :class="getStatusClass(task.status)">{{ task.status }}</span>
                  <span class="task-deadline">Due: {{ formatDate(task.due_date) }}</span>
                </div>
              </div>
              <div class="task-actions">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="9,18 15,12 9,6" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Projects -->
      <div class="dashboard-section">
        <div class="section-header">
          <h2>Projects</h2>
          <RouterLink to="/projects" class="view-all-link">View All</RouterLink>
        </div>
        <div class="projects-list">
          <div v-if="loading" class="loading">Loading projects...</div>
          <div v-else-if="recentProjects.length === 0" class="empty-state">
            <p>No active projects found.</p>
            <RouterLink to="/projects" class="btn-primary">Create Project</RouterLink>
          </div>
          <div v-else>
            <div v-for="project in recentProjects" :key="project.id" class="project-item" @click="openProjectDetails(project)">
              <div class="project-info">
                <h4>{{ project.name }}</h4>
                <p class="project-owner">Owner: {{ project.owner }}</p>
                <div class="project-progress">
                  <div class="progress-info">
                    <span>{{ project.tasksDone }} / {{ project.tasksTotal }} tasks</span>
                    <span>{{ getProjectProgress(project) }}%</span>
                  </div>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: getProjectProgress(project) + '%' }"></div>
                  </div>
                </div>
              </div>
              
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="dashboard-section full-width">
      <div class="section-header">
        <h2>Recent Activity</h2>
      </div>
      <div class="activity-feed">
        <div v-if="loading" class="loading">Loading activity...</div>
        <div v-else-if="recentActivity.length === 0" class="empty-state">
          <p>No recent activity to show.</p>
        </div>
        <div v-else>
          <div v-for="activity in recentActivity" :key="activity.id" class="activity-item">
            <div class="activity-icon" :class="activity.type">
              <svg v-if="activity.type === 'task'" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 11l3 3 8-8" stroke="currentColor" stroke-width="2"/>
              </svg>
              <svg v-else-if="activity.type === 'project'" width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="activity-content">
              <p>{{ activity.message }}</p>
              <span class="activity-time">{{ formatTimeAgo(activity.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// State
const loading = ref(true)
const tasks = ref([])
const projects = ref([])

// Computed properties
const currentEmployeeId = computed(() => Number(sessionStorage.getItem("employee_id")))
const currentEmployeeName = computed(() => sessionStorage.getItem("employee_name") || "User")

const projectStats = computed(() => {
  const total = projects.value.length
  const overdue = tasks.value.filter(t => {
    if (!t.due_date || t.status === 'done') return false
    return new Date(t.due_date) < new Date()
  }).length
  const active = projects.value.filter(p => p.status === 'Active').length
  const onHold = projects.value.filter(p => p.status === 'On hold').length
  return { total, active, onHold }
})

const taskStats = computed(() => {
  const myTasks = tasks.value
  console.log('My Tasks:', myTasks)
  const total = myTasks.length
  const completed = myTasks.filter(t => t.status === 'done').length
  const ongoing = myTasks.filter(t => t.status === 'ongoing').length
  return { total, completed, ongoing }
})

const overallProgress = computed(() => {
  if (projects.value.length === 0) return 0
  const totalTasks = projects.value.reduce((sum, p) => sum + p.tasksTotal, 0)
  const completedTasks = projects.value.reduce((sum, p) => sum + p.tasksDone, 0)
  return totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
})

const upcomingDeadlines = computed(() => {
  const nextWeek = new Date()
  nextWeek.setDate(nextWeek.getDate() + 7)
  return tasks.value.filter(t => {
    if (!t.due_date) return false
    const dueDate = new Date(t.due_date)
    return dueDate <= nextWeek && dueDate >= new Date()
  }).length
})

const overdueTasks = computed(() => {
  const now = new Date()
  return tasks.value.filter(t => {
    if (!t.due_date || t.status === 'done') return false
    return new Date(t.due_date) < now
  }).length
})

const myRecentTasks = computed(() => {
  return tasks.value
    .filter(t => t.owner === currentEmployeeId.value)
    .sort((a, b) => new Date(b.due_date || 0) - new Date(a.due_date || 0))
    .slice(0, 5)
})

const recentProjects = computed(() => {
  return (projects.value || [])
    .slice()
    .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    .slice(0, 3)
})

const recentActivity = computed(() => {
  const activities = []
  
  // Add recent tasks
  tasks.value.slice(0, 3).forEach(task => {
    activities.push({
      id: `task-${task.id}`,
      type: 'task',
      message: `Task "${task.name}" was created`,
      timestamp: task.due_date
    })
  })
  
  // Add recent projects
  projects.value.slice(0, 2).forEach(project => {
    activities.push({
      id: `project-${project.id}`,
      type: 'project',
      message: `Project "${project.name}" was updated`,
      timestamp: project.updatedAt
    })
  })
  
  return activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 5)
})

// Methods
const getUserName = () => currentEmployeeName.value
const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}
const getCurrentDate = () => {
  return new Date().toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}

const fetchData = async () => {
  loading.value = true

  const [tasksRes, projectsRes] = await Promise.allSettled([
    axios.get("http://localhost:5002/tasks", { withCredentials: true }),
    axios.get("http://localhost:8001/projects", { withCredentials: true })
  ])

  if (tasksRes.status === 'fulfilled') {
    const data = tasksRes.value.data
    tasks.value = (data.my_tasks || []).map(t => ({
      id: t.task_id,
      name: t.title,
      description: t.description,
      due_date: t.deadline,
      status: t.status,
      owner: Number(t.owner),
      project_id: t.project_id
    }))
  } else {
    console.error('Tasks load failed:', tasksRes.reason)
    tasks.value = []
  }

  if (projectsRes.status === 'fulfilled') {
    projects.value = projectsRes.value.data || []
  } else {
    console.error('Projects load failed:', projectsRes.reason)
    projects.value = []
  }

  loading.value = false
}

const formatDate = (date) => {
  if (!date) return 'No date'
  return new Date(date).toLocaleDateString()
}

const formatTimeAgo = (timestamp) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffInHours = Math.floor((now - time) / (1000 * 60 * 60))
  
  if (diffInHours < 1) return 'Just now'
  if (diffInHours < 24) return `${diffInHours}h ago`
  const diffInDays = Math.floor(diffInHours / 24)
  return `${diffInDays}d ago`
}

const getStatusClass = (status) => {
  const statusMap = {
    'ongoing': 'status-ongoing',
    'under review': 'status-review',
    'done': 'status-completed',
    'unassigned': 'status-unassigned'
  }
  return statusMap[status] || 'status-default'
}

// project status styling removed

const getProjectProgress = (project) => {
  if (project.tasksTotal === 0) return 0
  return Math.round((project.tasksDone / project.tasksTotal) * 100)
}

const openTaskDetails = (task) => {
  router.push('/tasks')
}

const openProjectDetails = (project) => {
  router.push('/projects')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* Dashboard Layout */
.dashboard {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.welcome-section h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: var(--color-ink);
}

.welcome-subtitle {
  color: var(--color-ink-secondary);
  font-size: 1.1rem;
  margin: 0;
}

.quick-actions {
  display: flex;
  gap: 1rem;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--color-mint);
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.quick-action-btn:hover {
  background: var(--color-mint-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  /* When this card is rendered as a RouterLink (<a>), prevent default underline */
  text-decoration: none;
  color: inherit;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.metric-icon.projects { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.metric-icon.tasks { background: linear-gradient(135deg, #10b981, #059669); }
.metric-icon.progress { background: linear-gradient(135deg, #f59e0b, #d97706); }
.metric-icon.deadline { background: linear-gradient(135deg, #ef4444, #dc2626); }

.metric-content h3 {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
  color: var(--color-ink);
}

.metric-content p {
  font-size: 0.9rem;
  color: var(--color-ink-secondary);
  margin: 0 0 0.5rem 0;
}

.metric-details {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
}

.metric-details span {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-weight: 500;
}

.metric-details .active { background: #d1fae5; color: #065f46; }
.metric-details .on-hold { background: #fef3c7; color: #92400e; }
.metric-details .completed { background: #d1fae5; color: #065f46; }
.metric-details .ongoing { background: #dbeafe; color: #1e40af; }
.metric-details .urgent { background: #fee2e2; color: #dc2626; }

.progress-bar {
  width: 100%;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.dashboard-section {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.dashboard-section.full-width {
  grid-column: 1 / -1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-ink);
}

.view-all-link {
  color: var(--color-mint);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
  transition: color var(--transition-fast);
}

.view-all-link:hover {
  color: var(--color-mint-dark);
}

/* Task Items */
.tasks-list, .projects-list, .activity-feed {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item, .project-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.task-item:hover, .project-item:hover {
  background: var(--color-background);
  border-color: var(--color-mint);
  transform: translateY(-1px);
}

.task-info h4, .project-info h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  color: var(--color-ink);
}

.task-description, .project-owner {
  font-size: 0.9rem;
  color: var(--color-ink-secondary);
  margin: 0 0 0.5rem 0;
  line-height: 1.4;
}

.task-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
}

.task-status {
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
  font-weight: 500;
}

.status-ongoing { background: #dbeafe; color: #1e40af; }
.status-review { background: #fef3c7; color: #92400e; }
.status-completed { background: #d1fae5; color: #065f46; }
.status-unassigned { background: #f3f4f6; color: #374151; }

.task-deadline {
  color: var(--color-ink-muted);
}

.task-actions {
  color: var(--color-ink-muted);
  transition: color var(--transition-fast);
}

.task-item:hover .task-actions {
  color: var(--color-mint);
}

/* Project Items */
.project-progress {
  margin-top: 0.5rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--color-ink-secondary);
  margin-bottom: 0.25rem;
}

.project-status {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-active { background: #d1fae5; color: #065f46; }
.status-on-hold { background: #fef3c7; color: #92400e; }
.status-archived { background: #f3f4f6; color: #374151; }

/* Activity Feed */
.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  transition: all var(--transition-fast);
}

.activity-item:hover {
  background: var(--color-background);
  border-color: var(--color-mint);
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.activity-icon.task { background: #10b981; }
.activity-icon.project { background: #3b82f6; }

.activity-content p {
  margin: 0 0 0.25rem 0;
  color: var(--color-ink);
  font-size: 0.9rem;
}

.activity-time {
  font-size: 0.8rem;
  color: var(--color-ink-muted);
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--color-ink-secondary);
}

.empty-state p {
  margin: 0 0 1rem 0;
}

.btn-primary {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: var(--color-mint);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.btn-primary:hover {
  background: var(--color-mint-dark);
  transform: translateY(-1px);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--color-ink-secondary);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 1rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-section h1 {
    font-size: 2rem;
  }
}
</style>
