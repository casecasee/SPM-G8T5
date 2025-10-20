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
              @change="updateTimeline"
              class="date-input"
            />
            <span>to</span>
            <input 
              type="date" 
              v-model="endDate" 
              @change="updateTimeline"
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
          <!-- Fill remaining space -->
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
              <div class="task-title">{{ task.name }}</div>
              <div class="task-meta">
                <span class="task-status">{{ task.status }}</span>
                <span class="task-priority">P{{ task.priority }}</span>
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

// Current user info
const currentEmployeeId = Number(sessionStorage.getItem('employee_id'))
const currentRole = sessionStorage.getItem('role')
const currentDepartment = sessionStorage.getItem('department')
const currentEmployeeName = sessionStorage.getItem('employee_name')

// Computed properties
const timelineDates = computed(() => {
  if (!startDate.value || !endDate.value) return []
  
  const dates = []
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)
  
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    dates.push({
      date: new Date(d),
      key: d.toISOString().split('T')[0]
    })
  }
  
  return dates
})

// Calculate the total width needed for the timeline
const timelineWidth = computed(() => {
  if (timelineDates.value.length === 0) return '100%'
  
  // Calculate minimum width: employee column (200px) + date columns (100px each)
  const minWidth = 200 + (timelineDates.value.length * 100)
  
  // Always use the calculated minimum width to ensure scrolling works
  return `${minWidth}px`
})

// Helper functions
function formatDateLabel(date) {
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  })
}

function formatDayLabel(date) {
  return date.toLocaleDateString('en-US', { 
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

function getTasksForEmployee(employeeId) {
  return timelineData.value
    .filter(task => 
      task.owner === employeeId || task.collaborators.includes(employeeId)
    )
    .sort((a, b) => {
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

function getTaskBarStyle(task) {
  // Parse dates as local dates (no timezone conversion)
  const taskStart = new Date(task.created_at)
  const taskEnd = new Date(task.due_date)
  const now = new Date()
  
  if (!startDate.value || !endDate.value || timelineDates.value.length === 0) {
    return { display: 'none' }
  }
  
  // Parse timeline dates as local dates (no timezone conversion)
  const timelineStart = new Date(startDate.value + 'T00:00:00')
  const timelineEnd = new Date(endDate.value + 'T23:59:59')
  
  // Convert task dates to local dates for comparison (date only, no time)
  const taskStartLocal = new Date(taskStart.getFullYear(), taskStart.getMonth(), taskStart.getDate())
  const taskEndLocal = new Date(taskEnd.getFullYear(), taskEnd.getMonth(), taskEnd.getDate())
  
  // For overdue tasks, extend the bar to show the original due date
  let displayEndDate = taskEndLocal
  if (task.status.toLowerCase() !== 'done' && taskEndLocal < now) {
    // Task is overdue - extend bar to current date or timeline end, whichever is smaller
    displayEndDate = new Date(Math.min(now.getTime(), timelineEnd.getTime()))
  }
  
  // Find the exact day index in the timeline dates array
  const taskStartDayIndex = timelineDates.value.findIndex(dateObj => {
    const timelineDate = new Date(dateObj.date.getFullYear(), dateObj.date.getMonth(), dateObj.date.getDate())
    const taskDate = new Date(taskStartLocal.getFullYear(), taskStartLocal.getMonth(), taskStartLocal.getDate())
    return timelineDate.getTime() === taskDate.getTime()
  })
  
  const taskEndDayIndex = timelineDates.value.findIndex(dateObj => {
    const timelineDate = new Date(dateObj.date.getFullYear(), dateObj.date.getMonth(), dateObj.date.getDate())
    const taskDate = new Date(displayEndDate.getFullYear(), displayEndDate.getMonth(), displayEndDate.getDate())
    return timelineDate.getTime() === taskDate.getTime()
  })
  
  // If task dates are outside timeline range, don't show
  if (taskStartDayIndex === -1 && taskEndDayIndex === -1) {
    return { display: 'none' }
  }
  
  // Use the found indices or clamp to timeline bounds
  const actualStartDay = taskStartDayIndex === -1 ? 0 : taskStartDayIndex
  const actualEndDay = taskEndDayIndex === -1 ? timelineDates.value.length - 1 : taskEndDayIndex
  
  const taskDuration = Math.max(1, actualEndDay - actualStartDay + 1)
  
  // Calculate position based on the actual timeline width
  // Each date column is 100px wide, so we calculate pixel positions
  const leftPixels = actualStartDay * 100
  const widthPixels = taskDuration * 100
  
  return {
    left: `${leftPixels}px`,
    width: `${widthPixels}px`,
    height: '52px',
    zIndex: 1
  }
}

function getTaskClass(task) {
  const classes = []
  
  // Status-based styling
  switch (task.status.toLowerCase()) {
    case 'ongoing':
      classes.push('status-ongoing')
      break
    case 'under review':
      classes.push('status-review')
      break
    case 'done':
      classes.push('status-completed')
      break
    case 'unassigned':
      classes.push('status-unassigned')
      break
    default:
      classes.push('status-default')
  }
  
  // Priority-based styling
  if (task.priority >= 8) {
    classes.push('priority-high')
  } else if (task.priority >= 5) {
    classes.push('priority-medium')
  } else {
    classes.push('priority-low')
  }
  
  // Completion status indicators
  if (task.status.toLowerCase() === 'done') {
    const dueDate = new Date(task.due_date)
    const completedDate = new Date(task.created_at) // Using created_at as completion date for now
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
  let tooltip = `${task.name}\nStatus: ${task.status}\nPriority: ${task.priority}\nDue: ${dueDate.toLocaleDateString()}`
  
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

function isCompletedEarly(task) {
  if (task.status.toLowerCase() !== 'done') return false
  const dueDate = new Date(task.due_date)
  const completedDate = new Date(task.created_at)
  return completedDate < dueDate
}

function isOverdue(task) {
  if (task.status.toLowerCase() === 'done') return false
  const dueDate = new Date(task.due_date)
  const now = new Date()
  return dueDate < now
}

function openTaskDetails(task) {
  // Navigate back to tasks page and open the specific task
  router.push({ 
    name: 'tasks',
    query: { taskId: task.id }
  })
}

function updateTimeline() {
  loadTimeline()
}

async function loadTimeline() {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch all tasks
    const res = await axios.get('http://localhost:5002/tasks', {
      withCredentials: true
    })
    
    const allTasks = (res.data.tasks || []).map(t => ({
      id: t.task_id,
      name: t.title,
      description: t.description,
      due_date: t.deadline,
      created_at: t.created_at,
      status: t.status,
      priority: t.priority || 5,
      owner: t.owner,
      collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(id => Number(id)) : [],
      project_id: t.project_id
    }))
    
    // Filter tasks based on user role
    let filteredTasks = []
    if (currentRole === 'staff') {
      // Staff can only see their own tasks
      filteredTasks = allTasks.filter(task => 
        task.owner === currentEmployeeId || task.collaborators.includes(currentEmployeeId)
      )
    } else if (currentRole === 'manager') {
      // Managers can see department tasks
      const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(currentDepartment)}`, {
        withCredentials: true
      })
      const departmentEmployeeIds = res.data.map(emp => emp.employee_id)
      filteredTasks = allTasks.filter(task => 
        departmentEmployeeIds.includes(task.owner) || 
        task.collaborators.some(collab => departmentEmployeeIds.includes(collab))
      )
    } else {
      // Senior managers and HR can see all tasks
      filteredTasks = allTasks
    }
    
    timelineData.value = filteredTasks
    
    // Get unique employees from filtered tasks
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
      const dates = filteredTasks.map(task => new Date(task.created_at))
      const dueDates = filteredTasks.map(task => new Date(task.due_date))
      const allDates = [...dates, ...dueDates]
      
      if (allDates.length > 0) {
        const minDate = new Date(Math.min(...allDates))
        const maxDate = new Date(Math.max(...allDates))
        
        // Extend range by 7 days on each side
        minDate.setDate(minDate.getDate() - 7)
        maxDate.setDate(maxDate.getDate() + 7)
        
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

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
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

.btn-secondary {
  background: #6b7280;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-secondary:hover {
  background: #4b5563;
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

.legend-marker {
  width: 16px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  position: relative;
}

.legend-marker.completion-marker {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #059669;
}

.legend-marker.completion-marker::before {
  content: '✓';
  position: absolute;
  top: -2px;
  left: 50%;
  transform: translateX(-50%);
  background: #059669;
  color: white;
  font-size: 8px;
  font-weight: bold;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.legend-marker.due-marker {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #dc2626;
}

.legend-marker.due-marker::before {
  content: 'DUE';
  position: absolute;
  top: -2px;
  left: 50%;
  transform: translateX(-50%);
  background: #dc2626;
  color: white;
  font-size: 6px;
  font-weight: bold;
  padding: 1px 2px;
  border-radius: 2px;
  white-space: nowrap;
}


.timeline-grid {
  overflow-x: auto;
  overflow-y: auto;
  width: 100%;
  max-height: 70vh;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  /* Firefox scrollbar styling */
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

/* Custom scrollbar styling */
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

.task-cell {
  min-width: 100px;
  padding: 4px;
  border-right: 1px solid #f3f4f6;
  background: white;
  min-height: 60px;
  position: relative;
}

.task-cell.weekend {
  background: #fefefe;
}

.task-cell.today {
  background: #f0f9ff;
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

.task-item {
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  padding: 4px 6px;
  margin-bottom: 2px;
  cursor: pointer;
  font-size: 11px;
  line-height: 1.2;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.task-item:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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

/* Completion line for early completed tasks */
.completion-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: var(--completion-line-position, 0);
  width: 2px;
  background: rgba(255, 255, 255, 0.8);
  z-index: 2;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.3);
}

.completion-line::before {
  content: '✓';
  position: absolute;
  top: 2px;
  left: -6px;
  background: rgba(255, 255, 255, 0.9);
  color: #059669;
  font-size: 10px;
  font-weight: bold;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Due date marker for overdue tasks */
.due-date-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  left: var(--due-date-position, 0);
  width: 2px;
  background: rgba(255, 255, 255, 0.9);
  z-index: 2;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.4);
}

.due-date-marker::before {
  content: 'DUE';
  position: absolute;
  top: 2px;
  left: -12px;
  background: rgba(255, 255, 255, 0.95);
  color: #dc2626;
  font-size: 8px;
  font-weight: bold;
  padding: 1px 3px;
  border-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}


/* Task item styling improvements */
.task-item {
  position: relative;
  overflow: hidden;
}

.task-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.3);
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
