<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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
const selectedTask = ref(null)
const showModal = ref(false)
const isEditing = ref(false)
const availableEmployees = ref([]) // For collaborators

// Logged-in user info
const currentEmployeeId = Number(sessionStorage.getItem("employee_id"))
const currentRole = sessionStorage.getItem("role")
const currentEmployeeName = sessionStorage.getItem("employee_name")

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
    attachments: []
  }
}

// ----------------- Functions -----------------
async function fetchEmployees() {
  try {
    let list = []
    if (currentRole === 'staff') {
      const depRaw = sessionStorage.getItem("department") || ""
      const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(depRaw)}`, { withCredentials: true })
      const byDept = Array.isArray(res.data) ? res.data : []
      // Staff can only pick other STAFF in their department
      list = byDept.filter(e => (e.role || '').toLowerCase() === 'staff')
    } else {
      const res = await axios.get("http://localhost:5000/employees/all", { withCredentials: true })
      list = Array.isArray(res.data) ? res.data : []
      // Managers/HR/Senior Manager can pick everyone
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
    const fetchedTasks = res.data.tasks.map(t => ({
      id: t.task_id,
      name: t.title,
      description: t.description,
      due_date: t.deadline,
      status: t.status,
      priority: t.priority || 5, // Use priority from backend, default to 5
      owner: t.owner,
      collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(id => Number(id)) : [],
      attachments: t.attachment ? [{ name: "File", url: t.attachment }] : []
    }))

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
  const payload = {
    title: taskForm.value.name,
    description: taskForm.value.description,
    attachment: taskForm.value.attachments.length ? taskForm.value.attachments[0].url : null,
    deadline: taskForm.value.due_date
      ? new Date(taskForm.value.due_date).toISOString()
      : new Date().toISOString(),
    status: taskForm.value.status,
    priority: taskForm.value.priority,
    parent_id: null,
    employee_id: currentEmployeeId,
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

  try {
    if (taskForm.value.id) {
      await axios.put(`http://localhost:5002/task/${taskForm.value.id}`, payload)
    } else {
      await axios.post("http://localhost:5002/tasks", payload)
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
  }
}

function isStaff() { return currentRole === 'staff' }
function isOwner(task) { return !!task && task.owner === currentEmployeeId }
function isCollaborator(task) {
  if (!task) return false
  const collabIds = Array.isArray(task.collaborators) ? task.collaborators : []
  return collabIds.includes(currentEmployeeId)
}
function isCollaboratorOnly(task) {
  return isStaff() && isCollaborator(task) && !isOwner(task)
}

async function updateTaskStatus(task, newStatus) {
  try {
    await axios.put(`http://localhost:5002/task/${task.id}`, { status: newStatus, employee_id: currentEmployeeId })
    task.status = newStatus
    if (openStatusFor.value === task.id) openStatusFor.value = null
  } catch (err) {
    console.error("Error updating status:", err)
  }
}

function toggleStatusMenu(task) {
  openStatusFor.value = openStatusFor.value === task.id ? null : task.id
}

// ----------------- Helper Functions -----------------
function findEmployeeNameById(id) {
  const emp = (availableEmployees.value || []).find(e => e.employee_id === id)
  return emp ? emp.employee_name : ''
}
function getOwnerName(ownerId) {
  if (!ownerId) return currentEmployeeName || ''
  const name = findEmployeeNameById(ownerId)
  return name || (ownerId === currentEmployeeId ? currentEmployeeName : '')
}

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
    collaborators: task.collaborators || [],
    attachments: task.attachments || []
  }
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
  const newFiles = event.files.map(file => ({ name: file.name, url: file.name }))
  taskForm.value.attachments.push(...newFiles)
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

// ----------------- Lifecycle -----------------
const refreshIntervalMs = 30000
let refreshTimer = null

onMounted(() => {
  fetchEmployees().finally(() => fetchTasks())
  // Auto-refresh
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
  <h2>My Tasks</h2>
  <div class="header-buttons">
    <Button icon="pi pi-filter" label="Filter" class="filter-btn" text />
    <Button label="+ Add Task" class="add-top-btn" @click="openAdd" />
  </div>
</div>

  <div class="tasks-grid">
    <Card v-for="task in tasks" :key="task.id" class="task-card" @click="openDetails(task)">
      <template #title>
        <div class="task-title-row">
          <span>{{ task.name }}</span>
          <span class="priority-badge" :class="getPriorityClass(task.priority)">
            {{ task.priority }}
          </span>
        </div>
      </template>
      <template #content>
        <p class="desc">{{ task.description }}</p>
        <p class="meta">📅 {{ formatDate(task.due_date) }}</p>
        <p class="status" :class="getStatusClass(task.status)" v-if="!(isStaff() && isOwner(task))">
          {{ task.status }}
        </p>
        <span
          v-else
          class="status-pill status-clickable"
          :class="getStatusClass(task.status)"
          @click.stop="toggleStatusMenu(task)"
          title="Change status"
        >{{ task.status }}</span>
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

  

  <Dialog v-model:visible="showModal" modal 
          :header="isEditing && !selectedTask ? 'New Task' : (isEditing ? 'Edit Task' : 'Task Details')" 
          class="page-style-modal">
    <div class="modal-content">
      <div class="field-row">
        <label>Name:</label>
        <template v-if="isEditing || !selectedTask">
          <InputText v-model="taskForm.name" class="input-field" :disabled="selectedTask && isStaff() && taskForm.owner === currentEmployeeId" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.name }}</span>
        </template>
      </div>

      <div class="field-row">
        <label>Description:</label>
        <template v-if="isEditing || !selectedTask">
          <Textarea v-model="taskForm.description" rows="4" class="input-field" maxlength="100" :disabled="selectedTask && isStaff() && taskForm.owner === currentEmployeeId" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.description }}</span>
        </template>
      </div>

      <div class="field-row grid-3">
        <div>
          <label>Due Date:</label>
          <template v-if="isEditing || !selectedTask">
            <Calendar v-model="taskForm.due_date" class="input-field" :minDate="new Date()" :disabled="selectedTask && isCollaboratorOnly(selectedTask)" />
          </template>
          <template v-else>
            <span class="text-field">{{ formatDate(taskForm.due_date) }}</span>
          </template>
        </div>
        <div>
          <label>Status:</label>
          <template v-if="isEditing && selectedTask && !isStaff()">
            <!-- Only show status dropdown when editing existing tasks -->
            <Dropdown v-model="taskForm.status" :options="statusOptions" optionLabel="label" optionValue="value" class="input-field w-full" />
          </template>
          <template v-else>
            <span class="text-field">{{ taskForm.status }}</span>
          </template>
        </div>
        <div>
          <label>Priority:</label>
          <template v-if="isEditing || !selectedTask">
            <Dropdown v-model="taskForm.priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="input-field w-full" :disabled="selectedTask && isCollaboratorOnly(selectedTask)" />
          </template>
          <template v-else>
            <span class="text-field">{{ taskForm.priority }}</span>
          </template>
        </div>
      </div>

      <div class="field-row">
        <label>Owner:</label>
        <span class="text-field">{{ currentEmployeeName }}</span>
      </div>

      <div class="field-row">
        <label>Collaborators:</label>
        <template v-if="isEditing || !selectedTask">
          <MultiSelect
            v-model="taskForm.collaborators"
            :options="availableEmployees" 
            optionLabel="employee_name"
            optionValue="employee_id"
            class="input-field w-full"
            :disabled="selectedTask && isCollaboratorOnly(selectedTask)"
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
          <FileUpload mode="basic" accept=".pdf" :multiple="true" choose-label="Upload" :auto="false" :customUpload="true" @select="handleAttachment" :disabled="selectedTask && isCollaboratorOnly(selectedTask)" />
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

      <div class="save-btn-container">
        <template v-if="selectedTask && !isEditing">
          <Button label="Edit" class="save-task-btn" @click="startEditing" />
        </template>
        <Button label="Save" class="save-task-btn" @click="saveTask" v-if="isEditing || !selectedTask" :disabled="selectedTask && isCollaboratorOnly(selectedTask)"/>
      </div>
    </div>
  </Dialog>
</div>
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

/* Task Grid */
.tasks-page { padding: 2rem; }
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
  padding: 1.2rem;
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
  min-width: 400px;
  max-height: 85vh;           
  border-radius: 12px;
  font-family: 'Segoe UI', sans-serif;
  margin: 2rem auto !important; 
}

:deep(.page-style-modal .p-dialog-content) {
  min-height: 400px; 
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
  min-height: 500px
}

/* Fields */
.field-row { display: flex; flex-direction: column; gap: 0.5rem; }
.field-row label { font-weight: 600; font-size: 1rem; color: #333; }
.input-field { border-radius: 8px; padding: 0.5rem 0.8rem; font-size: 0.95rem; border: 1px solid #ccc; }
.text-field {
  font-size: 0.95rem;
  color: #444;
  padding: 0.3rem 0;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
  max-width: 100%; 
  display: block;   
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
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
  min-width: 24px;
  flex-shrink: 0;
}

.priority-high {
  background-color: #ef4444; /* Red for high priority */
}

.priority-medium {
  background-color: #f59e0b; /* Orange for medium priority */
}

.priority-low {
  background-color: #10b981; /* Green for low priority */
}

</style>
