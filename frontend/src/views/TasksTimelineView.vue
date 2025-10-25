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

    <!-- Tabs visible to all users -->
    <div class="tabs">
      <button :class="['tab', currentTab==='my' ? 'active' : '']" @click="currentTab='my'">My Tasks</button>
      <button :class="['tab', currentTab==='team' ? 'active' : '']" @click="currentTab='team'" v-if="canViewTeamTasks">Team's Tasks</button>
      <button :class="['tab', currentTab==='departments' ? 'active' : '']" @click="currentTab='departments'" v-if="isSeniorManagerOrHR">All Departments</button>
    </div>

    <!-- Team search bar -->
    <div v-if="currentTab==='team'" class="team-search-section">
      <!-- Search bar -->
      <InputText v-model="teamSearch" placeholder="Search employee by name" class="input-field" />

      <!-- Employee grid -->
      <div class="employee-grid">
        <div
          v-for="emp in filteredEmployeesForTeam.length ? filteredEmployeesForTeam : availableEmployees.filter(e => e.employee_id !== currentEmployeeId)"
          :key="emp.employee_id"
          class="employee-card"
          :class="teamSelectedEmployeeId === emp.employee_id ? 'selected' : ''"
          @click="teamSelectedEmployeeId = emp.employee_id"
        >
          <div class="employee-avatar">
            <i class="pi pi-user" style="font-size:1.2rem;"></i>
          </div>
          <div class="employee-name">{{ emp.employee_name }}</div>
          <div class="employee-role">{{ emp.role }}</div>
        </div>
      </div>
    </div>

    <!-- Department selection for Senior Managers and HR -->
    <div v-if="isSeniorManagerOrHR && currentTab==='departments'" class="department-section">
      <!-- Department selection -->
      <div class="department-selection">
        <h3>Select Department</h3>
        <div class="department-grid">
          <div
            v-for="dept in departments"
            :key="dept"
            class="department-card"
            :class="selectedDepartment === dept ? 'selected' : ''"
            @click="selectDepartment(dept)"
          >
            <div class="department-icon">
              <i class="pi pi-building" style="font-size:1.5rem;"></i>
            </div>
            <div class="department-name">{{ dept }}</div>
          </div>
        </div>
      </div>

      <!-- Employee selection within department -->
      <div v-if="selectedDepartment" class="employee-selection">
        <h3>{{ selectedDepartment }} Employees</h3>
        <!-- Search bar -->
        <InputText v-model="departmentSearch" placeholder="Search employee by name" class="input-field" />

        <!-- Employee grid -->
        <div class="employee-grid">
          <div
            v-for="emp in filteredEmployeesForDepartment.length ? filteredEmployeesForDepartment : departmentEmployees.filter(e => e.employee_id !== currentEmployeeId)"
            :key="emp.employee_id"
            class="employee-card"
            :class="departmentSelectedEmployeeId === emp.employee_id ? 'selected' : ''"
            @click="selectDepartmentEmployee(emp.employee_id)"
          >
            <div class="employee-avatar">
              <i class="pi pi-user" style="font-size:1.2rem;"></i>
            </div>
            <div class="employee-name">{{ emp.employee_name }}</div>
            <div class="employee-role">{{ emp.role }}</div>
            <div class="employee-department">{{ emp.department }} - {{ emp.team }}</div>
          </div>
        </div>
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
            v-for="task in getDisplayTasks()"
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

    <!-- Task Detail Modal -->
    <Dialog v-model:visible="showModal" modal 
          header="Task Details" 
          class="clean-modal">
      <div class="modal-content">
        <!-- Basic Information Section -->
        <div class="form-section">
          <h3 class="section-title">Basic Information</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Task Name</label>
              <div class="form-display">{{ taskForm.name }}</div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Description</label>
              <div class="form-display">{{ taskForm.description || 'No description provided' }}</div>
            </div>
          </div>

          <div class="form-row-3">
            <div class="form-group">
              <label class="form-label">Status</label>
              <div class="form-display">
                <span :class="['status-display', getStatusClass(taskForm.status)]">
                  {{ taskForm.status }}
                </span>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">Priority</label>
              <div class="form-display">
                <span :class="['priority-display', getPriorityClass(taskForm.priority)]">
                  P{{ taskForm.priority }}
                </span>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">Due Date</label>
              <div class="form-display">{{ formatDate(taskForm.due_date) }}</div>
            </div>
          </div>
        </div>

        <!-- Assignment Information Section -->
        <div class="form-section">
          <h3 class="section-title">Assignment Information</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Owner</label>
              <div class="form-display">{{ getOwnerName(taskForm.owner) }}</div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Collaborators</label>
              <div class="form-display">{{ getCollaboratorNames(taskForm.collaborators) || 'None' }}</div>
            </div>
          </div>
        </div>

        <!-- Comments Section -->
        <div class="form-section">
          <h3 class="section-title">Comments</h3>
          
          <div v-if="comments.length === 0" class="no-comments">
            No comments yet
          </div>
          
          <div v-else class="comments-list">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-content">
                <div class="comment-meta">
                  <span>{{ comment.author_name }}</span>
                  <span>{{ formatDate(comment.created_at) }}</span>
                </div>
                <div class="comment-text">{{ comment.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import axios from 'axios'

const router = useRouter()

// State
const loading = ref(false)
const error = ref('')
const timelineData = ref([])
const startDate = ref('')
const endDate = ref('')
const selectedParentTask = ref(null)
const showSubtaskView = ref(false)

// Tab state
const currentTab = ref('my')
const teamSearch = ref('')
const departmentSearch = ref('')
const teamSelectedEmployeeId = ref(null)
const departmentSelectedEmployeeId = ref(null)
const availableEmployees = ref([])
const departmentEmployees = ref([])
const departments = ref([])
const selectedDepartment = ref('')

// Modal state
const selectedTask = ref(null)
const showModal = ref(false)
const taskForm = ref({})
const comments = ref([])

// Current user info
const currentEmployeeId = Number(sessionStorage.getItem('employee_id'))
const currentRole = sessionStorage.getItem('role')
const currentDepartment = sessionStorage.getItem('department')
const currentEmployeeName = sessionStorage.getItem('employee_name')

// Access control logic
const canViewTeamTasks = computed(() => {
  const role = (currentRole || '').toLowerCase()
  return role === 'manager' || role === 'staff'
})

const isSeniorManagerOrHR = computed(() => {
  const role = (currentRole || '').toLowerCase()
  const dept = (currentDepartment || '')
  return role === 'senior manager' || dept === 'HR' || role === 'director'
})

// Filtered employees for team tab
const filteredEmployeesForTeam = computed(() => {
  const search = teamSearch.value.toLowerCase()
  return availableEmployees.value.filter(emp => 
    emp.employee_id !== currentEmployeeId &&
    (emp.employee_name.toLowerCase().includes(search) || 
     emp.role.toLowerCase().includes(search))
  )
})

// Filtered employees for department tab
const filteredEmployeesForDepartment = computed(() => {
  const search = departmentSearch.value.toLowerCase()
  return departmentEmployees.value.filter(emp => 
    emp.employee_id !== currentEmployeeId &&
    (emp.employee_name.toLowerCase().includes(search) || 
     emp.role.toLowerCase().includes(search) ||
     emp.department.toLowerCase().includes(search) ||
     emp.team.toLowerCase().includes(search))
  )
})

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
  let date
  if (iso.includes('T')) {
      date = new Date(iso)
  } else {
      date = new Date(iso.replace(' ', 'T'))
  }
  return date.toLocaleString(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
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
    const priorityA = a.priority || 5
    const priorityB = b.priority || 5
    
    if (priorityA !== priorityB) {
      return priorityB - priorityA
    }
    
    const dueDateA = new Date(a.due_date)
    const dueDateB = new Date(b.due_date)
    return dueDateA - dueDateB
  })
}

function getTasksForEmployee(employeeId) {
  const allTasks = timelineData.value.filter(task => 
    task.owner === employeeId || task.collaborators.includes(employeeId)
  )
  
  const parentTasks = allTasks.filter(task => !task.parent_id)
  
  return sortTasksByPriorityAndDueDate(parentTasks)
}

// Get tasks based on current tab
function getDisplayTasks() {
  if (currentTab.value === 'my') {
    return getTasksForEmployee(currentEmployeeId)
  } else if (currentTab.value === 'team') {
    if (!teamSelectedEmployeeId.value) return []
    return getTasksForEmployee(Number(teamSelectedEmployeeId.value))
  } else if (currentTab.value === 'departments') {
    if (!departmentSelectedEmployeeId.value) return []
    return getTasksForEmployee(Number(departmentSelectedEmployeeId.value))
  }
  return []
}

function getSubtasksForParent(parentId) {
  const parentTask = timelineData.value.find(task => task.id === parentId)
  if (!parentTask || !parentTask.subtasks) {
    return []
  }
  
  // Determine which employee ID to use for filtering subtasks
  let targetEmployeeId = currentEmployeeId
  if (currentTab.value === 'team' && teamSelectedEmployeeId.value) {
    targetEmployeeId = Number(teamSelectedEmployeeId.value)
  } else if (currentTab.value === 'departments' && departmentSelectedEmployeeId.value) {
    targetEmployeeId = Number(departmentSelectedEmployeeId.value)
  }
  
  const accessibleSubtasks = parentTask.subtasks.filter(subtask => 
    subtask.owner === targetEmployeeId || subtask.collaborators.includes(targetEmployeeId)
  )
  
  return sortTasksByPriorityAndDueDate(accessibleSubtasks)
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
  
  const datesToUse = isSubtaskView ? subtaskTimelineDates.value : timelineDates.value
  
  if (datesToUse.length === 0) {
    return { display: 'none' }
  }
  
  const taskStartLocal = new Date(taskStart.getFullYear(), taskStart.getMonth(), taskStart.getDate())
  const taskEndLocal = new Date(taskEnd.getFullYear(), taskEnd.getMonth(), taskEnd.getDate())
  
  let displayEndDate = taskEndLocal
  if (task.status.toLowerCase() !== 'done' && taskEndLocal < now) {
    if (isSubtaskView) {
      const parentEnd = new Date(selectedParentTask.value.due_date.replace(/:\d{2}[.Z].*$/, ''))
      displayEndDate = new Date(Math.min(now.getTime(), parentEnd.getTime()))
    } else {
      const timelineEnd = new Date(endDate.value)
      displayEndDate = new Date(Math.min(now.getTime(), timelineEnd.getTime()))
    }
  }
  
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
  openDetails(task)
}

function openDetails(task) {
  selectedTask.value = task
  
  // Convert displayed date back to datetime-local format for editing
  let formattedDueDate = null
  if (task.due_date) {
    try {
      const date = new Date(task.due_date)
      if (!isNaN(date.getTime())) {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        formattedDueDate = `${year}-${month}-${day}T${hours}:${minutes}`
      }
    } catch (e) {
      console.error('Error parsing due date:', task.due_date, e)
    }
  }
  
  taskForm.value = {
    id: task.id,
    name: task.name,
    description: task.description,
    due_date: formattedDueDate,
    status: task.status,
    priority: task.priority,
    owner: task.owner,
    project_id: task.project_id || null,
    collaborators: (task.collaborators || []).filter(id => id !== task.owner),
    attachments: task.attachments || []
  }
  
  // Load comments for this task
  loadComments(task.id)
  showModal.value = true
}

async function loadComments(taskId) {
  comments.value = []
  try {
    const res = await axios.get(`http://localhost:5002/task/${taskId}/comments`, { withCredentials: true })
    comments.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    comments.value = []
  }
}

// Helper functions for modal
function formatDate(date) {
  return toLocal(date) || '-'
}

// Consolidated date formatting utilities
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

// Consolidated employee name resolution
function getEmployeeName(employeeId) {
  if (!employeeId) return 'Unassigned'
  
  // Check in available employees first
  const emp = availableEmployees.value.find(e => e.employee_id === employeeId)
  if (emp) return emp.employee_name
  
  // Check in department employees
  const deptEmp = departmentEmployees.value.find(e => e.employee_id === employeeId)
  if (deptEmp) return deptEmp.employee_name
  
  // Check if it's the current user
  if (employeeId === currentEmployeeId) return currentEmployeeName
  
  return `#${employeeId}`
}

function getOwnerName(ownerId) {
  return getEmployeeName(ownerId)
}

function getCollaboratorNames(collaboratorIds) {
  if (!Array.isArray(collaboratorIds) || collaboratorIds.length === 0) return ''
  
  const names = collaboratorIds.map(id => getEmployeeName(id)).filter(Boolean)
  return names.join(', ')
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

async function loadTimeline() {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch all tasks
    const res = await axios.get('http://localhost:5002/tasks', {
      withCredentials: true
    })
    
    // Helper function to transform task data
    const transformTask = (t) => {
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
        project_id: t.project_id,
        subtasks: Array.isArray(t.subtasks) ? t.subtasks.map(transformTask) : []
      }
    }
    
    let allTasks = []
    if (res.data.my_tasks && res.data.team_tasks) {
      const myTasks = (res.data.my_tasks || []).map(transformTask)
      const teamTasks = []
      
      for (const [employeeName, employeeTasks] of Object.entries(res.data.team_tasks || {})) {
        teamTasks.push(...(employeeTasks || []).map(transformTask))
      }
      
      allTasks = [...myTasks, ...teamTasks]
    } else if (res.data.my_tasks && res.data.company_tasks) {
      const myTasks = (res.data.my_tasks || []).map(transformTask)
      const companyTasks = []
      
      for (const [deptName, deptData] of Object.entries(res.data.company_tasks || {})) {
        for (const [teamName, teamData] of Object.entries(deptData || {})) {
          for (const [employeeName, employeeTasks] of Object.entries(teamData || {})) {
            companyTasks.push(...(employeeTasks || []).map(transformTask))
          }
        }
      }
      allTasks = [...myTasks, ...companyTasks]
    }
    const uniqueTasks = []
    const seenTaskIds = new Set()
    
    for (const task of allTasks) {
      if (!seenTaskIds.has(task.id)) {
        seenTaskIds.add(task.id)
        uniqueTasks.push(task)
      }
    }
    
    // Store all tasks for filtering based on current tab
    timelineData.value = uniqueTasks
    
    // Load employee data for team and department tabs
    await loadEmployeeData()
    
    // Load departments for senior managers and HR
    if (isSeniorManagerOrHR.value) {
      await fetchDepartments()
    }
    
    if (!startDate.value || !endDate.value) {
      const dates = uniqueTasks.map(task => new Date(task.created_at.replace(/:\d{2}[.Z].*$/, '')))
      const dueDates = uniqueTasks.map(task => new Date(task.due_date.replace(/:\d{2}[.Z].*$/, '')))
      const allDates = [...dates, ...dueDates]
      
      if (allDates.length > 0) {
        const minDate = new Date(Math.min(...allDates))
        const maxDate = new Date(Math.max(...allDates))
        
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

async function loadEmployeeData() {
  try {
    const role = (currentRole || '').toLowerCase()
    
    if (role === 'senior manager' || role === 'hr' || role === 'director') {
      // Senior managers, HR, and directors can see all employees
      const res = await axios.get('http://localhost:5000/employees/all', { withCredentials: true })
      availableEmployees.value = Array.isArray(res.data) ? res.data : []
      departmentEmployees.value = []
    } else {
      // For managers and staff, fetch team members from their department/team
      const depRaw = sessionStorage.getItem("department") || ""
      const teamRaw = sessionStorage.getItem("team") || ""
      const res = await axios.get(`http://localhost:5000/employees/department/${encodeURIComponent(depRaw)}/team/${encodeURIComponent(teamRaw)}`, { withCredentials: true })
      availableEmployees.value = Array.isArray(res.data) ? res.data : []
      
      // For department view, load all employees if user has access
      if (isSeniorManagerOrHR.value) {
        const deptRes = await axios.get('http://localhost:5000/employees/all', { withCredentials: true })
        departmentEmployees.value = Array.isArray(deptRes.data) ? deptRes.data : []
      }
    }
  } catch (err) {
    console.error('Error loading employee data:', err)
    availableEmployees.value = []
    departmentEmployees.value = []
  }
}

async function fetchDepartments() {
  try {
    const res = await axios.get('http://localhost:5000/departments', { withCredentials: true })
    departments.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Error fetching departments:', err)
    departments.value = []
  }
}

async function fetchDepartmentEmployees(department) {
  try {
    const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(department)}`, { withCredentials: true })
    departmentEmployees.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Error fetching department employees:', err)
    departmentEmployees.value = []
  }
}

function selectDepartment(department) {
  selectedDepartment.value = department
  departmentSelectedEmployeeId.value = null
  fetchDepartmentEmployees(department)
}

function selectDepartmentEmployee(employeeId) {
  departmentSelectedEmployeeId.value = employeeId
}

function goBack() {
  router.push({ name: 'tasks' })
}

// Watch for tab changes to reload timeline
watch(currentTab, () => {
  if (currentTab.value === 'my') {
    loadTimeline()
  }
})

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

/* Tabs styling - matching TasksView */
.tabs { 
  display: flex; 
  gap: 0.5rem; 
  margin-bottom: 1rem; 
  flex-wrap: wrap;
}

.tab { 
  border: 1px solid #e5e7eb; 
  background: #fff; 
  color: #111827; 
  padding: 0.4rem 0.9rem; 
  border-radius: 999px; 
  cursor: pointer; 
  font-weight: 600; 
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab.active { 
  background: #111827; 
  color: #fff; 
}

.tab:hover:not(.active) {
  background: #f9fafb;
  border-color: #d1d5db;
}

/* Employee selection styling - matching TasksView */
.team-search-section {
  margin-bottom: 1.5rem;
  margin-top: 1.5rem;
}

.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
}

.input-field:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.employee-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.8rem;
  margin-top: 1.5rem;
}

.employee-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.6rem 0.8rem;
  border-radius: 12px;
  background: #ededee;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
}

.employee-card:hover {
  background: #e1e5f3;
  transform: translateY(-2px);
}

.employee-card.selected {
  background: #5ea866;
  color: white;
}

.employee-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #bfd6cc;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.4rem;
}

.employee-card.selected .employee-avatar {
  background: white;
  color: #5ea866;
}

.employee-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.employee-role {
  font-size: 0.8rem;
  color: #6b7280;
}

.employee-department {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 2px;
}

/* Department Section Styling - matching TasksView */
.department-section {
  margin-bottom: 3rem;
  margin-top: 0.5rem;
  margin-left: 2rem;
  margin-right: 2rem;
}

.department-selection {
  margin-bottom: 2rem;
}

.department-selection h3 {
  margin-bottom: 1.5rem;
  font-size: 1.3rem;
  color: #333;
  font-weight: 600;
}

.department-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.5rem;
}

.department-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  border-radius: 12px;
  background: #f8f9fa;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.department-card:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.department-card.selected {
  background: #007bff;
  color: white;
  border-color: #0056b3;
}

.department-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #dee2e6;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.department-card.selected .department-icon {
  background: white;
  color: #007bff;
}

.department-name {
  font-weight: 600;
  font-size: 1rem;
}

.employee-selection {
  margin-top: 3rem;
}

.employee-selection h3 {
  margin-bottom: 1.5rem;
  font-size: 1.3rem;
  color: #686c84;
  font-weight: 600;
  border-top: 3px solid #d1d4e0;
  padding-top: 1.5rem;
}

/* Modal Styling - matching TasksView */
.modal-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  min-height: 400px;
  width: 100%;
}

.form-section {
  background: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 1.5rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #f3f4f6;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-row-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
  margin-bottom: 0.25rem;
}

.form-display {
  font-size: 0.95rem;
  color: #374151;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  min-height: 2.5rem;
  display: flex;
  align-items: center;
  word-wrap: break-word;
}

.status-display {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
  color: #fff;
  width: fit-content;
}

.priority-display {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  width: fit-content;
}

.status-ongoing {
  background-color: #3b82f6;
}

.status-review {
  background-color: #f59e0b;
}

.status-completed {
  background-color: #10b981;
}

.status-unassigned {
  background-color: #6b7280;
}

.status-default {
  background-color: #9ca3af;
}

.priority-high {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.priority-medium {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fed7aa;
}

.priority-low {
  background: #f0fdf4;
  color: #059669;
  border: 1px solid #bbf7d0;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
}

.comment-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-meta {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.comment-text {
  font-size: 0.95rem;
  color: #374151;
  white-space: pre-wrap;
  line-height: 1.5;
  word-wrap: break-word;
}

.no-comments {
  text-align: center;
  color: #9ca3af;
  font-style: italic;
  padding: 2rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
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
  top: 0;left: 0;right: 0;bottom: 0;
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
  background-image: repeating-linear-gradient(to right, transparent 0px, transparent 99px,#f3f4f6 100px
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

@media (max-width: 768px) {
  .tasks-timeline-page {
    padding: 16px;
  }
  
  .tabs {
    gap: 0.25rem; margin-bottom: 1.5rem; justify-content: center;
  }
  
  .tab {
    padding: 0.5rem 0.75rem; font-size: 0.9rem; flex: 1; text-align: center; min-width: 0;
  }
  
  .employee-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 0.5rem; margin-top: 1rem;
  }
  
  .employee-card {
    padding: 0.5rem 0.4rem;
  }
  
  .employee-name {
    font-size: 0.85rem;
  }
  
  .employee-role {
    font-size: 0.75rem;
  }
  
  .employee-department {
    font-size: 0.7rem;
  }
  
  .department-section {
    margin-left: 1rem; margin-right: 1rem;
  }
  
  .department-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem;
  }
  
  .department-card {
    padding: 0.75rem;
  }
  
  .department-icon {
    width: 40px; height: 40px;
  }
  
  .department-name {
    font-size: 0.9rem;
  }
  
  .timeline-controls {
    flex-direction: column; align-items: stretch; gap: 12px;
  }
  
  .date-range {
    justify-content: center;
  }
  
  .timeline-legend {
    justify-content: center;
  }
  
  .legend-items {
    justify-content: center; gap: 12px;
  }
  
  .legend-item {
    font-size: 11px;
  }
  
  .timeline-grid {
    max-height: 60vh; border: 12px solid #e5e7eb;
  }
  
  .employee-column {
    min-width: 150px;
  }
  
  .date-column {
    min-width: 80px;
  }
  
  .task-meta {
    font-size: 9px;
  }
  
  .form-row-3 {
    grid-template-columns: 1fr; gap: 0.75rem;
  }
  
  .form-section {
    padding: 1rem; border-radius: 8px;
  }
  
  .section-title {
    font-size: 1.1rem; margin-bottom: 1rem;
  }
  
  .form-row {
    gap: 0.75rem; margin-bottom: 1rem;
  }
  
  .form-input {
    padding: 0.625rem 0.875rem; font-size: 0.9rem;
  }
  
  .form-display {
    padding: 0.625rem 0.875rem; font-size: 0.9rem;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .tabs {
    gap: 0.375rem;
  }
  
  .tab {
    padding: 0.4rem 0.8rem; font-size: 0.95rem;
  }
  
  .employee-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem;
  }
}
</style>
