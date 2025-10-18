<template>
  <div class="timeline-page">
    <div class="timeline-header">
      <div class="header-left">
        <h2>Project Timeline</h2>
        <p class="breadcrumb">
          <a href="#" @click.prevent="() => router.push({ name: 'projects' })">Projects</a> / 
          <span v-if="selectedProject">{{ selectedProject.name }} / </span>
          <span>Timeline</span>
        </p>
      </div>
      <div class="header-right">
        <Button :label="selectedProject ? 'Back to Project' : 'Back to Projects'" class="btn" @click="goBack" />
      </div>
    </div>

    <!-- Project Selector (for multi-project users) -->
    <div v-if="availableProjects.length > 1" class="project-selector">
      <label>Project:</label>
      <Dropdown 
        v-model="selectedProjectId" 
        :options="projectOptions" 
        optionLabel="label" 
        optionValue="value" 
        class="project-dropdown"
        @change="onProjectChange"
      />
    </div>

    <!-- Timeline Controls -->
    <div class="timeline-controls">
      <div class="date-range-controls">
        <label>Date Range:</label>
        <Dropdown 
          v-model="dateRange" 
          :options="dateRangeOptions" 
          optionLabel="label" 
          optionValue="value" 
          class="date-range-dropdown"
          @change="onDateRangeChange"
        />
      </div>
      <div class="view-controls">
        <Button 
          :label="isCompactView ? 'Expand View' : 'Compact View'" 
          class="view-toggle-btn" 
          @click="toggleView"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading timeline data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <Button label="Retry" @click="loadTimelineData" />
    </div>

    <!-- No Data State -->
    <div v-else-if="timelineTasks.length === 0" class="no-data-state">
      <div class="no-data-content">
        <div class="no-data-icon">📅</div>
        <h3>No Tasks Found</h3>
        <p>There are no tasks in this project for the selected date range.</p>
        <Button label="Back to Project" @click="goBack" />
      </div>
    </div>

    <!-- Timeline Content -->
    <div v-else class="timeline-container" :class="{ 'compact-view': isCompactView }">
      <div class="timeline-canvas" ref="timelineCanvas">
        <!-- Timeline Header with Dates -->
        <div class="timeline-header-row">
          <div class="team-members-column">
            <h3>Team Members</h3>
          </div>
          <div class="dates-row">
            <div 
              v-for="date in timelineDates" 
              :key="date" 
              class="date-column"
              :class="{ 'is-weekend': isWeekend(date), 'compact': isCompactView }"
            >
              <div class="date-label" :class="{ 'compact': isCompactView }">{{ formatDateHeader(date) }}</div>
            </div>
          </div>
        </div>

        <!-- Timeline Rows for Each Team Member -->
        <div class="timeline-rows">
          <div 
            v-for="member in teamMembers" 
            :key="member.employee_id" 
            class="timeline-row"
          >
            <!-- Member Info Column -->
            <div class="member-info" :class="{ 'compact': isCompactView }">
              <div class="member-avatar" :class="{ 'compact': isCompactView }">
                <i class="pi pi-user"></i>
              </div>
              <div class="member-details" v-if="!isCompactView">
                <div class="member-name">{{ member.employee_name }}</div>
                <div class="member-role">{{ member.role }}</div>
              </div>
              <div class="member-name-compact" v-if="isCompactView">{{ member.employee_name }}</div>
            </div>

            <!-- Tasks Row -->
            <div class="tasks-row">
              <div 
                v-for="date in timelineDates" 
                :key="`${member.employee_id}-${date}`" 
                class="date-cell"
                :class="{ 'is-weekend': isWeekend(date), 'compact': isCompactView }"
              >
                <!-- Tasks for this member on this date -->
                <div 
                  v-for="task in getTasksForMemberAndDate(member.employee_id, date)" 
                  :key="task.id"
                  class="task-card"
                  :class="[getTaskCardClass(task), { 'compact': isCompactView }]"
                  @click="openTaskDetails(task)"
                >
                  <div class="task-title">{{ task.title }}</div>
                  <div class="task-meta" v-if="!isCompactView">
                    <span class="task-status">{{ task.status }}</span>
                    <span class="task-priority">P{{ task.priority }}</span>
                  </div>
                  <div class="task-priority-compact" v-if="isCompactView">P{{ task.priority }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Task Detail Modal -->
    <Dialog 
      v-model:visible="showTaskModal" 
      modal 
      :header="selectedTask ? `Task: ${selectedTask.title}` : 'Task Details'"
      class="task-detail-modal"
      :style="{ width: '600px', minWidth: '600px' }"
      :breakpoints="{ '960px': '95vw', '640px': '100vw' }"
    >
      <div v-if="selectedTask" class="task-details">
        <div class="detail-row">
          <label>Description:</label>
          <p>{{ selectedTask.description || 'No description' }}</p>
        </div>
        <div class="detail-row">
          <label>Status:</label>
          <span class="status-badge" :class="getStatusClass(selectedTask.status)">
            {{ selectedTask.status }}
          </span>
        </div>
        <div class="detail-row">
          <label>Priority:</label>
          <span class="priority-badge" :class="getPriorityClass(selectedTask.priority)">
            P{{ selectedTask.priority }}
          </span>
        </div>
        <div class="detail-row">
          <label>Due Date:</label>
          <span>{{ formatDate(selectedTask.due_date) }}</span>
        </div>
        <div class="detail-row">
          <label>Owner:</label>
          <span>{{ getMemberName(selectedTask.owner) }}</span>
        </div>
        <div class="detail-row" v-if="selectedTask.collaborators?.length">
          <label>Collaborators:</label>
          <span>{{ getCollaboratorNames(selectedTask.collaborators) }}</span>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProjects } from '../api/projects'
import { listTasks } from '../api/tasks'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// State
const loading = ref(false)
const error = ref('')
const selectedProjectId = ref(null)
const selectedProject = ref(null)
const availableProjects = ref([])
const teamMembers = ref([])
const timelineTasks = ref([])
const showTaskModal = ref(false)
const selectedTask = ref(null)
const dateRange = ref('month')
const isCompactView = ref(false)
const projectDateRange = ref(null)

// Current user info
const currentEmployeeId = Number(sessionStorage.getItem('employee_id')) || null
const currentRole = sessionStorage.getItem('role') || ''
const currentDepartment = sessionStorage.getItem('department') || ''

// Computed properties
const projectOptions = computed(() => {
  return availableProjects.value.map(project => ({
    label: `${project.name} (#${project.id})`,
    value: project.id
  }))
})

const dateRangeOptions = computed(() => {
  const options = [
    { label: 'This Week', value: 'week' },
    { label: 'This Month', value: 'month' },
    { label: 'Next 3 Months', value: 'quarter' }
  ]
  
  // Add project duration option if we have project date range
  if (projectDateRange.value) {
    const startDate = new Date(projectDateRange.value.start_date)
    const endDate = new Date(projectDateRange.value.end_date)
    const startStr = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    const endStr = endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    
    options.push({
      label: `Project Duration (${startStr} - ${endStr})`,
      value: 'project'
    })
  }
  
  return options
})

const timelineDates = computed(() => {
  const dates = []
  let startDate, endDate
  
  if (dateRange.value === 'project' && projectDateRange.value) {
    // Use project duration
    startDate = new Date(projectDateRange.value.start_date)
    endDate = new Date(projectDateRange.value.end_date)
  } else {
    // Use relative date ranges
    startDate = new Date()
    endDate = new Date()
    
    switch (dateRange.value) {
      case 'week':
        endDate.setDate(startDate.getDate() + 7)
        break
      case 'month':
        endDate.setMonth(startDate.getMonth() + 1)
        break
      case 'quarter':
        endDate.setMonth(startDate.getMonth() + 3)
        break
    }
  }
  
  const current = new Date(startDate)
  while (current <= endDate) {
    dates.push(new Date(current))
    current.setDate(current.getDate() + 1)
  }
  
  return dates
})

// Methods
function goBack() {
  // If we have a selected project, go back to project detail
  // Otherwise, go back to projects list
  if (selectedProjectId.value) {
    router.push({ name: 'project-detail', params: { id: selectedProjectId.value } })
  } else {
    router.push({ name: 'projects' })
  }
}

function onProjectChange() {
  selectedProject.value = availableProjects.value.find(p => p.id === selectedProjectId.value)
  loadTimelineData()
}

function onDateRangeChange() {
  loadTimelineData()
}

function toggleView() {
  isCompactView.value = !isCompactView.value
}

function formatDateHeader(date) {
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  })
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function isWeekend(date) {
  const day = date.getDay()
  return day === 0 || day === 6 // Sunday or Saturday
}

function getTasksForMemberAndDate(memberId, date) {
  return timelineTasks.value.filter(task => {
    if (task.owner !== memberId) return false
    
    const taskDate = new Date(task.due_date)
    return taskDate.toDateString() === date.toDateString()
  })
}

function getTaskCardClass(task) {
  const classes = []
  
  // Status classes
  classes.push(`status-${task.status.replace(/\s+/g, '-').toLowerCase()}`)
  
  // Priority classes
  if (task.priority >= 8) classes.push('priority-high')
  else if (task.priority >= 5) classes.push('priority-medium')
  else classes.push('priority-low')
  
  return classes.join(' ')
}

function getStatusClass(status) {
  switch (status?.toLowerCase()) {
    case 'ongoing': return 'status-ongoing'
    case 'under review': return 'status-review'
    case 'done': return 'status-completed'
    case 'unassigned': return 'status-unassigned'
    default: return 'status-default'
  }
}

function getPriorityClass(priority) {
  if (priority >= 8) return 'priority-high'
  if (priority >= 5) return 'priority-medium'
  return 'priority-low'
}

function getMemberName(memberId) {
  const member = teamMembers.value.find(m => m.employee_id === memberId)
  return member ? member.employee_name : `#${memberId}`
}

function getCollaboratorNames(collaborators) {
  if (!collaborators || !Array.isArray(collaborators)) return 'None'
  const names = collaborators.map(id => getMemberName(id))
  return names.join(', ')
}

function openTaskDetails(task) {
  selectedTask.value = task
  showTaskModal.value = true
}

async function loadTimelineData() {
  if (!selectedProjectId.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    // Use the new timeline API endpoint
    const res = await axios.get(`http://localhost:5002/projects/${selectedProjectId.value}/timeline`, { 
      withCredentials: true 
    })
    
    if (res.data) {
      timelineTasks.value = res.data.tasks || []
      teamMembers.value = res.data.team_members || []
      projectDateRange.value = res.data.project_date_range || null
    }
    
  } catch (err) {
    console.error('Error loading timeline data:', err)
    error.value = 'Failed to load timeline data. Please try again.'
    timelineTasks.value = []
    teamMembers.value = []
  } finally {
    loading.value = false
  }
}


async function loadProjects() {
  try {
    const projects = await getProjects()
    availableProjects.value = projects || []
    
    // Set initial project
    if (route.params.id) {
      selectedProjectId.value = Number(route.params.id)
      selectedProject.value = projects.find(p => p.id === selectedProjectId.value)
    } else if (projects.length > 0) {
      selectedProjectId.value = projects[0].id
      selectedProject.value = projects[0]
    }
  } catch (err) {
    console.error('Error loading projects:', err)
    error.value = 'Failed to load projects.'
  }
}

// Lifecycle
onMounted(async () => {
  await loadProjects()
  
  // If no project ID in route, select the first available project
  if (!selectedProjectId.value && availableProjects.value.length > 0) {
    selectedProjectId.value = availableProjects.value[0].id
    selectedProject.value = availableProjects.value[0]
  }
  
  if (selectedProjectId.value) {
    await loadTimelineData()
  }
})

// Watch for route changes
watch(() => route.params.id, (newId) => {
  if (newId) {
    selectedProjectId.value = Number(newId)
    selectedProject.value = availableProjects.value.find(p => p.id === selectedProjectId.value)
    loadTimelineData()
  }
})
</script>

<style scoped>
.timeline-page {
  padding: 24px;
  background-color: #f8fafc;
  min-height: 100vh;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-left h2 {
  margin: 0;
  font-size: 28px;
  color: #1f2937;
}

.breadcrumb {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.breadcrumb a {
  color: #2563eb;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.project-selector {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.project-selector label {
  font-weight: 600;
  margin-right: 12px;
}

.project-dropdown {
  min-width: 200px;
}

.timeline-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.date-range-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-range-controls label {
  font-weight: 600;
}

.date-range-dropdown {
  min-width: 150px;
}

.loading-state, .error-state, .no-data-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.no-data-content {
  max-width: 400px;
  margin: 0 auto;
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.no-data-content h3 {
  margin: 0 0 8px;
  color: #374151;
}

.no-data-content p {
  margin: 0 0 20px;
  color: #6b7280;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc2626;
  margin-bottom: 16px;
}

.timeline-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.timeline-canvas {
  overflow-x: auto;
  min-width: 100%;
}

.timeline-header-row {
  display: flex;
  border-bottom: 2px solid #e5e7eb;
  background: #f9fafb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.team-members-column {
  min-width: 200px;
  padding: 16px;
  border-right: 1px solid #e5e7eb;
  background: #f3f4f6;
}

.team-members-column h3 {
  margin: 0;
  font-size: 16px;
  color: #374151;
}

.dates-row {
  display: flex;
  flex: 1;
}

.date-column {
  min-width: 80px;
  padding: 12px 8px;
  text-align: center;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
}

.date-column.is-weekend {
  background: #fef2f2;
}

.date-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.timeline-rows {
  min-height: 400px;
}

.timeline-row {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  min-height: 80px;
}

.timeline-row:hover {
  background: #f8fafc;
}

.member-info {
  min-width: 200px;
  padding: 16px;
  border-right: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.member-details {
  flex: 1;
}

.member-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.member-role {
  font-size: 12px;
  color: #6b7280;
}

.tasks-row {
  display: flex;
  flex: 1;
}

.date-cell {
  min-width: 80px;
  padding: 8px 4px;
  border-right: 1px solid #e5e7eb;
  background: white;
  position: relative;
}

.date-cell.is-weekend {
  background: #fef2f2;
}

.task-card {
  background: #3b82f6;
  color: white;
  padding: 6px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
  cursor: pointer;
  font-size: 11px;
  line-height: 1.2;
  transition: all 0.2s ease;
  min-width: 60px;
}

.task-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.task-title {
  font-weight: 600;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  opacity: 0.9;
}

/* Status classes */
.task-card.status-ongoing {
  background: #3b82f6;
}

.task-card.status-under-review {
  background: #f59e0b;
}

.task-card.status-done {
  background: #10b981;
}

.task-card.status-unassigned {
  background: #6b7280;
}

/* Priority classes */
.task-card.priority-high {
  border-left: 4px solid #dc2626;
}

.task-card.priority-medium {
  border-left: 4px solid #f59e0b;
}

.task-card.priority-low {
  border-left: 4px solid #10b981;
}

/* Task Detail Modal */
.task-detail-modal {
  max-width: 800px;
  min-width: 600px;
}

.task-detail-modal :deep(.p-dialog) {
  max-width: 800px !important;
  min-width: 600px !important;
  width: 600px !important;
}

.task-detail-modal :deep(.p-dialog-content) {
  min-width: 600px !important;
}

.task-details {
  padding: 20px 0;
}

.detail-row {
  margin-bottom: 16px;
}

.detail-row label {
  font-weight: 600;
  color: #374151;
  display: block;
  margin-bottom: 4px;
}

.detail-row p {
  margin: 0;
  color: #6b7280;
  line-height: 1.5;
}

.status-badge, .priority-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-ongoing { background: #dbeafe; color: #1e40af; }
.status-review { background: #fef3c7; color: #92400e; }
.status-completed { background: #d1fae5; color: #065f46; }
.status-unassigned { background: #f3f4f6; color: #374151; }

.priority-high { background: #fee2e2; color: #991b1b; }
.priority-medium { background: #fef3c7; color: #92400e; }
.priority-low { background: #d1fae5; color: #065f46; }

/* Compact View Styles */
.timeline-container.compact-view .team-members-column {
  min-width: 120px;
}

.timeline-container.compact-view .member-info.compact {
  min-width: 120px;
  padding: 8px 12px;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.timeline-container.compact-view .member-avatar.compact {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
}

.timeline-container.compact-view .member-name-compact {
  font-size: 11px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.2;
}

.timeline-container.compact-view .date-column.compact {
  min-width: 50px;
  padding: 8px 4px;
}

.timeline-container.compact-view .date-label.compact {
  font-size: 10px;
  font-weight: 500;
}

.timeline-container.compact-view .date-cell.compact {
  min-width: 50px;
  padding: 4px 2px;
}

.timeline-container.compact-view .task-card.compact {
  padding: 3px 4px;
  margin-bottom: 2px;
  font-size: 9px;
  line-height: 1.1;
  border-radius: 3px;
  min-width: 40px;
}

.timeline-container.compact-view .task-card.compact .task-title {
  font-size: 9px;
  margin-bottom: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-container.compact-view .task-priority-compact {
  font-size: 8px;
  opacity: 0.8;
  text-align: center;
}

.timeline-container.compact-view .timeline-row {
  min-height: 50px;
}

.timeline-container.compact-view .member-info {
  min-height: 50px;
}

/* Responsive */
@media (max-width: 768px) {
  .timeline-page {
    padding: 16px;
  }
  
  .timeline-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .timeline-controls {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .team-members-column {
    min-width: 150px;
  }
  
  .member-info {
    min-width: 150px;
  }
  
  .date-column {
    min-width: 60px;
  }
  
  .date-cell {
    min-width: 60px;
  }
  
  /* Compact view responsive adjustments */
  .timeline-container.compact-view .team-members-column {
    min-width: 100px;
  }
  
  .timeline-container.compact-view .member-info.compact {
    min-width: 100px;
  }
  
  .timeline-container.compact-view .date-column.compact {
    min-width: 40px;
  }
  
  .timeline-container.compact-view .date-cell.compact {
    min-width: 40px;
  }
  
  /* Task detail modal responsive */
  .task-detail-modal {
    min-width: 400px;
    max-width: 95vw;
  }
}
</style>
