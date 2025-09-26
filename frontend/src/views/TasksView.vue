<script setup>
import { ref, onMounted } from 'vue'
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

// Logged-in user info
const currentEmployeeId = Number(sessionStorage.getItem("employee_id"))
const currentRole = sessionStorage.getItem("role")
const currentEmployeeName = sessionStorage.getItem("employee_name")

const statusOptions = [
  { label: 'Ongoing', value: 'ongoing' },
  { label: 'Under Review', value: 'under review' },
  { label: 'Completed', value: 'done' }
]

const taskForm = ref(resetForm())

function resetForm() {
  return {
    id: null,
    name: '',
    description: '',
    due_date: null,
    status: 'ongoing',
    owner: currentEmployeeId,
    collaborators: [], // will hold full objects from backend
    attachments: []
  }
}

// ----------------- Functions -----------------
async function fetchTasks() {
  try {
    const res = await axios.get("http://localhost:5002/tasks")
    tasks.value = res.data.tasks.map(t => ({
      id: t.task_id,
      name: t.title,
      description: t.description,
      due_date: t.deadline,
      status: t.status,
      owner: t.owner,
      collaborators: t.collaborators || [], // ??
      attachments: t.attachment ? [{ name: "File", url: t.attachment }] : []
    }))
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
    parent_id: null,
    employee_id: currentEmployeeId,
    collaborators: taskForm.value.collaborators.map(c => c.employee_id), // TODO
    role: currentRole
  }

  try {
    await axios.post("http://localhost:5002/tasks", payload)
    await fetchTasks()
    showModal.value = false
    taskForm.value = resetForm()
  } catch (err) {
    console.error("Error saving task:", err)
  }
}

// ----------------- Helper Functions -----------------
function getCollaboratorNames(collaborators) {
  return collaborators.map(c => c.employee_name).join(', ')
} //TODO

function openAdd() {
  isEditing.value = true
  selectedTask.value = null
  taskForm.value = resetForm()
  showModal.value = true
}

function openDetails(task) {
  selectedTask.value = task
  isEditing.value = false
  // Use full objects for MultiSelect
  taskForm.value = { ...task }
  showModal.value = true
}

function startEditing() {
  isEditing.value = true
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
    case 'ongoing': return 'status-ongoing'
    case 'under review': return 'status-review'
    case 'done': return 'status-completed'
    default: return 'status-default'
  }
}

// ----------------- Lifecycle -----------------
onMounted(() => {
  fetchTasks()
})
</script>

<template>
<div class="tasks-page">
  <div class="tasks-header">
    <h2>My Tasks</h2>
    <Button label="+ Add Task" class="add-top-btn" @click="openAdd" />
  </div>

  <div class="tasks-grid">
    <Card v-for="task in tasks" :key="task.id" class="task-card" @click="openDetails(task)">
      <template #title>{{ task.name }}</template>
      <template #content>
        <p class="desc">{{ task.description }}</p>
        <p class="meta">📅 {{ formatDate(task.due_date) }}</p>
        <p class="status" :class="getStatusClass(task.status)">
          Status: <b>{{ task.status }}</b>
        </p>
        <p class="meta">Owner: <b>{{ task.owner_name || currentEmployeeName }}</b></p>
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
          <InputText v-model="taskForm.name" class="input-field" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.name }}</span>
        </template>
      </div>

      <div class="field-row">
        <label>Description:</label>
        <template v-if="isEditing || !selectedTask">
          <Textarea v-model="taskForm.description" rows="4" class="input-field" maxlength="100" />
        </template>
        <template v-else>
          <span class="text-field">{{ taskForm.description }}</span>
        </template>
      </div>

      <div class="field-row grid-2">
        <div>
          <label>Due Date:</label>
          <template v-if="isEditing || !selectedTask">
            <Calendar v-model="taskForm.due_date" class="input-field" />
          </template>
          <template v-else>
            <span class="text-field">{{ formatDate(taskForm.due_date) }}</span>
          </template>
        </div>
        <div>
          <label>Status:</label>
          <template v-if="isEditing || !selectedTask">
            <Dropdown v-model="taskForm.status" :options="statusOptions" optionLabel="label" optionValue="value" class="input-field w-full" />
          </template>
          <template v-else>
            <span class="text-field">{{ taskForm.status }}</span>
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
            :options="taskForm.collaborators" 
            optionLabel="employee_name"
            optionValue="employee_id"
            class="input-field w-full"
          />
        </template>
        <template v-else>
          <span class="text-field">{{ getCollaboratorNames(taskForm.collaborators) }}</span>
        </template>
      </div>

      <div class="field-row">
        <label>Attachments:</label>
        <template v-if="isEditing || !selectedTask">
          <FileUpload mode="basic" accept=".pdf" :multiple="true" choose-label="Upload" :auto="false" :customUpload="true" @select="handleAttachment" />
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
        <Button label="Save" class="save-task-btn" @click="saveTask" v-if="isEditing || !selectedTask"/>
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
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
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
</style>
