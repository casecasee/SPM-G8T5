<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import { getProjects } from '../api/projects'
import { listTasks, createTask, updateTaskProject } from '../api/tasks'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.id))
const project = ref(null)
const loading = ref(false)
const error = ref('')
const allTasks = ref([])
const currentEmployeeId = Number(sessionStorage.getItem('employee_id')) || null
const activeTab = ref('all') // 'all' | 'mine'
const showAddModal = ref(false)

// Add/Attach state
const addTab = ref('create') // 'create' | 'attach'
const createTaskNow = ref(true)
const selectedExisting = ref([])
const taskForm = ref({
  title: '',
  description: '',
  deadline: '',
  priority: 5,
  collaborators: ''
})
const addBusy = ref(false)
const addError = ref('')
const searchExisting = ref('')

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

function statusClass(status) {
  switch ((status || '').toLowerCase()) {
    case 'ongoing': return 'status-pill status-ongoing'
    case 'under review': return 'status-pill status-review'
    case 'done': return 'status-pill status-completed'
    default: return 'status-pill status-default'
  }
}

function projectBadgeClass(s) {
  const k = (s || '').toLowerCase()
  return {
    'badge--active': k === 'active',
    'badge--on-hold': k === 'on hold',
    'badge--archived': k === 'archived'
  }
}

async function addTasksToProject() {
  if (addBusy.value) return
  addError.value = ''
  const ops = []
  const pid = projectId.value

  if (addTab.value === 'create' && createTaskNow.value) {
    const deadline = taskForm.value.deadline && taskForm.value.deadline.length === 16
      ? `${taskForm.value.deadline}:00`
      : taskForm.value.deadline
    const collaborators = (taskForm.value.collaborators || '')
      .split(',')
      .map(s => parseInt(s.trim(), 10))
      .filter(n => Number.isFinite(n))

    if (!taskForm.value.title?.trim()) {
      addError.value = 'Title is required.'
      return
    }
    if (!deadline) {
      addError.value = 'Deadline is required.'
      return
    }

    ops.push(
      createTask({
        title: taskForm.value.title.trim(),
        description: (taskForm.value.description || '').trim(),
        deadline,
        priority: Number(taskForm.value.priority) || 1,
        project_id: pid,
        collaborators,
        attachments: []
      })
    )
  }

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
    createTaskNow.value = true
    taskForm.value = { title: '', description: '', deadline: '', priority: 5, collaborators: '' }
    showAddModal.value = false
  } catch (_) {}
  finally {
    addBusy.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const list = await getProjects()
    project.value = list.find(p => p.id === projectId.value) || null
  } catch (e) {
    error.value = 'Failed to load project.'
  }
  try {
    allTasks.value = await listTasks()
  } catch (e) {
    // best-effort
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'projects' })
}

function openTask(t) {
  // Navigate to Tasks page; the Tasks view already handles details modal
  router.push({ name: 'tasks' })
}

onMounted(load)
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
        <div class="label">Status</div>
        <div class="value"><span class="badge" :class="projectBadgeClass(project.status)">{{ project.status }}</span></div>
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
        <div class="label">Last Updated</div>
        <div class="value">{{ formatDate(project.updatedAt) }}</div>
      </div>
    </div>
  </div>

  <div class="tasks-header">
    <h3 class="section-title">Tasks</h3>
    <Button v-if="canManage" label="+ Add Task" class="btn-primary" @click="showAddModal=true" />
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

    <div v-if="addTab==='create'">
      <div class="create-grid">
        <label>
          Title
          <input v-model="taskForm.title" class="input" placeholder="Task title" />
        </label>
        <label>
          Priority (1–10)
          <input type="number" min="1" max="10" v-model.number="taskForm.priority" class="input" />
        </label>
        <label class="full">
          Description
          <input v-model="taskForm.description" class="input" placeholder="What needs to be done" />
        </label>
        <label>
          Deadline
          <input type="datetime-local" v-model="taskForm.deadline" class="input" />
        </label>
        <label>
          Collaborators (IDs, comma-separated)
          <input v-model="taskForm.collaborators" class="input" placeholder="e.g. 2,3,34" />
        </label>
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
      <button class="btn btn-primary" @click="addTasksToProject" :disabled="addBusy">{{ addBusy ? 'Adding…' : 'Add' }}</button>
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
.badge--active { background:#d1fae5; color:#065f46; }
.badge--on-hold { background:#fef3c7; color:#92400e; }
.badge--archived { background:#e5e7eb; color:#374151; }
.section-title { margin:16px 0 8px; }
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
</style>

