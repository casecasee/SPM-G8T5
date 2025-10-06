<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getProjects } from '../api/projects'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Calendar from 'primevue/calendar'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import MultiSelect from 'primevue/multiselect'
import axios from 'axios'

// ----------------- State -----------------
const tasks = ref([])
const projects = ref([])
const currentTab = ref('my')
const teamSearch = ref('')
const teamSelectedEmployeeId = ref(null)
const selectedTask = ref(null)
const showModal = ref(false)
const isEditing = ref(false)
const availableEmployees = ref([])
const fileUploadRef = ref(null)

// Department view state
const departments = ref([])
const selectedDepartment = ref(null)
const departmentEmployees = ref([])
const departmentSearch = ref('')
const departmentSelectedEmployeeId = ref(null) 

// Logged-in user info
const currentEmployeeId = Number(sessionStorage.getItem("employee_id"))
const currentRole = sessionStorage.getItem("role")
const currentEmployeeName = sessionStorage.getItem("employee_name")
const currentDep = sessionStorage.getItem("department")
const currentTeam = sessionStorage.getItem("team")

const statusOptions = [
  { label: 'Ongoing', value: 'ongoing' },
  { label: 'Under Review', value: 'under review' },
  { label: 'Done', value: 'done' }
]

const priorityOptions = [
  { label: '1 - Lowest', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 },
  { label: '4', value: 4 },
  { label: '5 - Medium', value: 5 },
  { label: '6', value: 6 },
  { label: '7', value: 7 },
  { label: '8', value: 8 },
  { label: '9', value: 9 },
  { label: '10 - Highest', value: 10 }
]

const taskForm = ref(resetForm())
const openStatusFor = ref(null)

// Subtasks state
const subtasks = ref([])
const newSubtask = ref({
  name: '',
  description: '',
  due_date: null,
  status: 'ongoing',
  priority: 5,
  owner: currentEmployeeId,
  collaborators: [],
  attachments: []
})
const showSubtaskForm = ref(false)
const subtaskFileUploadRef = ref(null)

function resetForm() {
  const defaultStatus = currentRole === 'staff' ? 'ongoing' : 'unassigned'
  
  return {
    id: null,
    name: '',
    description: '',
    due_date: null,
    status: defaultStatus,
    priority: 5, 
    owner: currentEmployeeId, 
    collaborators: [], 
    project_id: null,
    attachments: []
  }
}

function resetSubtaskForm() {
  return {
    name: '',
    description: '',
    due_date: null,
    status: 'ongoing',
    priority: 5,
    owner: currentEmployeeId,
    collaborators: [],
    project_id: null,
    attachments: []
  }
}

function addSubtask() {
  if (!newSubtask.value.name.trim()) return
  
  subtasks.value.push({
    id: Date.now(), // Temporary ID for new subtasks
    ...newSubtask.value
  })
  
  newSubtask.value = resetSubtaskForm()
  showSubtaskForm.value = false
}

function toggleSubtaskForm() {
  showSubtaskForm.value = !showSubtaskForm.value
  if (!showSubtaskForm.value) {
    newSubtask.value = resetSubtaskForm()
  }
}

function handleSubtaskAttachment(event) {
  const newFiles = event.files.map(file => ({ 
    name: file.name, 
    file: file,
    url: null
  }))
  newSubtask.value.attachments.push(...newFiles)
  
  if (subtaskFileUploadRef.value && typeof subtaskFileUploadRef.value.clear === 'function') {
    subtaskFileUploadRef.value.clear()
  }
}

function removeSubtaskAttachment(index) {
  newSubtask.value.attachments.splice(index, 1)
}

function updateSubtaskStatus(subtask, newStatus) {
  subtask.status = newStatus
}

function canEdit(task) {
  if (!task) return true 
  
  if (currentTab.value === 'departments' && task.owner !== currentEmployeeId) {
    return false
  }
  
  if (currentTab.value === 'team' && task.owner !== currentEmployeeId) {
    return false
  }
  
  if (isManagerRole.value) return true
  return isOwner(task)
}

function canAssignTasks() {
  return isManagerRole.value
}

const isManagerRole = computed(() => (currentRole || '').toLowerCase() !== 'staff')
const isSeniorManagerOrHR = computed(() => {
  const role = (currentRole || '').toLowerCase()
  return role === 'senior manager' || role === 'hr'
})

const myTasks = computed(() => {
  const collabIncludes = (task) => Array.isArray(task.collaborators) && task.collaborators.includes(currentEmployeeId)
  return (tasks.value || []).filter(task => task.owner === currentEmployeeId || collabIncludes(task))
})

const displayTasks = computed(() => {
  let filteredTasks = []
  
  if (currentTab.value === 'team') {
    if (!teamSelectedEmployeeId.value) return []
    const targetId = Number(teamSelectedEmployeeId.value)
    if (targetId === currentEmployeeId) return []
    filteredTasks = (tasks.value || []).filter(t => t.owner === targetId || (Array.isArray(t.collaborators) && t.collaborators.includes(targetId)))
  } else if (currentTab.value === 'departments') {
    if (!departmentSelectedEmployeeId.value) return []
    const targetId = Number(departmentSelectedEmployeeId.value)
    if (targetId === currentEmployeeId) return []
    filteredTasks = (tasks.value || []).filter(t => t.owner === targetId || (Array.isArray(t.collaborators) && t.collaborators.includes(targetId)))
  } else {
    filteredTasks = myTasks.value
  }
  
  return filteredTasks.sort((a, b) => {
    const priorityA = a.priority || 5
    const priorityB = b.priority || 5
    return priorityB - priorityA
  })
})

const tasksByPriority = computed(() => {
  const tasks = displayTasks.value
  const groups = {
    high: [],
    medium: [],
    low: []
  }
  
  tasks.forEach(task => {
    const priority = task.priority || 5
    if (priority >= 8) {
      groups.high.push(task)
    } else if (priority >= 5) {
      groups.medium.push(task)
    } else {
      groups.low.push(task)
    }
  })
  
  return groups
})

const shouldShowNoTasksMessage = computed(() => {
  if (displayTasks.value.length > 0) return false
  
  if (currentTab.value === 'my') return true
  
  if (currentTab.value === 'team') {
    return teamSelectedEmployeeId.value !== null
  }
  
  if (currentTab.value === 'departments') {
    return selectedDepartment.value !== null && departmentSelectedEmployeeId.value !== null
  }
  
  return false
})

// Subtask progress tracking
const subtaskProgress = computed(() => {
  if (subtasks.value.length === 0) return { completed: 0, total: 0, percentage: 0 }
  
  const completed = subtasks.value.filter(subtask => subtask.status === 'done').length
  const total = subtasks.value.length
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0
  
  return { completed, total, percentage }
})

const filteredEmployeesForTeam = computed(() => {
  const q = (teamSearch.value || '').trim().toLowerCase()
  const list = (Array.isArray(availableEmployees.value) ? availableEmployees.value : [])
    .filter(e => e.employee_id !== currentEmployeeId)
  if (q.length < 2) return []
  return list.filter(e => (e.employee_name || '').toLowerCase().startsWith(q))
})

const filteredEmployeesForDepartment = computed(() => {
  const q = (departmentSearch.value || '').trim().toLowerCase()
  const list = (Array.isArray(departmentEmployees.value) ? departmentEmployees.value : [])
    .filter(e => e.employee_id !== currentEmployeeId)
  if (q.length < 2) return []
  return list.filter(e => (e.employee_name || '').toLowerCase().startsWith(q))
})

// ----------------- Functions -----------------
async function fetchDepartments() {
  try {
    const res = await axios.get("http://localhost:5000/departments", { withCredentials: true })
    departments.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error("Error fetching departments:", err)
    departments.value = []
  }
}

async function fetchDepartmentEmployees(department) {
  try {
    const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(department)}`, { withCredentials: true })
    departmentEmployees.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error("Error fetching department employees:", err)
    departmentEmployees.value = []
  }
}

async function fetchEmployees() {
  try {
    let list = []
    if (currentRole === 'staff') {
      const depRaw = sessionStorage.getItem("department") || ""
      const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(depRaw)}`, { withCredentials: true })
      const byDept = Array.isArray(res.data) ? res.data : []
      list = byDept.filter(e => (e.role || '').toLowerCase() === 'staff')
    } else if (isManagerRole.value) {
      const dep = sessionStorage.getItem("department") || ""
      const team = sessionStorage.getItem("team") || ""
      const res = await axios.get(
        `http://localhost:5000/employees/department/${encodeURIComponent(dep)}/team/${encodeURIComponent(team)}`,
        { withCredentials: true }
      )
      list = Array.isArray(res.data) ? res.data : []
    } else {
      const res = await axios.get("http://localhost:5000/employees/all", { withCredentials: true })
      list = Array.isArray(res.data) ? res.data : []
    }
    availableEmployees.value = list
  } catch (err) {
    console.error("Error fetching employees:", err)
    availableEmployees.value = []
  }
}

async function fetchTasks() {
  try {
    const res = await axios.get("http://localhost:5002/tasks", {
      withCredentials: true,
      params: {
        eid: currentEmployeeId,
        role: currentRole
      }
    })
    const fetchedTasks = res.data.tasks.map(t => {
      // Parse attachments from JSON string
      let attachments = []
      if (t.attachment) {
        try {
          const parsed = JSON.parse(t.attachment)
          attachments = Array.isArray(parsed) ? parsed.map(filename => ({
            name: filename.split(/[/\\]/).pop() || "File",
            url: `http://localhost:5002/attachments/${filename}`
          })) : []
        } catch (e) {
          // If it's not JSON, handle old single file format
          attachments = [{
            name: t.attachment.split(/[/\\]/).pop() || "File",
            url: `http://localhost:5002/attachments/${t.attachment}`
          }]
        }
      }
      
      return {
        id: t.task_id,
        name: t.title,
        description: t.description,
        due_date: t.deadline,
        status: t.status,
        priority: t.priority || 5,
        owner: t.owner,
        project_id: t.project_id,
        collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(id => Number(id)) : [],
        attachments: attachments
      }
    })

    if (currentRole === 'staff') {
      tasks.value = fetchedTasks.filter(task => {
        const collabIds = Array.isArray(task.collaborators) ? task.collaborators : []
        return task.owner === currentEmployeeId || collabIds.includes(currentEmployeeId)
      })
    } else {
      tasks.value = fetchedTasks
    }
    if (!availableEmployees.value || availableEmployees.value.length === 0) {
      try { await fetchEmployees() } catch (_) {}
    }
  } catch (err) {
    console.error("Error fetching tasks:", err)
  }
}

async function saveTask() {
  try {
    let uploadedAttachments = []

    // Upload all new files
    for (const attachment of taskForm.value.attachments) {
      if (attachment.file) {
        // New file to upload
        const formData = new FormData()
        formData.append('attachment', attachment.file)

        const uploadRes = await axios.post('http://localhost:5002/upload-attachment', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          withCredentials: true
        })
        
        uploadedAttachments.push(uploadRes.data.file_path)
      } else if (attachment.url) {
        // Existing file - extract filename from URL
        const urlParts = attachment.url.split('/')
        uploadedAttachments.push(urlParts[urlParts.length - 1])
      }
    }

    const payload = {
      title: taskForm.value.name,
      description: taskForm.value.description,
      attachments: uploadedAttachments,  // Array of filenames
      deadline: taskForm.value.due_date
        ? new Date(taskForm.value.due_date).toISOString()
        : new Date().toISOString(),
      status: taskForm.value.status,
      priority: taskForm.value.priority,
      parent_id: null,
      employee_id: currentEmployeeId,
      owner: taskForm.value.owner,
      project_id: taskForm.value.project_id,
      collaborators: (() => {
        const selected = Array.isArray(taskForm.value.collaborators) ? taskForm.value.collaborators : []
        if (currentRole === 'staff') {
          const allowedIds = (availableEmployees.value || []).map(e => e.employee_id)
          return selected.filter(id => allowedIds.includes(id))
        }
        return selected
      })(),
      role: currentRole
    }

    if (taskForm.value.id) {
      await axios.put(`http://localhost:5002/task/${taskForm.value.id}`, payload, { withCredentials: true })
    } else {
      await axios.post("http://localhost:5002/tasks", payload, { withCredentials: true })
    }

    await fetchTasks()

    if (taskForm.value.id) {
      selectedTask.value = tasks.value.find(t => t.id === taskForm.value.id)
    }

    showModal.value = false
    taskForm.value = resetForm()
    isEditing.value = false
  } catch (err) {
    console.error("Error saving task:", err)
    alert('Error saving task. Please check the console for details.')
  }
}

function isStaff() { return currentRole === 'staff' }
function isOwner(task) { 
  return !!task && task.owner === currentEmployeeId 
}
function isCollaborator(task) {
  if (!task) return false
  const collabIds = Array.isArray(task.collaborators) ? task.collaborators : []
  return collabIds.includes(currentEmployeeId)
}
function isCollaboratorOnly(task) {
  return isStaff() && isCollaborator(task) && !isOwner(task)
}

function isOwnerOrCollaborator(task) {
  return isOwner(task) || isCollaborator(task)
}

async function updateTaskStatus(task, newStatus) {
  try {
    await axios.patch(`http://localhost:5002/task/status/${task.id}`, { status: newStatus, employee_id: currentEmployeeId }, { withCredentials: true })
    task.status = newStatus
    if (openStatusFor.value === task.id) openStatusFor.value = null
  } catch (err) {
    console.error("Error updating status:", err)
  }
}

function toggleStatusMenu(task) {
  openStatusFor.value = openStatusFor.value === task.id ? null : task.id
}

function findEmployeeNameById(id) {
  const emp = (availableEmployees.value || []).find(e => e.employee_id === id)
  return emp ? emp.employee_name : ''
}
function getOwnerName(ownerId) {
  if (!ownerId) return currentEmployeeName || ''
  const name = findEmployeeNameById(ownerId)
  return name || (ownerId === currentEmployeeId ? currentEmployeeName : '')
}

// -------- Project helpers for task details --------
function getProjectLabelById(id) {
  if (!id) return '-'
  const p = (projects.value || []).find(p => p.id === id)
  return p ? `${p.name} (#${p.id})` : `#${id}`
}

const projectOptions = computed(() => {
  const opts = [{ label: 'None', value: null }]
  for (const p of (projects.value || [])) {
    opts.push({ label: `${p.name} (#${p.id})`, value: p.id })
  }
  return opts
})

function getCollaboratorNames(collaboratorIds) {
  if (!Array.isArray(collaboratorIds) || collaboratorIds.length === 0) return ''
  const names = collaboratorIds
    .map(id => findEmployeeNameById(id))
    .filter(Boolean)
  return names.join(', ')
}

async function openAdd() {
  isEditing.value = true
  selectedTask.value = null
  taskForm.value = resetForm()
  await fetchEmployees()
  showModal.value = true
}

function openDetails(task) {
  selectedTask.value = task
  isEditing.value = false
  taskForm.value = {
    id: task.id,
    name: task.name,
    description: task.description,
    due_date: task.due_date,
    status: task.status,
    priority: task.priority || 5,
    owner: task.owner,
    project_id: task.project_id || null,
    collaborators: (task.collaborators || []).filter(id => id !== task.owner),
    attachments: task.attachments || []
  }
  // Initialize subtasks (you can fetch from API later)
  subtasks.value = task.subtasks || []
  showModal.value = true
}

async function startEditing() {
  isEditing.value = true
  await fetchEmployees()
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function handleAttachment(event) {
  const newFiles = event.files.map(file => ({ 
    name: file.name, 
    file: file,
    url: null
  }))
  taskForm.value.attachments.push(...newFiles)
  
  if (fileUploadRef.value && typeof fileUploadRef.value.clear === 'function') {
    fileUploadRef.value.clear()
  }
}

function removeAttachment(index) {
  taskForm.value.attachments.splice(index, 1)
}

function getStatusClass(status) {
  switch (status) {
    case 'ongoing': return 'status-pill status-ongoing'
    case 'under review': return 'status-pill status-review'
    case 'done': return 'status-pill status-completed'
    default: return 'status-pill status-default'
  }
}

function getPriorityClass(priority) {
  if (priority >= 8) return 'priority-high'
  if (priority >= 5) return 'priority-medium'
  return 'priority-low'
}

async function selectDepartment(department) {
  selectedDepartment.value = department
  departmentSelectedEmployeeId.value = null
  await fetchDepartmentEmployees(department)
}

function selectDepartmentEmployee(employeeId) {
  departmentSelectedEmployeeId.value = employeeId
}

const refreshIntervalMs = 30000
let refreshTimer = null

onMounted(() => {
  fetchEmployees().finally(() => fetchTasks())
  getProjects().then(list => { projects.value = Array.isArray(list) ? list : [] }).catch(() => { projects.value = [] })
  
  if (isSeniorManagerOrHR.value) {
    fetchDepartments()
  }
  
  refreshTimer = setInterval(fetchTasks, refreshIntervalMs)
  window.addEventListener('focus', fetchTasks)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  window.removeEventListener('focus', fetchTasks)
})
</script>

<template>
<div class="tasks-page">
  <div class="tasks-header">
    <h2>Tasks</h2>
    <div class="header-buttons" v-if="currentTab === 'my'">
      <Button icon="pi pi-filter" label="Filter" class="filter-btn" text />
      <Button label="+ Add Task" class="add-top-btn" @click="openAdd" />
    </div>
  </div>

  <!-- Tabs visible to managers; staff always see 'My' implicitly -->
  <div class="tabs" v-if="isManagerRole">
    <button :class="['tab', currentTab==='my' ? 'active' : '']" @click="currentTab='my'">My Tasks</button>
    <button :class="['tab', currentTab==='team' ? 'active' : '']" @click="currentTab='team'" v-if="!isSeniorManagerOrHR">Team's Tasks</button>
    <button :class="['tab', currentTab==='departments' ? 'active' : '']" @click="currentTab='departments'" v-if="isSeniorManagerOrHR">All Departments</button>
  </div>

  <!-- Team search bar -->
    <div v-if="isManagerRole && currentTab==='team'" class="team-search-section">
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
        </div>
      </div>
    </div>
  </div>

  <div class="tasks-container">
    <!-- High Priority Tasks -->
    <div v-if="tasksByPriority.high.length > 0" class="priority-section">
      <div class="priority-header high-priority">
        <i class="pi pi-exclamation-triangle"></i>
        <span>High Priority</span>
        <span class="task-count">{{ tasksByPriority.high.length }}</span>
      </div>
      <div class="tasks-grid">
        <Card v-for="task in tasksByPriority.high" :key="task.id" class="task-card" @click="openDetails(task)">
          <template #title>
            <div class="task-title-row">
              <span>{{ task.name }}</span>
            </div>
          </template>
          <template #content>
            <p class="desc">{{ task.description }}</p>
            <p class="meta">📅 {{ formatDate(task.due_date) }}</p>
            <span
              v-if="isOwnerOrCollaborator(task)"
              class="status-pill status-clickable"
              :class="getStatusClass(task.status)"
              @click.stop="toggleStatusMenu(task)"
              title="Change status"
            >
              {{ task.status }}
            </span>
            <p v-else class="status" :class="getStatusClass(task.status)">
              {{ task.status }}
            </p>
            <div v-if="openStatusFor === task.id" class="status-menu-inline" @click.stop>
              <span
                v-for="opt in statusOptions"
                :key="opt.value"
                class="status-pill status-option"
                :class="getStatusClass(opt.value) + (task.status===opt.value ? ' status-selected' : '')"
                @click.stop="updateTaskStatus(task, opt.value)"
              >{{ opt.label }}</span>
            </div>
            <p class="meta">Owner: <b>{{ getOwnerName(task.owner) || currentEmployeeName }}</b></p>
            <p class="meta">Collaborators: <b>{{ getCollaboratorNames(task.collaborators) }}</b></p>
          </template>
        </Card>
      </div>
    </div>

    <!-- Medium Priority Tasks -->
    <div v-if="tasksByPriority.medium.length > 0" class="priority-section">
      <div class="priority-header medium-priority">
        <i class="pi pi-clock"></i>
        <span>Medium Priority</span>
        <span class="task-count">{{ tasksByPriority.medium.length }}</span>
      </div>
      <div class="tasks-grid">
        <Card v-for="task in tasksByPriority.medium" :key="task.id" class="task-card" @click="openDetails(task)">
          <template #title>
            <div class="task-title-row">
              <span>{{ task.name }}</span>
            </div>
          </template>
          <template #content>
            <p class="desc">{{ task.description }}</p>
            <p class="meta">📅 {{ formatDate(task.due_date) }}</p>
            <span
              v-if="isOwnerOrCollaborator(task)"
              class="status-pill status-clickable"
              :class="getStatusClass(task.status)"
              @click.stop="toggleStatusMenu(task)"
              title="Change status"
            >
              {{ task.status }}
            </span>
            <p v-else class="status" :class="getStatusClass(task.status)">
              {{ task.status }}
            </p>
            <div v-if="openStatusFor === task.id" class="status-menu-inline" @click.stop>
              <span
                v-for="opt in statusOptions"
                :key="opt.value"
                class="status-pill status-option"
                :class="getStatusClass(opt.value) + (task.status===opt.value ? ' status-selected' : '')"
                @click.stop="updateTaskStatus(task, opt.value)"
              >{{ opt.label }}</span>
            </div>
            <p class="meta">Owner: <b>{{ getOwnerName(task.owner) || currentEmployeeName }}</b></p>
            <p class="meta">Collaborators: <b>{{ getCollaboratorNames(task.collaborators) }}</b></p>
          </template>
        </Card>
      </div>
    </div>

    <!-- Low Priority Tasks -->
    <div v-if="tasksByPriority.low.length > 0" class="priority-section">
      <div class="priority-header low-priority">
        <i class="pi pi-check-circle"></i>
        <span>Low Priority</span>
        <span class="task-count">{{ tasksByPriority.low.length }}</span>
      </div>
      <div class="tasks-grid">
        <Card v-for="task in tasksByPriority.low" :key="task.id" class="task-card" @click="openDetails(task)">
          <template #title>
            <div class="task-title-row">
              <span>{{ task.name }}</span>
            </div>
          </template>
          <template #content>
            <p class="desc">{{ task.description }}</p>
            <p class="meta">📅 {{ formatDate(task.due_date) }}</p>
            <span
              v-if="isOwnerOrCollaborator(task)"
              class="status-pill status-clickable"
              :class="getStatusClass(task.status)"
              @click.stop="toggleStatusMenu(task)"
              title="Change status"
            >
              {{ task.status }}
            </span>
            <p v-else class="status" :class="getStatusClass(task.status)">
              {{ task.status }}
            </p>
            <div v-if="openStatusFor === task.id" class="status-menu-inline" @click.stop>
              <span
                v-for="opt in statusOptions"
                :key="opt.value"
                class="status-pill status-option"
                :class="getStatusClass(opt.value) + (task.status===opt.value ? ' status-selected' : '')"
                @click.stop="updateTaskStatus(task, opt.value)"
              >{{ opt.label }}</span>
            </div>
            <p class="meta">Owner: <b>{{ getOwnerName(task.owner) || currentEmployeeName }}</b></p>
            <p class="meta">Collaborators: <b>{{ getCollaboratorNames(task.collaborators) }}</b></p>
          </template>
        </Card>
      </div>
    </div>

    <!-- No tasks message -->
    <div v-if="shouldShowNoTasksMessage" class="no-tasks">
      <i class="pi pi-inbox"></i>
      <p>No tasks found</p>
    </div>
  </div>

  <Dialog v-model:visible="showModal" modal 
        :header="isEditing && !selectedTask ? 'New Task' : (isEditing ? 'Edit Task' : 'Task Details')" 
        class="page-style-modal">
    <div class="modal-content">
      <div class="field-row">
        <label>Name:</label>
        <template v-if="isEditing || !selectedTask">
          <InputText v-model="taskForm.name" class="input-field" :disabled="!canEdit(selectedTask)" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.name }}</span>
        </template>
      </div>

      <div class="field-row">
        <label>Description:</label>
        <template v-if="isEditing || !selectedTask">
          <Textarea v-model="taskForm.description" rows="4" class="input-field" maxlength="100" :disabled="!canEdit(selectedTask)" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.description }}</span>
        </template>
      </div>

      <div class="field-row grid-3">
        <div>
          <label>Due Date:</label>
          <template v-if="isEditing || !selectedTask">
            <Calendar v-model="taskForm.due_date" class="input-field" :minDate="new Date()" :disabled="!canEdit(selectedTask)" />
          </template>
          <template v-else>
            <span class="text-field">{{ formatDate(taskForm.due_date) }}</span>
          </template>
        </div>
        <div>
          <label>Status:</label>
          <template v-if="isEditing && selectedTask && !isStaff()">
            <Dropdown v-model="taskForm.status" :options="statusOptions" optionLabel="label" optionValue="value" class="input-field w-full" />
          </template>
          <template v-else>
            <span class="text-field">{{ taskForm.status }}</span>
          </template>
        </div>
        <div>
          <label>Priority:</label>
          <template v-if="isEditing || !selectedTask">
            <Dropdown v-model="taskForm.priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="input-field w-full" :disabled="!canEdit(selectedTask)" />
          </template>
          <template v-else>
            <span class="text-field">{{ taskForm.priority }}</span>
          </template>
        </div>
      </div>

      <div class="field-row">
        <label>Project:</label>
        <template v-if="isEditing || !selectedTask">
          <Dropdown v-model="taskForm.project_id" :options="projectOptions" optionLabel="label" optionValue="value" class="input-field w-full" />
        </template>
        <template v-else>
          <span class="text-field">{{ getProjectLabelById(taskForm.project_id) }}</span>
        </template>
      </div>

      <div class="field-row" v-if="canAssignTasks() && isEditing">
        <label>Owner:</label>
        <Dropdown
          v-model="taskForm.owner"
          :options="availableEmployees"
          optionLabel="employee_name"
          optionValue="employee_id"
          placeholder="Select owner..."
          class="input-field w-full"
          :disabled="!canEdit(selectedTask)"
        />
      </div>

      <div class="field-row" v-else>
        <label>Owner:</label>
        <span class="text-field">{{ getOwnerName(taskForm.owner) || currentEmployeeName }}</span>
      </div>

      <div class="field-row">
        <label>Collaborators:</label>
        <template v-if="isEditing || !selectedTask">
          <MultiSelect
            v-model="taskForm.collaborators"
            :options="availableEmployees.filter(emp => emp.employee_id !== taskForm.owner)" 
            optionLabel="employee_name"
            optionValue="employee_id"
            class="input-field w-full"
            :disabled="!canEdit(selectedTask)"
            placeholder="Select collaborators..."
          />
        </template>
        <template v-else>
          <span class="text-field">{{ getCollaboratorNames(taskForm.collaborators) }}</span>
        </template>
      </div>

      <div class="field-row">
        <label>Attachments:</label>
        <template v-if="isEditing || !selectedTask">
        <FileUpload 
          ref="fileUploadRef"
          mode="basic" 
          accept=".pdf" 
          :multiple="true"
          chooseLabel="Upload" 
          :auto="false" 
          :customUpload="true" 
          @select="handleAttachment"
          :disabled="selectedTask && isCollaboratorOnly(selectedTask)" 
        />
          <ul class="file-list">
            <li v-for="(file, index) in taskForm.attachments" :key="index">
              <a :href="file.url" target="_blank">{{ file.name }}</a>
              <Button icon="pi pi-times" class="delete-btn" @click="removeAttachment(index)" v-if="isEditing || !selectedTask"/>
            </li>
          </ul>
        </template>
        <template v-else>
          <ul class="file-list">
            <li v-for="(file, index) in taskForm.attachments" :key="index">
              <a :href="file.url" target="_blank">{{ file.name }}</a>
            </li>
          </ul>
        </template>
      </div>

      <!-- Subtasks Section -->
      <div class="field-row subtasks-section">
        <div class="subtasks-header">
          <label>Subtasks:</label>
          <Button 
            v-if="isEditing || !selectedTask" 
            icon="pi pi-plus" 
            label="Add Subtask" 
            class="add-subtask-btn" 
            @click="toggleSubtaskForm"
            size="small"
          />
        </div>
        
        <!-- Progress Bar -->
        <div v-if="subtasks.length > 0" class="subtask-progress">
          <div class="progress-header">
            <span class="progress-title">Progress</span>
            <span class="progress-stats">{{ subtaskProgress.completed }}/{{ subtaskProgress.total }} completed</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: subtaskProgress.percentage + '%' }"
              ></div>
            </div>
            <span class="progress-percentage">{{ subtaskProgress.percentage }}%</span>
          </div>
        </div>
        
        <!-- Subtask Form -->
        <div v-if="showSubtaskForm && (isEditing || !selectedTask)" class="subtask-form">
          <div class="subtask-form-row">
            <InputText v-model="newSubtask.name" placeholder="Subtask name" class="input-field" />
            <div class="subtask-form-controls">
              <Button label="Add" @click="addSubtask" size="small" />
              <Button label="Cancel" @click="toggleSubtaskForm" severity="secondary" size="small" />
            </div>
          </div>
          <div class="subtask-form-row">
            <Textarea v-model="newSubtask.description" placeholder="Description" rows="2" class="input-field" />
          </div>
          <div class="subtask-form-row grid-3">
            <Calendar v-model="newSubtask.due_date" placeholder="Due date" class="input-field" />
            <Dropdown v-model="newSubtask.status" :options="statusOptions" optionLabel="label" optionValue="value" class="input-field" />
            <Dropdown v-model="newSubtask.priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="input-field" />
          </div>
          
          <!-- Owner Selection -->
          <div class="subtask-form-row">
            <label>Owner:</label>
            <Dropdown
              v-model="newSubtask.owner"
              :options="availableEmployees"
              optionLabel="employee_name"
              optionValue="employee_id"
              placeholder="Select owner..."
              class="input-field"
            />
          </div>
          
          <!-- Collaborators -->
          <div class="subtask-form-row">
            <label>Collaborators:</label>
            <MultiSelect
              v-model="newSubtask.collaborators"
              :options="availableEmployees.filter(emp => emp.employee_id !== newSubtask.owner)" 
              optionLabel="employee_name"
              optionValue="employee_id"
              class="input-field"
              placeholder="Select collaborators..."
            />
          </div>
          
          <!-- Attachments -->
          <div class="subtask-form-row">
            <label>Attachments:</label>
            <FileUpload 
              ref="subtaskFileUploadRef"
              mode="basic" 
              accept=".pdf" 
              :multiple="true"
              chooseLabel="Upload" 
              :auto="false" 
              :customUpload="true" 
              @select="handleSubtaskAttachment"
            />
            <ul class="file-list">
              <li v-for="(file, index) in newSubtask.attachments" :key="index">
                <span>{{ file.name }}</span>
                <Button icon="pi pi-times" class="delete-btn" @click="removeSubtaskAttachment(index)" size="small" text />
              </li>
            </ul>
          </div>
        </div>

        <!-- Subtasks List - Compact Design -->
        <div v-if="subtasks.length > 0" class="subtasks-list">
          <div v-for="(subtask, index) in subtasks" :key="subtask.id || index" class="subtask-item">
            <div class="subtask-content">
              <div class="subtask-header">
                <h4 class="subtask-title">{{ subtask.name }}</h4>
                <div class="subtask-meta">
                  <span 
                    class="status-pill status-clickable" 
                    :class="getStatusClass(subtask.status)"
                    @click="updateSubtaskStatus(subtask, subtask.status === 'done' ? 'ongoing' : 'done')"
                    title="Click to toggle status"
                  >
                    {{ subtask.status }}
                  </span>
                  <span class="priority-badge" :class="getPriorityClass(subtask.priority)">P{{ subtask.priority }}</span>
                </div>
              </div>
              <p v-if="subtask.description" class="subtask-description">{{ subtask.description }}</p>
              <div class="subtask-details">
                <span v-if="subtask.due_date" class="subtask-due">📅 {{ formatDate(subtask.due_date) }}</span>
                <span class="subtask-owner">👤 {{ getOwnerName(subtask.owner) }}</span>
                <span v-if="subtask.collaborators && subtask.collaborators.length > 0" class="subtask-collabs">
                  🤝 {{ getCollaboratorNames(subtask.collaborators) }}
                </span>
                <span v-if="subtask.attachments && subtask.attachments.length > 0" class="subtask-attachments">
                  📎 {{ subtask.attachments.length }} file(s)
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!showSubtaskForm" class="no-subtasks">
          <span>No subtasks yet</span>
        </div>
      </div>

      <div class="save-btn-container">
        <template v-if="selectedTask && !isEditing && canEdit(selectedTask)">
          <Button label="Edit" class="save-task-btn" @click="startEditing" />
        </template>
        <Button label="Save" class="save-task-btn" @click="saveTask" v-if="isEditing || !selectedTask" :disabled="!canEdit(selectedTask)"/>
      </div>

    </div>
  </Dialog>
</template>

<style scoped>
/* Header */
.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}
.tasks-header h2 { font-size: 2rem; margin: 0; }
.add-top-btn {
  border-radius: 50px;
  padding: 0.6rem 1.8rem;
  font-weight: bold;
}

/* Tabs */
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.tab { border: 1px solid #e5e7eb; background: #fff; color: #111827; padding: 0.4rem 0.9rem; border-radius: 999px; cursor: pointer; font-weight: 600; }
.tab.active { background: #111827; color: #fff; }

/* Team search */
.team-search-section {
  margin-bottom: 1.5rem;
  margin-top: 1.5rem;
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

/* Department Section */
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

/* Task Container */
.tasks-page { 
  padding: 2rem 3rem; 
  max-width: 1400px;
  margin: 0 auto;
}

.tasks-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.priority-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.priority-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
}

.high-priority {
  background: #fef2f2;
  color: #dc2626;
  border-left: 4px solid #dc2626;
}

.medium-priority {
  background: #fffbeb;
  color: #d97706;
  border-left: 4px solid #d97706;
}

.low-priority {
  background: #f0fdf4;
  color: #059669;
  border-left: 4px solid #059669;
}

.task-count {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.20rem 2rem;
  border-radius: 5px;
  font-size: 0.8rem;
  font-weight: 700;
}

.tasks-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}
.task-card {
  cursor: pointer;
  transition: transform 0.2s ease;
  word-wrap: break-word;     
  overflow-wrap: break-word; 
  white-space: normal;
  background: #fff;
  border-radius: 12px;
  padding: 0.5rem;
  margin: 0 1rem;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.task-card:hover { transform: translateY(-3px); }
.desc, .p-card-title {
  color: #555;
  font-size: 0.95rem;
  line-height: 1.4;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}
.meta, .status { font-size: 0.9rem; margin-top: 0.5rem; }

/* Modal Styling */
:deep(.page-style-modal .p-dialog) {
  width: 60vw !important;      
  max-width: 700px;           
  min-width: 700px;
  max-height: 85vh;           
  border-radius: 12px;
  font-family: 'Segoe UI', sans-serif;
  margin: 2rem auto !important; 
}

:deep(.page-style-modal .p-dialog-content) {
  min-height: 500px; 
  max-height: 70vh;
  padding: 1.5rem;
  box-sizing: border-box;
  overflow-y: auto;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  white-space: normal;
}

:deep(.p-dialog-mask) {
  padding: 1.5rem;
  box-sizing: border-box;
}

.header-buttons {
  display: flex;
  align-items: center;
  gap: 0.8rem; /* space between filter and add task */
}

/* Minimalistic Filter Button */
.filter-btn {
  border: 1px solid #3b82f6;
  background: none;
  color: #3b82f6;
  font-size: 0.95rem;
  padding: 0.6rem 1rem;
  border-radius: 50px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  background-color: #3b82f6;
  color: #fff;
}

.modal-content {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
  min-height: 500px;
  width: 100%;
}

/* Fields */
.field-row { display: flex; flex-direction: column; gap: 0.5rem; }
.field-row label { font-weight: 600; font-size: 1rem; color: #333; }
.input-field { border-radius: 8px; padding: 0.5rem 0.8rem; font-size: 0.95rem; border: 1px solid #ccc; }
.text-field {
  font-size: 0.95rem;
  color: #444;
  padding: 0.5rem 0.8rem;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
  max-width: 100%; 
  display: block;
  min-height: 2.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

:deep(.p-calendar){
  border: none !important;
  width: 100%;
}
:deep(.p-dropdown) {
  border: 1px solid #ccc !important;
  border-radius: 8px;  
  width: 100%;
}

:deep(.p-inputtext) {
  border-radius: 8px;
  padding: 0.5rem 0.8rem;
  font-size: 0.95rem;
}

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }

/* Buttons */
.save-btn-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}
.save-task-btn {
  border-radius: 50px;
  padding: 0.6rem 1.6rem;
  font-weight: 600;
}

.file-list {
  list-style: none;
  padding-left: 0;
  margin-top: 0.5rem;
}
.file-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}
.delete-btn {
  border: none;
  background: none;
  color: red;
  font-size: 0.8rem;
}
.status-pill {
  display: inline-block;
  padding: 0.25rem 0.8rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
  color: #fff;
  min-width: 70px;
  text-align: center;
}

.status-clickable {
  cursor: pointer;
  user-select: none;
}

.status-menu-inline { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
.status-option {
  padding: 0.2rem 0.6rem;
}
.status-selected {
  outline: 2px solid rgba(0,0,0,0.15);
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

.status-default {
  background-color: #6b7280;
}

/* Priority Badge */
.task-title-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.no-tasks {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #6b7280;
  text-align: center;
}

.no-tasks i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-tasks p {
  font-size: 1.1rem;
  margin: 0;
}

/* Subtasks Section - Compact Design */
.subtasks-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 1.5rem;
  margin-top: 1rem;
}

.subtasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.add-subtask-btn {
  border-radius: 6px;
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

/* Progress Bar */
.subtask-progress {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-title {
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
}

.progress-stats {
  font-size: 0.85rem;
  color: #6b7280;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-percentage {
  font-size: 0.85rem;
  font-weight: 600;
  color: #059669;
  min-width: 35px;
  text-align: right;
}

/* Subtask Form */
.subtask-form {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.subtask-form-row {
  display: flex;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
  align-items: flex-start;
}

.subtask-form-row:last-child {
  margin-bottom: 0;
}

.subtask-form-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.subtask-form-row label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.3rem;
  display: block;
}

.subtask-form-row .input-field {
  width: 100%;
}

/* Compact Subtasks List */
.subtasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.subtask-item {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.8rem;
  transition: all 0.2s ease;
}

.subtask-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.subtask-content {
  width: 100%;
}

.subtask-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.4rem;
  gap: 1rem;
}

.subtask-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
}

.subtask-meta {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  flex-shrink: 0;
}

.priority-badge {
  display: inline-block;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 600;
  text-align: center;
  min-width: 25px;
}

.priority-badge.priority-high {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.priority-badge.priority-medium {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fed7aa;
}

.priority-badge.priority-low {
  background: #f0fdf4;
  color: #059669;
  border: 1px solid #bbf7d0;
}

.subtask-description {
  color: #6b7280;
  font-size: 0.85rem;
  margin: 0.3rem 0;
  line-height: 1.3;
  word-wrap: break-word;
}

.subtask-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.3rem;
}

.subtask-due,
.subtask-owner,
.subtask-collabs,
.subtask-attachments {
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.no-subtasks {
  text-align: center;
  color: #9ca3af;
  font-style: italic;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
}

</style>
