<template>
  <div class="tasks-timeline-page">
    <div class="timeline-header">
        <div class="header-left">
            <h2>Tasks Timeline</h2>
            <p class="breadcrumb">
                <a href="#" @click.prevent="goBack">Tasks</a> / 
                <span>Timeline View</span>
            </p>
        </div>
        <div class="header-right">
            <Button label="Back to Tasks" class="btn" @click="goBack" />
        </div>
    </div>

    <div v-if="loading" class="card">Loading timeline...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="timelineData.length === 0" class="no-tasks">
      <i class="pi pi-calendar-times"></i>
      <p>No tasks found for timeline view.</p>
    </div>

    <div v-else class="timeline-container">
      <!-- Timeline Controls -->
      <div class="timeline-controls">
        <div class="date-range">
          <label>Date Range:</label>
          <div class="date-inputs">
            <input 
              type="date" 
              v-model="startDate" 
              @change="loadTimeline"
              class="date-input"
            />
            <span>to</span>
            <input 
              type="date" 
              v-model="endDate" 
              @change="loadTimeline"
              class="date-input"
            />
          </div>
        </div>
        
        <!-- Legend -->
        <div class="timeline-legend">
          <div class="legend-title">Legend:</div>
          <div class="legend-items">
            <div class="legend-item">
              <div class="legend-color completed-early"></div>
              <span>Completed Early</span>
            </div>
            <div class="legend-item">
              <div class="legend-color completed-on-time"></div>
              <span>Completed On Time</span>
            </div>
            <div class="legend-item">
              <div class="legend-color completed-late"></div>
              <span>Completed Late</span>
            </div>
            <div class="legend-item">
              <div class="legend-color overdue"></div>
              <span>Overdue</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline Grid -->
      <div class="timeline-grid">
        <!-- Timeline Header -->
        <div class="timeline-header-grid" :style="{ width: timelineWidth }">
          <div class="employee-column">
            <div class="header-label">My Tasks</div>
            <div class="employee-list">
              <div class="employee-header-item">
                <div class="employee-name">{{ currentEmployeeName }}</div>
                <div class="employee-role">{{ currentRole }}</div>
              </div>
            </div>
          </div>
          <div 
            v-for="date in timelineDates" 
            :key="date.key"
            class="date-column"
            :class="{ 'weekend': isWeekend(date.date), 'today': isToday(date.date) }"
          >
            <div class="date-label">{{ formatDateLabel(date.date) }}</div>
            <div class="day-label">{{ formatDayLabel(date.date) }}</div>
          </div>
          <div class="timeline-filler"></div>
        </div>

        <!-- Timeline Rows -->
        <div class="employee-section" :style="{ width: timelineWidth }">
          <!-- Task Rows -->
          <div 
            v-for="task in getTasksForEmployee(currentEmployeeId)"
            :key="task.id"
            class="task-row"
          >
            <div class="task-info">
              <div class="task-title clickable-title" @click="openSubtaskView(task)">
                {{ task.name }}
                <i class="pi pi-external-link title-link-icon"></i>
              </div>
              <div class="task-meta">
                <span class="task-status">{{ task.status }}</span>
                <span class="task-priority">P{{ task.priority }}</span>
                <span class="subtask-count">{{ getSubtasksForParent(task.id).length }} subtasks</span>
              </div>
            </div>
            <div class="task-timeline-row">
              <div 
                class="task-bar"
                :class="getTaskClass(task)"
                :style="getTaskBarStyle(task)"
                :title="getTaskTooltip(task)"
                @click="openTaskDetails(task)"
              >
                <div class="task-bar-content">
                  <div class="task-title">{{ task.name }}</div>
                  <div class="task-meta">
                    <span class="task-status">{{ task.status }}</span>
                    <span class="task-priority">P{{ task.priority }}</span>
                  </div>
                </div>
              </div>
              <!-- Fill remaining space -->
              <div class="timeline-filler"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Subtask Timeline Modal -->
    <div v-if="showSubtaskView" class="subtask-modal-overlay" @click="closeSubtaskView">
      <div class="subtask-modal" @click.stop>
        <div class="subtask-header">
          <h3>{{ selectedParentTask?.name }}</h3>
          <button @click="closeSubtaskView" class="close-button">
            <i class="pi pi-times"></i>
          </button>
        </div>
        
        <div class="subtask-content">
          <div class="subtask-timeline-grid">
            <!-- Subtask Timeline Header -->
            <div class="subtask-timeline-header" :style="{ width: subtaskTimelineWidth }">
              <div class="subtask-employee-column">
                <div class="subtask-header-label">Subtasks</div>
                <div class="subtask-date-range">
                  {{ formatDateLabel(subtaskTimelineDates[0]?.date) }} - {{ formatDateLabel(subtaskTimelineDates[subtaskTimelineDates.length - 1]?.date) }}
                </div>
              </div>
              <div 
                v-for="date in subtaskTimelineDates" 
                :key="date.key"
                class="subtask-date-column"
                :class="{ 'weekend': isWeekend(date.date), 'today': isToday(date.date) }"
              >
                <div class="date-label">{{ formatDateLabel(date.date) }}</div>
                <div class="day-label">{{ formatDayLabel(date.date) }}</div>
              </div>
              <div class="timeline-filler"></div>
            </div>

            <!-- Subtask Rows -->
            <div class="subtask-section" :style="{ width: subtaskTimelineWidth }">
              <div 
                v-for="subtask in getSubtasksForParent(selectedParentTask?.id)"
                :key="subtask.id"
                class="subtask-row"
              >
                <div class="subtask-info">
                  <div class="subtask-title">{{ subtask.name }}</div>
                  <div class="subtask-meta">
                    <span class="task-status">{{ subtask.status }}</span>
                    <span class="task-priority">P{{ subtask.priority }}</span>
                  </div>
                </div>
                <div class="subtask-timeline-row">
                  <div 
                    class="subtask-bar"
                    :class="getTaskClass(subtask)"
                    :style="getTaskBarStyle(subtask, true)"
                    :title="getTaskTooltip(subtask)"
                    @click="openTaskDetails(subtask)"
                  >
                    <div class="task-bar-content">
                      <div class="task-title">{{ subtask.name }}</div>
                      <div class="task-meta">
                        <span class="task-status">{{ subtask.status }}</span>
                        <span class="task-priority">P{{ subtask.priority }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="timeline-filler"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import axios from 'axios'

const router = useRouter()

// State
const loading = ref(false)
const error = ref('')
const timelineData = ref([])
const timelineEmployees = ref([])
const startDate = ref('')
const endDate = ref('')
const selectedParentTask = ref(null)
const showSubtaskView = ref(false)

// Current user info
const currentEmployeeId = Number(sessionStorage.getItem('employee_id'))
const currentRole = sessionStorage.getItem('role')
const currentDepartment = sessionStorage.getItem('department')
const currentEmployeeName = sessionStorage.getItem('employee_name')

// Helper function to generate date ranges
function generateDateRange(startDate, endDate) {
  if (!startDate || !endDate) return []
  
  const dates = []
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    dates.push({
      date: new Date(d),
      key: d.toISOString().split('T')[0]
    })
  }
  
  return dates
}

// Helper function to calculate timeline width
function calculateTimelineWidth(dateCount) {
  if (dateCount === 0) return '100%'
  const minWidth = 200 + (dateCount * 100)
  return `${minWidth}px`
}

// Computed properties for subtask timeline
const subtaskTimelineDates = computed(() => {
  if (!selectedParentTask.value) return []
  
  const parentStart = selectedParentTask.value.created_at.replace(/:\d{2}[.Z].*$/, '')
  const parentEnd = selectedParentTask.value.due_date.replace(/:\d{2}[.Z].*$/, '')
  
  return generateDateRange(parentStart, parentEnd)
})

const subtaskTimelineWidth = computed(() => {
  return calculateTimelineWidth(subtaskTimelineDates.value.length)
})

// Computed properties for main timeline
const timelineDates = computed(() => {
  return generateDateRange(startDate.value, endDate.value)
})

const timelineWidth = computed(() => {
  return calculateTimelineWidth(timelineDates.value.length)
})

// Helper functions
const toLocal = iso => {
  if (!iso) return null
  // Handle both ISO format and MySQL DATETIME format
  let date
  if (iso.includes('T')) {
      // ISO format: "2025-10-30T15:18:00.000Z"
      date = new Date(iso)
  } else {
      // MySQL DATETIME format: "2025-10-30 15:18:00"
      date = new Date(iso.replace(' ', 'T'))
  }
  return date.toLocaleString(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
  })
}

function formatDateLabel(date) {
  return date.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  })
}

function formatDayLabel(date) {
  return date.toLocaleString('en-US', { 
    weekday: 'short' 
  })
}

function isWeekend(date) {
  const day = date.getDay()
  return day === 0 || day === 6
}

function isToday(date) {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

// Helper function to sort tasks by priority and due date
function sortTasksByPriorityAndDueDate(tasks) {
  return tasks.sort((a, b) => {
    // Sort by priority (highest first), then by due date (earliest first)
    const priorityA = a.priority || 5
    const priorityB = b.priority || 5
    
    if (priorityA !== priorityB) {
      return priorityB - priorityA // Higher priority first
    }
    
    // If same priority, sort by due date (earliest first)
    const dueDateA = new Date(a.due_date)
    const dueDateB = new Date(b.due_date)
    return dueDateA - dueDateB
  })
}

function getTasksForEmployee(employeeId) {
  // Show only parent tasks (tasks without parent_id)
  const allTasks = timelineData.value.filter(task => 
    task.owner === employeeId || task.collaborators.includes(employeeId)
  )
  
  console.log('All tasks for employee:', allTasks.map(t => ({ 
    id: t.id, 
    name: t.name, 
    parent_id: t.parent_id 
  })))
  
  const parentTasks = allTasks.filter(task => !task.parent_id)
  const subtasks = allTasks.filter(task => task.parent_id)
  
  console.log('Parent tasks:', parentTasks.map(t => ({ id: t.id, name: t.name })))
  console.log('Subtasks:', subtasks.map(t => ({ id: t.id, name: t.name, parent_id: t.parent_id })))
  
  return sortTasksByPriorityAndDueDate(parentTasks)
}

function getSubtasksForParent(parentId) {
  const subtasks = timelineData.value.filter(task => 
    task.parent_id === parentId &&
    (task.owner === currentEmployeeId || task.collaborators.includes(currentEmployeeId))
  )
  
  return sortTasksByPriorityAndDueDate(subtasks)
}

function openSubtaskView(parentTask) {
  selectedParentTask.value = parentTask
  showSubtaskView.value = true
}

function closeSubtaskView() {
  showSubtaskView.value = false
  selectedParentTask.value = null
}

function getTaskBarStyle(task, isSubtaskView = false) {
  const taskStart = new Date(task.created_at.replace(/:\d{2}[.Z].*$/, ''))
  const taskEnd = new Date(task.due_date.replace(/:\d{2}[.Z].*$/, ''))
  const now = new Date()
  
  // Use different date ranges for main timeline vs subtask view
  const datesToUse = isSubtaskView ? subtaskTimelineDates.value : timelineDates.value
  
  if (datesToUse.length === 0) {
    return { display: 'none' }
  }
  
  // Convert task dates to local dates for comparison (date only, no time)
  const taskStartLocal = new Date(taskStart.getFullYear(), taskStart.getMonth(), taskStart.getDate())
  const taskEndLocal = new Date(taskEnd.getFullYear(), taskEnd.getMonth(), taskEnd.getDate())
  
  // For overdue tasks, extend the bar to show the original due date
  let displayEndDate = taskEndLocal
  if (task.status.toLowerCase() !== 'done' && taskEndLocal < now) {
    if (isSubtaskView) {
      // In subtask view, extend to parent's end date or now, whichever is smaller
      const parentEnd = new Date(selectedParentTask.value.due_date.replace(/:\d{2}[.Z].*$/, ''))
      displayEndDate = new Date(Math.min(now.getTime(), parentEnd.getTime()))
    } else {
      const timelineEnd = new Date(endDate.value)
      displayEndDate = new Date(Math.min(now.getTime(), timelineEnd.getTime()))
    }
  }
  
  // Find the exact day index in the timeline dates array
  const taskStartDayIndex = datesToUse.findIndex(dateObj => {
    const timelineDate = new Date(dateObj.date.getFullYear(), dateObj.date.getMonth(), dateObj.date.getDate())
    const taskDate = new Date(taskStartLocal.getFullYear(), taskStartLocal.getMonth(), taskStartLocal.getDate())
    return timelineDate.getTime() === taskDate.getTime()
  })
  
  const taskEndDayIndex = datesToUse.findIndex(dateObj => {
    const timelineDate = new Date(dateObj.date.getFullYear(), dateObj.date.getMonth(), dateObj.date.getDate())
    const taskDate = new Date(displayEndDate.getFullYear(), displayEndDate.getMonth(), displayEndDate.getDate())
    return timelineDate.getTime() === taskDate.getTime()
  })
  
  if (taskStartDayIndex === -1 && taskEndDayIndex === -1) {
    return { display: 'none' }
  }
  
  const actualStartDay = taskStartDayIndex === -1 ? 0 : taskStartDayIndex
  const actualEndDay = taskEndDayIndex === -1 ? datesToUse.length - 1 : taskEndDayIndex
  
  const taskDuration = Math.max(1, actualEndDay - actualStartDay + 1)
  
  const leftPixels = actualStartDay * 100;
  const widthPixels = taskDuration * 100
  
  return {
    left: `${leftPixels}px`,
    width: `${widthPixels}px`,
    height: isSubtaskView ? '45px' : '52px',
    zIndex: 1
  }
}

function getTaskClass(task) {
  const classes = []
  
  // Status-based styling
  switch (task.status.toLowerCase()) {
    case 'ongoing': classes.push('status-ongoing'); break
    case 'under review': classes.push('status-review'); break
    case 'done': classes.push('status-completed'); break
    case 'unassigned':      classes.push('status-unassigned');break
    default: classes.push('status-default'); break
  }
  
  // Priority-based styling
  if (task.priority >= 8) { 
    classes.push('priority-high');
  } 
    else if (task.priority >= 5) { 
    classes.push('priority-medium');
    } else {
    classes.push('priority-low');
  }
  
  // Completion status indicators
  if (task.status.toLowerCase() === 'done') {
    const dueDate = new Date(task.due_date)
    const completedDate = new Date(task.created_at)
    const now = new Date()
    
    if (completedDate < dueDate) {
      classes.push('completed-early')
    } else if (completedDate > dueDate) {
      classes.push('completed-late')
    } else {
      classes.push('completed-on-time')
    }
  } else {
    // Check if task is overdue
    const dueDate = new Date(task.due_date)
    const now = new Date()
    
    if (dueDate < now) {
      classes.push('overdue')
    }
  }
  
  return classes.join(' ')
}

function getTaskTooltip(task) {
  const dueDate = new Date(task.due_date)
  const now = new Date()
  let tooltip = `${task.name}\nStatus: ${task.status}\nPriority: ${task.priority}\nDue: ${toLocal(task.due_date)}`
  
  if (task.status.toLowerCase() === 'done') {
    const completedDate = new Date(task.created_at)
    const daysDiff = Math.ceil((completedDate - dueDate) / (1000 * 60 * 60 * 24))
    
    if (daysDiff < 0) {
      tooltip += `\n✅ Completed ${Math.abs(daysDiff)} days early`
    } else if (daysDiff > 0) {
      tooltip += `\n⚠️ Completed ${daysDiff} days late`
    } else {
      tooltip += `\n✅ Completed on time`
    }
  } else if (dueDate < now) {
    const daysOverdue = Math.ceil((now - dueDate) / (1000 * 60 * 60 * 24))
    tooltip += `\n🚨 Overdue by ${daysOverdue} days`
  }
  
  return tooltip
}

function openTaskDetails(task) {
  router.push({ 
    name: 'tasks',
    query: { taskId: task.id }
  })
}

async function loadTimeline() {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch all tasks
    const res = await axios.get('http://localhost:5002/tasks', {
      withCredentials: true
    })
    
    const allTasks = (res.data.tasks || []).map(t => {
      console.log(`Task: ${t.title}`)
      console.log(`Raw created_at from backend: ${t.created_at}`)
      console.log(`Raw deadline from backend: ${t.deadline}`)
      console.log('---')
      
      return {
        id: t.task_id,
        name: t.title,
        description: t.description,
        due_date: t.deadline, 
        created_at: t.created_at, 
        status: t.status,
        priority: t.priority || 5,
        parent_id: t.parent_id,
        owner: t.owner,
        collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(id => Number(id)) : [],
        project_id: t.project_id
      }
    })
    
    // Filter tasks based on user role
    let filteredTasks = []
    if (currentRole === 'staff') {
      filteredTasks = allTasks.filter(task => 
        task.owner === currentEmployeeId || task.collaborators.includes(currentEmployeeId)
      )
    } else if (currentRole === 'manager') {
      const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(currentDepartment)}`, {
        withCredentials: true
      })
      const departmentEmployeeIds = res.data.map(emp => emp.employee_id)
      filteredTasks = allTasks.filter(task => 
        departmentEmployeeIds.includes(task.owner) || 
        task.collaborators.some(collab => departmentEmployeeIds.includes(collab))
      )
    } else {
      filteredTasks = allTasks
    }
    
    timelineData.value = filteredTasks
    
    const employeeIds = new Set()
    filteredTasks.forEach(task => {
      employeeIds.add(task.owner)
      task.collaborators.forEach(collab => employeeIds.add(collab))
    })
    
    // Fetch employee details
    const employeePromises = Array.from(employeeIds).map(async (id) => {
      try {
        const res = await axios.get(`http://localhost:5000/api/internal/employee/${id}`)
        return res.data
      } catch (error) {
        return { employee_id: id, employee_name: `#${id}`, role: 'Unknown' }
      }
    })
    
    timelineEmployees.value = await Promise.all(employeePromises)
    
    // Set default date range if not set
    if (!startDate.value || !endDate.value) {
      const dates = filteredTasks.map(task => new Date(task.created_at.replace(/:\d{2}[.Z].*$/, '')))
      const dueDates = filteredTasks.map(task => new Date(task.due_date.replace(/:\d{2}[.Z].*$/, '')))
      const allDates = [...dates, ...dueDates]
      
      if (allDates.length > 0) {
        const minDate = new Date(Math.min(...allDates))
        const maxDate = new Date(Math.max(...allDates))
        
        // Extend range by 7 days on each side
        minDate.setDate(minDate.getDate() - 5)
        maxDate.setDate(maxDate.getDate() + 5)
        
        startDate.value = minDate.toISOString().split('T')[0]
        endDate.value = maxDate.toISOString().split('T')[0]
      }
    }
    
  } catch (err) {
    console.error('Error loading timeline:', err)
    error.value = 'Failed to load timeline data'
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'tasks' })
}

onMounted(() => {
  loadTimeline()
})
</script>

<style scoped>
.tasks-timeline-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
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

.card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  color: #6b7280;
}

.error {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.no-tasks {
  text-align: center;
  padding: 48px 24px;
  color: #6b7280;
}

.no-tasks i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.timeline-container {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.timeline-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 16px 24px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-range label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.date-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.timeline-legend {
  display: flex;
  align-items: center;
  gap: 12px;
}

.legend-title {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.legend-items {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.legend-color {
  width: 16px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-color.completed-early {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.legend-color.completed-on-time {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.legend-color.completed-late {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.legend-color.overdue {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}


.timeline-grid {
  overflow-x: auto;
  overflow-y: auto;
  width: 100%;
  max-height: 70vh;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

.timeline-grid::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.timeline-grid::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.timeline-grid::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.timeline-grid::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
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

.timeline-header-grid {
  display: flex;
  background: #f3f4f6;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
  min-width: max-content;
}

.timeline-filler {
  flex: 1;
  min-width: 0;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  position: relative;
}

.timeline-filler::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: repeating-linear-gradient(
    to right,
    transparent 0px,
    transparent 99px,
    #e5e7eb 100px
  );
  pointer-events: none;
}

.employee-column {
  min-width: 200px;
  width: 200px;
  padding: 12px 16px;
  font-weight: 600;
  color: #374151;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
  position: sticky;
  left: 0;
  z-index: 6;
  display: flex;
  flex-direction: column;
}

.header-label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  margin-bottom: 8px;
}

.employee-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.employee-header-item {
  padding: 4px 0;
  border-bottom: 1px solid #e5e7eb;
}

.employee-header-item:last-child {
  border-bottom: none;
}

.employee-header-item .employee-name {
  font-weight: 600;
  color: #111827;
  font-size: 12px;
}

.employee-header-item .employee-role {
  color: #6b7280;
  font-size: 10px;
  margin-top: 2px;
}

.date-column {
  min-width: 100px;
  width: 100px;
  padding: 8px;
  text-align: center;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.date-column.weekend {
  background: #fef2f2;
}

.date-column.today {
  background: #dbeafe;
  font-weight: 600;
}

.date-label {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
}

.day-label {
  color: #6b7280;
  font-size: 11px;
  margin-top: 2px;
}

.employee-section {
  border-bottom: 2px solid #e5e7eb;
  min-width: max-content;
}


.task-row {
  display: flex;
  border-bottom: 1px solid #f3f4f6;
  position: relative;
  min-height: 60px;
  min-width: max-content;
}

.task-row:hover {
  background: #f8fafc;
}

.task-info {
  width: 200px;
  min-width: 200px;
  max-width: 200px;
  padding: 12px 16px;
  border-right: 1px solid #e5e7eb;
  background: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
  position: sticky;
  left: 0;
  z-index: 4;
}

.task-info .task-title {
  font-weight: 600;
  color: #111827;
  font-size: 14px;
}

.task-info .task-meta {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

.clickable-title {
  cursor: pointer;
  color: #3b82f6;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.clickable-title:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.title-link-icon {
  font-size: 12px;
  opacity: 0.7;
}

.subtask-count {
  background: #e0e7ff;
  color: #3730a3;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.task-timeline-row {
  flex: 1;
  position: relative;
  min-height: 60px;
  background: white;
  overflow: hidden;
  min-width: max-content;
  display: flex;
}

.task-timeline-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: repeating-linear-gradient(
    to right,
    transparent 0px,
    transparent 99px,
    #f3f4f6 100px
  );
  pointer-events: none;
  z-index: 0;
}

.task-bar {
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  position: absolute;
  top: 4px;
  height: 52px;
  z-index: 1;
}

.task-bar:hover {
  transform: scaleY(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

.task-bar-content {
  padding: 4px 6px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.task-title {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 2px;
  font-size: 10px;
  opacity: 0.9;
}

.task-status {
  text-transform: capitalize;
}

.task-priority {
  font-weight: 600;
}

/* Status colors */
.status-ongoing {
  background: #3b82f6;
}

.status-review {
  background: #f59e0b;
}

.status-completed {
  background: #10b981;
}

.status-unassigned {
  background: #6b7280;
}

.status-default {
  background: #9ca3af;
}

/* Priority indicators */
.priority-high {
  border-left: 3px solid #dc2626;
}

.priority-medium {
  border-left: 3px solid #d97706;
}

.priority-low {
  border-left: 3px solid #059669;
}

/* Completion status indicators */
.completed-early {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  position: relative;
}

.completed-early::after {
  content: '✓';
  position: absolute;
  top: 2px;
  right: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.completed-on-time {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  position: relative;
}

.completed-on-time::after {
  content: '✓';
  position: absolute;
  top: 2px;
  right: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.completed-late {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  position: relative;
}

.completed-late::after {
  content: '⚠';
  position: absolute;
  top: 2px;
  right: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Overdue indicators */
.overdue {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
  animation: pulse-overdue 2s infinite;
  position: relative;
}

.overdue::after {
  content: '🚨';
  position: absolute;
  top: 2px;
  right: 4px;
  font-size: 10px;
  animation: blink 1s infinite;
}

@keyframes pulse-overdue {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.1);
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}



/* Subtask Modal Styles */
.subtask-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.subtask-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 90vw;
  max-height: 90vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.subtask-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.subtask-header h3 {
  margin: 0;
  font-size: 18px;
  color: #111827;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  color: #6b7280;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: #e5e7eb;
  color: #374151;
}

.subtask-content {
  flex: 1;
  overflow: auto;
  padding: 10px;
}

.subtask-timeline-grid {
  overflow-x: auto;
  overflow-y: auto;
  width: 100%;
  max-height: 60vh;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.subtask-timeline-header {
  display: flex;
  background: #f3f4f6;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
  min-width: max-content;
}

.subtask-employee-column {
  min-width: 200px;
  width: 200px;
  padding: 12px 16px;
  font-weight: 600;
  color: #374151;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
  position: sticky;
  left: 0;
  z-index: 6;
}

.subtask-header-label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.subtask-date-range {
  color: #6b7280;
  font-size: 11px;
  margin-top: 4px;
  font-weight: 500;
}

.subtask-date-column {
  min-width: 100px;
  width: 100px;
  padding: 8px;
  text-align: center;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
  flex-shrink: 0;
}

.subtask-section {
  border-bottom: 2px solid #e5e7eb;
  min-width: max-content;
}

.subtask-row {
  display: flex;
  border-bottom: 1px solid #f3f4f6;
  position: relative;
  min-height: 35px;
  min-width: max-content;
  background: #fafbfc;
}

.subtask-row:hover {
  background: #f8fafc;
}

.subtask-info {
  width: 200px;
  min-width: 200px;
  max-width: 200px;
  padding: 8px 16px;
  border-right: 1px solid #e5e7eb;
  background: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
  position: sticky;
  left: 0;
  z-index: 4;
}

.subtask-title {
  font-weight: 500;
  color: #111827;
  font-size: 12px;
  line-height: 1.2;
}

.subtask-meta {
  color: #6b7280;
  font-size: 10px;
  margin-top: 1px;
}

.subtask-timeline-row {
  flex: 1;
  position: relative;
  min-height: 35px;
  background: white;
  overflow: hidden;
  min-width: max-content;
  display: flex;
}

.subtask-timeline-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: repeating-linear-gradient(
    to right,
    transparent 0px,
    transparent 99px,
    #f3f4f6 100px
  );
  pointer-events: none;
  z-index: 0;
}

.subtask-bar {
  background: #6366f1;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  position: absolute;
  top: 2px;
  height: 31px;
  z-index: 1;
}

.subtask-bar:hover {
  transform: scaleY(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 2;
}

/* Responsive design */
@media (max-width: 768px) {
  .tasks-timeline-page {
    padding: 16px;
  }
  
  .timeline-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .date-range {
    justify-content: center;
  }
  
  .timeline-legend {
    justify-content: center;
  }
  
  .legend-items {
    justify-content: center;
    gap: 12px;
  }
  
  .legend-item {
    font-size: 11px;
  }
  
  .timeline-grid {
    max-height: 60vh;
    border: 12px solid #e5e7eb;
  }
  
  .employee-column, .employee-cell {
    min-width: 150px;
  }
  
  .date-column, .task-cell {
    min-width: 80px;
  }
  
  .task-item {
    font-size: 10px;
    padding: 3px 4px;
  }
  
  .task-meta {
    font-size: 9px;
  }
}
</style>
