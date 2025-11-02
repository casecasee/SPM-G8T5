<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import FileUpload from 'primevue/fileupload'
import MultiSelect from 'primevue/multiselect'
import { getProjects, updateProject } from '../api/projects'
import { listTasks, createTask, updateTaskProject } from '../api/tasks'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.id))
const project = ref(null)
const projects = ref([])
const loading = ref(false)
const error = ref('')
const allTasks = ref([])
const currentEmployeeId = Number(sessionStorage.getItem('employee_id')) || null
const currentEmployeeName = sessionStorage.getItem('employee_name') || ''
const currentRole = sessionStorage.getItem('role') || ''
const activeTab = ref('all') // 'all' | 'mine'
const showAddModal = ref(false)
const showEditProject = ref(false)
const editDueDate = ref(null)
const editMembers = ref([])
const editError = ref('')

// Add these new data properties
const availableEmployees = ref([])
const fileUploadRef = ref(null)
const comments = ref([])
const newComment = ref('')
const newCommentAttachments = ref([])
const editingCommentId = ref(null)
const editingContent = ref('')
const commentError = ref('')

// Mention suggestions
const mentionable = ref([])
const showMentionList = ref(false)
const mentionQuery = ref('')
const mentionStartIdx = ref(-1)
const mentionHighlighted = ref(0)

const currentTab = ref('')

// Options for dropdowns
const statusOptions = [
  { label: 'Unassigned', value: 'unassigned' },
  { label: 'Ongoing', value: 'ongoing' },
  { label: 'Under Review', value: 'under review' },
  { label: 'Done', value: 'done' }
]

const priorityOptions = [
  { label: '1 - Lowest', value: 1 },{ label: '2', value: 2 },{ label: '3', value: 3 },{ label: '4', value: 4 },
  { label: '5 - Medium', value: 5 },{ label: '6', value: 6 },{ label: '7', value: 7 },{ label: '8', value: 8 },
  { label: '9', value: 9 },{ label: '10 - Highest', value: 10 }
]

// Add/Attach state
const addTab = ref('create') // 'create' | 'attach'
const createTaskNow = ref(true)
const selectedExisting = ref([])
const addBusy = ref(false)
const addError = ref('')
const searchExisting = ref('')
// Validation state for Add Task modal
const formErrors = ref({})
const showValidationErrors = ref(false)

// Replace taskForm with Tasks page structure
function resetForm() {
  const role = (currentRole || '').toLowerCase()
  let defaultStatus = 'ongoing'

  // Only these roles start as "unassigned"
  if (['manager', 'hr', 'senior director', 'senior manager'].includes(role)) {
    defaultStatus = 'unassigned'
  }
  
  return {
    id: null,
    name: '',
    description: '',
    due_date: null,
    status: defaultStatus,
    priority: 5, 
    owner: currentEmployeeId, 
    collaborators: [], 
    project_id: projectId.value, // ← This is the key difference - prefilled with current project
    attachments: []
  }
}

const taskForm = ref(resetForm())

const projectTasks = computed(() => {
  const pid = projectId.value
  return (allTasks.value || [])
    .filter(t => Number(t.project_id) === pid)
    .map(t => ({
      id: t.task_id,
      name: t.title,
      description: t.description,
      due_date: t.deadline,
      status: t.status,
      priority: t.priority || 5,
      owner: t.owner,
      collaborators: Array.isArray(t.collaborators) ? t.collaborators : []
    }))
    .sort((a, b) => (b.priority || 0) - (a.priority || 0))
})

const myProjectTasks = computed(() =>
  projectTasks.value.filter(t => t.owner === currentEmployeeId || (Array.isArray(t.collaborators) && t.collaborators.includes(currentEmployeeId)))
)

const canManage = computed(() => {
  const p = project.value
  return !!p && Number(p.ownerId) === currentEmployeeId
})

// Computed properties for Tasks page functionality
const filteredStatusOptions = computed(() => {
  if (currentRole === 'staff') {
    return statusOptions.filter(opt => opt.value !== 'unassigned');
  }
  return statusOptions;
});

const projectOptions = computed(() => {
  const opts = [{ label: 'None', value: null }]
  for (const p of (projects.value || [])) {
    opts.push({ label: `${p.name} (#${p.id})`, value: p.id })
  }
  return opts
})

const employeeDisplayList = computed(() => {
  return (availableEmployees.value || []).map(emp => ({
    ...emp,
    display_label: `${emp.employee_name} (${emp.role}) - ${emp.department || 'N/A'}`
  }))
})

const filteredMentionable = computed(() => {
  const q = (mentionQuery.value || '').trim().toLowerCase()
  if (!q) return mentionable.value
  return (mentionable.value || []).filter(u => (u.employee_name || '').toLowerCase().includes(q))
})

// Disable past dates in the add-task date picker (match Tasks page behavior)
const minDate = computed(() => {
  return new Date().toISOString().slice(0, 16)
})

const unassignedTasks = computed(() => (allTasks.value || []).filter(t => !t.project_id && Number(t.owner) === currentEmployeeId))
const filteredUnassigned = computed(() => {
  const q = (searchExisting.value || '').trim().toLowerCase()
  const list = unassignedTasks.value
  if (!q) return list
  return list.filter(t => (t.title || '').toLowerCase().includes(q))
})

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString()
}

function formatDueDate(dueDate) {
  if (!dueDate) return '-'
  const date = new Date(dueDate)
  if (isNaN(date.getTime())) return '-'
  const dateLabel = date.toLocaleDateString()
  const now = new Date()
  const d0 = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const n0 = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const diffDays = Math.round((d0 - n0) / (1000 * 60 * 60 * 24))

  let rel
  if (diffDays < 0) {
    rel = `${Math.abs(diffDays)} days overdue`
  } else if (diffDays === 0) {
    rel = 'today'
  } else if (diffDays === 1) {
    rel = 'tomorrow'
  } else {
    rel = `in ${diffDays} days`
  }
  return `${dateLabel} (${rel})`
}

function statusClass(status) {
  switch ((status || '').toLowerCase()) {
    case 'ongoing': return 'status-pill status-ongoing'
    case 'under review': return 'status-pill status-review'
    case 'done': return 'status-pill status-completed'
    default: return 'status-pill status-default'
  }
}

// project status visuals removed

function clearValidationErrors() {
  formErrors.value = {}
  showValidationErrors.value = false
}

function getFieldError(field) {
  return formErrors.value[field]
}

function validateForm() {
  const errors = {}

  if (!taskForm.value.name || !taskForm.value.name.trim()) {
    errors.name = 'Task name is required'
  }

  if (!taskForm.value.description || !taskForm.value.description.trim()) {
    errors.description = 'Description is required'
  }

  if (!taskForm.value.due_date || String(taskForm.value.due_date).trim() === '') {
    errors.due_date = 'Due date is required'
  } else {
    const d = new Date(taskForm.value.due_date)
    if (isNaN(d.getTime()) || d <= new Date()) {
      errors.due_date = 'Deadline must be in the future'
    }
  }

  if (taskForm.value.priority == null) {
    errors.priority = 'Priority is required'
  }

  formErrors.value = errors
  showValidationErrors.value = Object.keys(errors).length > 0
  return !showValidationErrors.value
}

function toLocalInput(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (isNaN(d.getTime())) return null
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day}T${hh}:${mm}`
}

function openEditProject() {
  editError.value = ''
  editDueDate.value = toLocalInput(project.value?.dueDate || null)
  editMembers.value = Array.isArray(project.value?.memberIds) ? [...project.value.memberIds] : []
  showEditProject.value = true
}

async function saveEditProject() {
  editError.value = ''
  const currentIds = new Set(project.value?.memberIds || [])
  const nextIds = new Set(editMembers.value || [])
  const add = [...[...nextIds].filter(id => !currentIds.has(id))]
  const remove = [...[...currentIds].filter(id => !nextIds.has(id))]
  const dueDateISO = editDueDate.value ? new Date(editDueDate.value).toISOString() : null
  try {
    const res = await updateProject(projectId.value, { dueDate: dueDateISO, add, remove })
    project.value = { ...project.value, ...res }
    showEditProject.value = false
  } catch (e) {
    const msg = e?.response?.data?.error || 'Failed to update project'
    editError.value = msg
  }
}

async function saveTask() {
  clearValidationErrors()
  if (!validateForm()) return
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

    let deadlineDate
    if (taskForm.value.due_date) {
      if (taskForm.value.due_date instanceof Date) {
        deadlineDate = taskForm.value.due_date.toISOString()
      } else {
        deadlineDate = new Date(taskForm.value.due_date).toISOString()
      }
    } else {
      // Set deadline to 7 days from now in local timezone
      const futureDate = new Date()
      futureDate.setDate(futureDate.getDate() + 7)
      deadlineDate = futureDate.toISOString()
    }

    const payload = {
      title: taskForm.value.name,
      description: taskForm.value.description,
      attachments: uploadedAttachments,
      deadline: deadlineDate,
      status: taskForm.value.status,
      priority: taskForm.value.priority,
      parent_id: null,
      employee_id: currentEmployeeId,
      owner: taskForm.value.owner,
      project_id: projectId.value, // ← Always use current project ID
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

    const createRes = await axios.post("http://localhost:5002/tasks", payload, { withCredentials: true })
    console.log("Task created:", createRes.data)

    // Refresh tasks list
    await load()
    
    showAddModal.value = false
    taskForm.value = resetForm()
    comments.value = []
  } catch (error) {
    console.error("Error creating task:", error)
    const msg = error?.response?.data?.message || 'Failed to create task. Please try again.'
    addError.value = msg
  }
}

// Keep the attach existing functionality
async function addTasksToProject() {
  if (addBusy.value) return
  addError.value = ''
  const ops = []
  const pid = projectId.value

  if (addTab.value === 'attach' && selectedExisting.value.length) {
    for (const id of selectedExisting.value) {
      const t = (allTasks.value || []).find(x => x.task_id === id)
      if (t) ops.push(updateTaskProject(id, pid, t.owner))
    }
  }

  if (ops.length === 0) return
  try {
    addBusy.value = true
    await Promise.allSettled(ops)
    // refresh tasks list and clear selections
    allTasks.value = await listTasks()
    selectedExisting.value = []
    showAddModal.value = false
  } catch (_) {}
  finally {
    addBusy.value = false
  }
}

async function fetchEmployees() {
  try {
    const role = (currentRole || '').toLowerCase()
    if (role === 'senior manager' || role === 'hr') {
      const res = await axios.get("http://localhost:5000/employees/all", { withCredentials: true })
      availableEmployees.value = Array.isArray(res.data) ? res.data : []
    } else {
      const depRaw = sessionStorage.getItem("department") || ""
      const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(depRaw)}`, { withCredentials: true })
      availableEmployees.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (err) {
    console.error("Error fetching employees:", err)
    availableEmployees.value = []
  }
}

async function fetchMentionable(taskId) {
  try {
    const res = await axios.get(`http://localhost:5002/task/${taskId}/mentionable`, { withCredentials: true })
    mentionable.value = res.data || []
  } catch (error) {
    console.error("Error fetching mentionable users:", error)
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const list = await getProjects()
    projects.value = list
    project.value = list.find(p => p.id === projectId.value) || null
  } catch (e) {
    error.value = 'Failed to load project.'
  }
  try {
    allTasks.value = await listTasks()
  } catch (e) {
    allTasks.value = []
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'projects' })
}

function goToTimeline() {
  router.push({ name: 'project-timeline', params: { id: projectId.value } })
}

function openTask(t) {
  router.push({
    name: 'tasks',
    query: {
      taskId: t.id,
      open: 'details',
      from: 'project',
      projectId: projectId.value
    }
  })
}

// Helper functions from Tasks page
function getOwnerName(ownerId) {
  const emp = availableEmployees.value.find(e => e.employee_id === ownerId)
  return emp ? emp.employee_name : `#${ownerId}`
}

function getCollaboratorNames(collaborators) {
  if (!collaborators || !Array.isArray(collaborators)) return 'None'
  const names = collaborators.map(id => {
    const emp = availableEmployees.value.find(e => e.employee_id === id)
    return emp ? emp.employee_name : `#${id}`
  })
  return names.join(', ')
}

function getProjectLabelById(projectId) {
  if (!projectId) return 'None'
  const project = projects.value.find(p => p.id === projectId)
  return project ? `${project.name} (#${project.id})` : `#${projectId}`
}

function canAssignTasks() {
  return ['manager', 'hr', 'senior director', 'senior manager'].includes(currentRole.toLowerCase())
}

function canEdit(task) {
  if (!task) return true // New task
  return task.owner === currentEmployeeId || canAssignTasks()
}

// File upload handling
function handleAttachment(event) {
  const files = event.files
  for (const file of files) {
    taskForm.value.attachments.push({
      file: file,
      name: file.name,
      url: null
    })
  }
}

function removeAttachment(index) {
  taskForm.value.attachments.splice(index, 1)
}

// Comment and mention handling (simplified for Projects page)
function onCommentInput(e) {
  // Simplified version - you can add full mention functionality if needed
}

function hideMentionList() {
  showMentionList.value = false
  mentionQuery.value = ''
  mentionStartIdx.value = -1
  mentionHighlighted.value = 0
}

onMounted(async () => {
  await Promise.allSettled([load(), fetchEmployees()])
})




// Data
const projectReportTasks = ref([])
const projectReportGenerating = ref(false)
const projectReportError = ref('')

// Computed
const projectReportCompleted = computed(() =>
  projectReportTasks.value.filter(t => t.status.toLowerCase() === 'done' || t.status.toLowerCase() === 'completed').length
)
const projectReportOngoing = computed(() =>
  projectReportTasks.value.filter(t => t.status.toLowerCase() === 'ongoing').length
)
const projectReportOverdue = computed(() =>
  projectReportTasks.value.filter(t => {
    if (!t.due_date) return false
    const due = new Date(t.due_date)
    return due < new Date() && !['done', 'completed'].includes(t.status.toLowerCase())
  }).length
)
const projectReportOverallProgress = computed(() => {
  const total = projectReportTasks.value.length
  if (total === 0) return 'No Data'
  const completed = projectReportCompleted.value
  const ratio = completed / total
  if (ratio >= 0.7) return 'Good'
  if (ratio >= 0.4) return 'Average'
  return 'Poor'
})

// Helper functions
function report_formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString()
}
function report_formatDueDate(dueDate) {
  if (!dueDate) return '-'
  const date = new Date(dueDate)
  const now = new Date()
  const diffDays = Math.round((date - now) / (1000 * 60 * 60 * 24))
  let rel = diffDays < 0 ? `${Math.abs(diffDays)} days overdue` : diffDays === 0 ? 'today' : `in ${diffDays} days`
  return `${date.toLocaleDateString()} (${rel})`
}
function report_statusClass(status) {
  switch ((status || '').toLowerCase()) {
    case 'ongoing': return 'status-pill status-ongoing'
    case 'under review': return 'status-pill status-review'
    case 'done': return 'status-pill status-completed'
    default: return 'status-pill status-default'
  }
}
function report_getOwnerName(ownerId) {
  const emp = projectTeam.value.find(e => e.employee_id === ownerId)
  return emp ? emp.employee_name : `#${ownerId}`
}
function report_getCollaboratorNames(collaborators) {
  if (!collaborators || !Array.isArray(collaborators)) return 'None'
  return collaborators.map(id => {
    const emp = projectTeam.value.find(e => e.employee_id === id)
    return emp ? emp.employee_name : `#${id}`
  }).join(', ')
}

// Export PDF
function exportProjectReportPDF() {
  if (!projectReportTasks.value.length) return
  projectReportGenerating.value = true

  const doc = new jsPDF()
  doc.setFontSize(14)
  doc.text(`Project Report: ${project.name || 'N/A'}`, 14, 20)

  const rows = projectReportTasks.value.map(t => [
    t.name,
    getOwnerName(t.owner),
    formatDate(t.start_date),
    formatDueDate(t.due_date),
    t.status,
    getCollaboratorNames(t.collaborators)
  ])

  doc.autoTable({
    startY: 30,
    head: [['Task Name','Owner','Start','Due','Status','Collaborators']],
    body: rows,
    styles: { fontSize: 10 }
  })

  doc.save(`Project_Report_${project?.name || 'Project'}.pdf`)
  projectReportGenerating.value = false
}


</script>

<template>
<div class="project-detail">
  <div class="header-row">
    <div class="left">
      <h2>Project Details <span class="pid">#{{ projectId }}</span></h2>
      <p class="breadcrumb"><a href="#" @click.prevent="goBack">Projects</a> / <span>#{{ projectId }}</span></p>
    </div>
    <div class="right">
      <Button label="Back" class="btn" @click="goBack" />
      <Button v-if="canManage" label="Edit Project" class="btn" @click="openEditProject" />
    </div>
  </div>
 
      <button
  :class="['tab', currentTab==='project_report' ? 'active' : '']"
  @click="currentTab = 'project_report'"
>Project Report</button>
    
  <!-- ===========================
  PROJECT REPORT (Current Project)
=========================== -->
<div v-if="currentTab === 'project_report'" class="report-tab">
  <div class="report-controls">
    <div class="left-controls">
           <button
  :class="['tab', currentTab==='' ? 'active' : '']"
  @click="currentTab = ''"
>Back</button>
      <span>{{ project?.name || 'Project Report' }}</span>
    </div>

    <div class="right-controls">
      <button class="download-btn" @click="exportProjectReportPDF" :disabled="projectReportGenerating">
        <i class="pi pi-file-pdf"></i> Download Report
      </button>
    </div>
  </div>

  <div class="report-card">
    <h2 class="report-title">📁 Project Schedule Report</h2>

    <div v-if="projectReportError" class="error-message">{{ projectReportError }}</div>

    <div v-if="projectReportTasks.length">
      <div class="report-summary">
        <ul>
          <li><strong>Total Tasks:</strong> {{ projectReportTasks.length }}</li>
          <li><strong>Completed:</strong> {{ projectReportCompleted }}</li>
          <li><strong>Ongoing:</strong> {{ projectReportOngoing }}</li>
          <li><strong>Overdue:</strong> {{ projectReportOverdue }}</li>
          <li><strong>Overall Progress:</strong> {{ projectReportOverallProgress }}</li>
        </ul>
      </div>

      <table class="report-table">
        <thead>
          <tr>
            <th>Task Name</th>
            <th>Owner</th>
            <th>Start Date</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Collaborators</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in projectReportTasks" :key="task.id">
            <td>{{ task.name }}</td>
            <td>{{ report_getOwnerName(task.owner) }}</td>
            <td>{{ report_formatDate(task.start_date) }}</td>
            <td>{{ report_formatDueDate(task.due_date) }}</td>
            <td :class="statusClass(task.status)">{{ task.status }}</td>
            <td>{{ report_getCollaboratorNames(task.collaborators) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="no-data">No tasks available for this project.</div>
  </div>
</div>

  <div v-if="loading" class="card like">Loading…</div>
  <div v-else-if="error" class="error">{{ error }}</div>

  <div v-if="project" class="card details">
    <div class="meta-grid">
      <div>
        <div class="label">Name</div>
        <div class="value">{{ project.name }} <span class="pid">#{{ project.id }}</span></div>
      </div>
      <div>
        <div class="label">Owner</div>
        <div class="value">{{ project.owner || 'Unassigned' }}</div>
      </div>
      
      <div>
        <div class="label">Tasks</div>
        <div class="value">{{ project.tasksDone }} / {{ project.tasksTotal }}</div>
      </div>
      <div>
        <div class="label">Members</div>
        <div class="value">{{ (project.memberNames && project.memberNames.length) ? project.memberNames.join(', ') : '-' }}</div>
      </div>
      <div>
        <div class="label">Due Date</div>
        <div class="value">{{ formatDueDate(project.dueDate) }}</div>
      </div>
      <div>
        <div class="label">Last Updated</div>
        <div class="value">{{ formatDate(project.updatedAt) }}</div>
      </div>
    </div>
  </div>

  <div class="tasks-header">
    <h3 class="section-title">Tasks</h3>
    <div class="header-buttons">
      <Button label="📅 Timeline View" class="btn-secondary" @click="goToTimeline" />
      <Button v-if="canManage" label="+ Add Task" class="btn-primary" @click="showAddModal=true" />
    </div>
  </div>
  <div class="tabs">
    <button :class="['tab', activeTab==='all' ? 'active' : '']" @click="activeTab='all'">All</button>
    <button :class="['tab', activeTab==='mine' ? 'active' : '']" @click="activeTab='mine'">My Tasks</button>
  </div>

  <div v-if="(activeTab==='all' ? projectTasks : myProjectTasks).length === 0" class="no-tasks">
    No tasks found.
  </div>

  <div class="tasks-grid">
    <Card v-for="t in (activeTab==='all' ? projectTasks : myProjectTasks)" :key="t.id" class="task-card" @click="openTask(t)">
      <template #title>
        <div class="task-title-row">
          <span>{{ t.name }}</span>
          <span class="priority-badge" :class="t.priority >= 8 ? 'priority-high' : (t.priority >=5 ? 'priority-medium' : 'priority-low')">P{{ t.priority }}</span>
        </div>
      </template>
      <template #content>
        <p class="desc">{{ t.description }}</p>
        <p class="meta">📅 {{ formatDate(t.due_date) }}</p>
        <p class="meta"><span :class="statusClass(t.status)">{{ t.status }}</span></p>
      </template>
    </Card>
  </div>

  <!-- Add Task Modal -->
  <Dialog v-if="canManage" v-model:visible="showAddModal" modal header="Add Task" class="page-style-modal">
    <div class="pill-tabs">
      <button :class="['pill', addTab==='create' ? 'active' : '']" @click="addTab='create'">Create New</button>
      <button :class="['pill', addTab==='attach' ? 'active' : '']" @click="addTab='attach'">Attach Existing</button>
    </div>

    <div v-if="addTab==='create'" class="modal-content">
      <div v-if="showValidationErrors" class="error" style="padding:8px; border:1px solid #fecaca; background:#fef2f2; border-radius:6px; margin-bottom:12px;">
        <strong>Please fix the following:</strong>
        <ul style="margin:6px 0 0 16px;">
          <li v-for="(msg, field) in formErrors" :key="field">{{ msg }}</li>
        </ul>
      </div>
      <div class="field-row">
        <label>Name:</label>
        <InputText v-model="taskForm.name" class="input-field" />
        <div v-if="getFieldError('name')" class="error">{{ getFieldError('name') }}</div>
      </div>

      <div class="field-row">
        <label>Description:</label>
        <Textarea v-model="taskForm.description" rows="4" class="input-field" maxlength="100" />
        <div v-if="getFieldError('description')" class="error">{{ getFieldError('description') }}</div>
      </div>

      <div class="field-row grid-3">
        <div>
          <label>Due Date:</label>
          <input type="datetime-local" v-model="taskForm.due_date" :min="minDate" class="input-field" />
          <div v-if="getFieldError('due_date')" class="error">{{ getFieldError('due_date') }}</div>
        </div>
        <div>
          <label>Status:</label>
          <div class="meta">
            <span :class="statusClass(taskForm.status)">{{ taskForm.status }}</span>
          </div>
        </div>
        <div>
          <label>Priority:</label>
          <Dropdown v-model="taskForm.priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="input-field w-full" />
          <div v-if="getFieldError('priority')" class="error">{{ getFieldError('priority') }}</div>
        </div>
      </div>

      <div class="field-row">
        <label>Project:</label>
        <span class="text-field">{{ getProjectLabelById(projectId) }} (Fixed)</span>
      </div>

      <div class="field-row" v-if="canAssignTasks()">
        <label>Owner:</label>
        <Dropdown
          v-model="taskForm.owner"
          :options="employeeDisplayList"
          optionLabel="display_label"
          optionValue="employee_id"
          placeholder="Select owner..."
          class="input-field w-full"
          filter
          filterBy="display_label,employee_name,role,team,department"
        />
      </div>

      <div class="field-row" v-else>
        <label>Owner:</label>
        <span class="text-field">{{ getOwnerName(taskForm.owner) || currentEmployeeName }}</span>
      </div>

      <div class="field-row">
        <label>Collaborators:</label>
        <MultiSelect
          v-model="taskForm.collaborators"
          :options="employeeDisplayList.filter(emp => emp.employee_id !== taskForm.owner)"
          optionLabel="display_label"
          optionValue="employee_id"
          class="input-field w-full"
          placeholder="Select collaborators..."
          filter
          filterBy="display_label,employee_name,role,team,department"
        />
      </div>

      <div class="field-row">
        <label>Attachments:</label>
        <FileUpload 
          ref="fileUploadRef"
          mode="basic" 
          accept=".pdf" 
          :multiple="true"
          chooseLabel="Upload" 
          :auto="false" 
          :customUpload="true" 
          @select="handleAttachment"
        />
        <ul class="file-list">
          <li v-for="(file, index) in taskForm.attachments" :key="index">
            <a :href="file.url" target="_blank">{{ file.name }}</a>
            <Button icon="pi pi-times" class="p-button-danger p-button-text p-button-sm" @click="removeAttachment(index)"/>
          </li>
        </ul>
      </div>
    </div>

    <div v-else>
      <div class="attach-toolbar">
        <input class="search input" v-model="searchExisting" placeholder="Search tasks by title" />
        <span class="muted">{{ filteredUnassigned.length }} available</span>
      </div>
      <div class="attach-list">
        <label v-for="t in filteredUnassigned" :key="t.task_id" class="attach-item">
          <input type="checkbox" v-model="selectedExisting" :value="t.task_id" />
          <div class="attach-meta">
            <div class="attach-title">{{ t.title }}</div>
            <div class="attach-sub">ID: {{ t.task_id }}</div>
          </div>
        </label>
      </div>
    </div>

    <p v-if="addError" class="error" style="margin-top:8px;">{{ addError }}</p>
    <div style="display:flex;justify-content:flex-end;margin-top:12px;gap:8px;">
      <button class="btn btn-secondary" @click="showAddModal=false" :disabled="addBusy">Cancel</button>
      <button class="btn btn-primary" @click="addTab==='create' ? saveTask() : addTasksToProject()" :disabled="addBusy">{{ addBusy ? 'Processing…' : (addTab==='create' ? 'Create Task' : 'Add') }}</button>
    </div>
  </Dialog>

  <!-- Edit Project Modal -->
  <Dialog v-if="canManage" v-model:visible="showEditProject" modal header="Edit Project" class="page-style-modal">
    <div class="modal-content">
      <div class="field-row">
        <label>Project Due Date</label>
        <input type="datetime-local" v-model="editDueDate" class="input-field" />
      </div>
      <div class="field-row">
        <label>Members</label>
        <MultiSelect
          v-model="editMembers"
          :options="employeeDisplayList"
          optionLabel="display_label"
          optionValue="employee_id"
          class="input-field w-full"
          placeholder="Select members..."
          filter
          filterBy="display_label,employee_name,role,team,department"
        />
        <small class="muted">Removing a member fails if they are involved in any task in this project.</small>
      </div>
      <p v-if="editError" class="error" style="margin-top:8px;">{{ editError }}</p>
      <div style="display:flex;justify-content:flex-end;margin-top:12px;gap:8px;">
        <button class="btn btn-secondary" @click="showEditProject=false">Cancel</button>
        <button class="btn btn-primary" @click="saveEditProject">Save</button>
      </div>
    </div>
  </Dialog>
</div>
</template>

<style scoped>
.project-detail { padding: 24px; }
.header-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.breadcrumb { margin: 4px 0 0; color:#6b7280; font-size: 12px; }
.breadcrumb a { color:#2563eb; text-decoration:none; }
.card.details { border:1px solid #e5e7eb; border-radius:12px; background:#fff; padding:16px; margin-bottom:16px; }
.meta-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap:12px; }
.label { font-size:12px; color:#6b7280; }
.value { font-weight:600; }
.pid { color:#9ca3af; font-weight:500; margin-left:6px; }
.badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:600; background:#e5e7eb; color:#374151; }
/* status badge styles removed */
.section-title { margin:16px 0 8px; }
.header-buttons { display:flex; gap:8px; align-items:center; }
.tabs { display:flex; gap:8px; margin:8px 0 12px; }
.tab { border:1px solid #e5e7eb; background:#fff; color:#111827; padding:6px 12px; border-radius: var(--radius-pill); cursor:pointer; font-weight:600; }
.tab.active { background:#111827; color:#fff; }
.no-tasks { color:#6b7280; margin:8px 0 16px; }
.tasks-grid { display:grid; gap:16px; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }
.task-card { cursor:pointer; }
.task-title-row { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.priority-badge { padding:2px 6px; border-radius:4px; font-size:12px; font-weight:700; }
.priority-high { background:#fee2e2; color:#991b1b; border:1px solid #fecaca; }
.priority-medium { background:#fffbeb; color:#92400e; border:1px solid #fed7aa; }
.priority-low { background:#ecfdf5; color:#065f46; border:1px solid #bbf7d0; }
.desc { color:#555; font-size:0.95rem; }
.meta { font-size:0.9rem; margin-top:6px; }
.status-pill { display:inline-block; padding: 2px 8px; border-radius:999px; color:#fff; font-size:12px; font-weight:600; }
.status-ongoing { background:#3b82f6; }
.status-review { background:#f59e0b; }
.status-completed { background:#10b981; }
.status-default { background:#6b7280; }
.btn { border:1px solid #d1d5db; }
.pill-tabs { display:flex; gap:8px; margin:8px 0; }
.pill { border:1px solid #e5e7eb; background:#fff; color:#111827; padding:6px 12px; border-radius: var(--radius-pill); cursor:pointer; font-weight:600; }
.pill.active { background:#111827; color:#fff; }
.attach-toolbar { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:8px; }
.muted { color:#6b7280; }
.attach-list { display:flex; flex-direction:column; gap:6px; margin-top:8px; max-height:240px; overflow:auto; border:1px solid #e5e7eb; border-radius: var(--radius-md); padding:8px; }
.attach-item { display:flex; align-items:flex-start; gap:10px; padding:8px; border:1px solid #e5e7eb; border-radius: var(--radius-md); background:#fff; }
.attach-item:hover { background:#f8fafc; }
.attach-title { font-weight:600; }
.attach-sub { color:#6b7280; font-size:12px; }

/* New styles for Tasks page form */
.modal-content {
  padding: 0;
}

.field-row {
  margin-bottom: 16px;
}

.field-row.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

.input-field {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.text-field {
  padding: 8px 12px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #6b7280;
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.file-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  margin-bottom: 4px;
}

.file-list a {
  color: #2563eb;
  text-decoration: none;
}

.file-list a:hover {
  text-decoration: underline;
}

.w-full {
  width: 100%;
}
</style>

