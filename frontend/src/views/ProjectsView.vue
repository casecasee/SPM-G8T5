<template>
    <div class="projects-page">
        <div class="header-row">
            <h1>Projects</h1>

            <div class="header-actions">
                <input
                    v-model="search"
                    class="search"
                    type="search"
                    placeholder="Search projects"
                    :disabled="loading"
                />
                <button class="btn-primary" @click="openCreate" :disabled="loading">
                    Create Project
                </button>
            </div>
        </div>

        <div class="filters-row">
            <select v-model="owner" class="filter">
                <option value="">Owner</option>
                <option v-for="o in owners" :key="o" :value="o">{{ o }}</option>
            </select>

            <select v-model="status" class="filter">
                <option value="">Status</option>
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>

            <select v-model="sort" class="filter">
                <option value="updated_desc">Sort</option>
                <option value="updated_desc">Last updated (newest)</option>
                <option value="updated_asc">Last updated (oldest)</option>
                <option value="name_asc">Name A–Z</option>
                <option value="name_desc">Name Z–A</option>
            </select>
        </div>

        <div class="card">
            <table class="projects-table">
                <thead>
                    <tr>
                        <th>Project Name</th>
                        <th>Owner</th>
                        <th>Status</th>
                        <th>Tasks</th>
                        <th>Members</th>
                        <th>Due Date</th>
                        <th>Last Updated</th>
                    </tr>
                </thead>

                <tbody>
                    <tr v-if="loading">
                        <td colspan="7">Loading…</td>
                    </tr>

                    <tr v-else-if="!loading && filteredAndSorted.length === 0">
                        <td colspan="7">No projects found.</td>
                    </tr>

                    <tr v-for="p in filteredAndSorted" :key="p.id" @click="$router.push({ name: 'project-detail', params: { id: p.id } })" style="cursor:pointer;">
                        <td class="name">{{ p.name }} <span class="pid">#{{ p.id }}</span></td>
                        <td>{{ p.owner }}</td>
                        <td>
                            <span class="badge" :class="badgeClass(p.status)">
                                {{ p.status }}
                            </span>
                        </td>
                        <td>{{ p.tasksDone }} / {{ p.tasksTotal }}</td>
                        <td>{{ (p.memberNames && p.memberNames.length) ? p.memberNames.join(', ') : '-' }}</td>
                        <td>{{ formatDueDate(p.dueDate) }}</td>
                        <td>{{ fromNow(p.updatedAt) }}</td>
                    </tr>
                </tbody>
            </table>

            <!-- Removed archive footer -->
        </div>

        <!-- Create Project Modal -->
        <div v-if="showCreate" class="modal-overlay" @click.self.stop="cancelCreate">
            <div class="modal">
                <h2>Create Project</h2>
                <form @submit.prevent="submitCreate">
                    <label>
                        Name
                        <input v-model="form.name" required />
                    </label>

                    <label>
                        Owner
                        <input v-model="form.owner" disabled />
                    </label>

                    <label>
                        Status
                        <select v-model="form.status">
                            <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
                        </select>
                    </label>

                    <div class="row">
                        <label>
                            Tasks done (auto)
                            <input type="number" min="0" v-model.number="form.tasksDone" disabled />
                        </label>
                        <label>
                            Tasks total (auto)
                            <input type="number" min="0" v-model.number="form.tasksTotal" disabled />
                        </label>
                    </div>

                    <label>
                        Project Due Date
                        <input type="datetime-local" v-model="form.dueDate" />
                    </label>

                    <label>
                        Members
                        <div v-if="employees.length > 0" class="custom-multiselect">
                            <div 
                              class="multiselect-trigger"
                              @click="showDropdown = !showDropdown"
                              :class="{ 'open': showDropdown }"
                            >
                                <span v-if="form.memberIds.length === 0" class="placeholder">Select collaborators...</span>
                                <span v-else class="selected-count">{{ form.memberIds.length }} selected</span>
                                <span class="dropdown-arrow">▼</span>
                            </div>
                            <div v-if="showDropdown" class="multiselect-dropdown">
                                <div class="dropdown-header">
                                    <input 
                                      v-model="searchFilter" 
                                      placeholder="Search employees..." 
                                      class="search-input"
                                      @click.stop
                                    />
                                </div>
                                <div class="dropdown-options">
                                    <div 
                                      v-for="employee in filteredEmployees" 
                                      :key="employee.employee_id" 
                                      class="option-item"
                                      :class="{ 'selected': form.memberIds.includes(employee.employee_id) }"
                                      @click="toggleEmployee(employee.employee_id)"
                                    >
                                        <div class="checkbox">
                                            <div class="checkbox-inner" v-if="form.memberIds.includes(employee.employee_id)">✓</div>
                                        </div>
                                        <span class="option-text">{{ employee.display_label }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else>Loading employees...</div>
                    </label>

                    <!-- Attach Existing Tasks UI -->
                    <div v-if="isOwner">
                        <h4 style="margin: 16px 0 8px 0; font-weight: 600; color: #374151;">Attach existing tasks</h4>
                        <div v-if="tasksLoading">Loading tasks…</div>
                        <div v-else>
                            <div class="attach-toolbar">
                                <input class="search input" v-model="searchExisting" placeholder="Search tasks by title" />
                                <small class="muted">{{ unassignedTasks.length }} available</small>
                            </div>
                            <div class="attach-list">
                                <label v-for="t in unassignedTasks" :key="t.task_id" class="attach-item">
                                    <input type="checkbox" v-model="selectedExisting" :value="t.task_id" />
                                    <div class="attach-meta">
                                        <div class="attach-title">{{ t.title }}</div>
                                        <div class="attach-sub">ID: {{ t.task_id }}</div>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div v-if="isOwner" class="actions">
                        <button type="button" class="btn" @click="cancelCreate">Cancel</button>
                        <button type="submit" class="btn-primary">Save</button>
                    </div>

                    <p v-if="formError" class="error">{{ formError }}</p>
                </form>
            </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import MultiSelect from 'primevue/multiselect'
import { getProjects, createProject } from '../api/projects'
import { listTasks, updateTaskProject } from '../api/tasks'
import axios from 'axios'

const projects = ref([])
const loading = ref(false)
const error = ref('')

const search = ref('')
const owner = ref('')
const status = ref('')
const sort = ref('updated_desc')

const statuses = ['Active', 'On hold', 'Archived']

// Task selection/creation state
const tasksLoading = ref(false)
const allTasks = ref([])
const currentEmployeeId = Number(sessionStorage.getItem('employee_id')) || null
const unassignedTasks = computed(() => allTasks.value.filter(t => !t.project_id && Number(t.owner) === currentEmployeeId))
const selectedExisting = ref([])
const searchExisting = ref('')

const isOwner = computed(() => {
    const eid = Number(sessionStorage.getItem('employee_id')) || null
    return Number(form.ownerId || sessionStorage.getItem('employee_id')) === eid
})

// Employees for member dropdown
const employees = ref([])
const showDropdown = ref(false)
const searchFilter = ref('')

const employeeOptions = computed(() => {
  const options = (employees.value || []).map(e => ({
    ...e,
    display_label: `${e.employee_name} (#${e.employee_id})${e.role ? ' · ' + e.role : ''}${e.department ? ' · ' + e.department : ''}${e.team ? ' · ' + e.team : ''}`
  }))
  
  return options
})

const filteredEmployees = computed(() => {
  if (!searchFilter.value) return employeeOptions.value
  return employeeOptions.value.filter(emp => 
    emp.display_label.toLowerCase().includes(searchFilter.value.toLowerCase())
  )
})


function toggleEmployee(employeeId) {
  const index = form.memberIds.indexOf(employeeId)
  if (index > -1) {
    form.memberIds.splice(index, 1)
  } else {
    form.memberIds.push(employeeId)
  }
}


// Fetch employees for project collaborators (anyone can be invited)
async function fetchEmployees() {
  try {
    const res = await axios.get('http://localhost:5000/employees/all', { withCredentials: true })
    employees.value = Array.isArray(res.data) ? res.data : []
  } catch (error) {
    console.error('Error fetching employees:', error)
    employees.value = []
  }
}

const owners = computed(() => {
    const uniq = new Set(projects.value.map(p => p.owner).filter(Boolean))
    return Array.from(uniq).sort((a, b) => a.localeCompare(b))
})

function badgeClass(s) {
    const k = (s || '').toLowerCase()
    return {
        'badge--active': k === 'active',
        'badge--on-hold': k === 'on hold',
        'badge--archived': k === 'archived'
    }
}

function fromNow(iso) {
    const d = new Date(iso)
    const sec = Math.max(1, Math.floor((Date.now() - d.getTime()) / 1000))
    if (sec < 60) return 'just now'
    const min = Math.floor(sec / 60)
    if (min < 60) return `${min} minute${min > 1 ? 's' : ''} ago`
    const hr = Math.floor(min / 60)
    if (hr < 24) return `${hr} hour${hr > 1 ? 's' : ''} ago`
    const day = Math.floor(hr / 24)
    return `${day} day${day > 1 ? 's' : ''} ago`
}

function formatDueDate(dueDate) {
  if (!dueDate) return '-'
  const date = new Date(dueDate)
  const now = new Date()
  const diffTime = date - now
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) {
    return `${Math.abs(diffDays)} days overdue`
  } else if (diffDays === 0) {
    return 'Due today'
  } else if (diffDays === 1) {
    return 'Due tomorrow'
  } else {
    return `Due in ${diffDays} days`
  }
}

const filteredAndSorted = computed(() => {
    let list = projects.value.filter(p => {
        const q = search.value.trim().toLowerCase()
        const matchesSearch = !q || p.name.toLowerCase().includes(q)
        const matchesOwner = !owner.value || p.owner === owner.value
        const matchesStatus = !status.value || p.status === status.value
        return matchesSearch && matchesOwner && matchesStatus
    })

    switch (sort.value) {
        case 'updated_asc':
            list = list.sort((a, b) => new Date(a.updatedAt) - new Date(b.updatedAt))
            break
        case 'name_asc':
            list = list.sort((a, b) => a.name.localeCompare(b.name))
            break
        case 'name_desc':
            list = list.sort((a, b) => b.name.localeCompare(a.name))
            break
        default:
            list = list.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    }
    return list
})

async function load() {
    loading.value = true
    error.value = ''
    try {
        projects.value = await getProjects()
    } catch (e) {
        error.value = 'Failed to load from service. Showing demo data.'
        projects.value = [
            { id: 1, name: 'Marketing Campaign', owner: 'John Smith', status: 'Active',   tasksDone: 1, tasksTotal: 5,  updatedAt: new Date(Date.now() - 2 * 3600_000).toISOString() },
            { id: 2, name: 'Website Redesign',   owner: 'Mary Johnson', status: 'On hold', tasksDone: 2, tasksTotal: 8,  updatedAt: new Date(Date.now() - 24 * 3600_000).toISOString() },
            { id: 3, name: 'Mobile App Development', owner: 'Robert Brown', status: 'Active', tasksDone: 3, tasksTotal: 12, updatedAt: new Date(Date.now() - 3 * 24 * 3600_000).toISOString() },
            { id: 4, name: 'Data Analysis', owner: 'Susan Lee', status: 'Archived', tasksDone: 0, tasksTotal: 7, updatedAt: new Date(Date.now() - 5 * 24 * 3600_000).toISOString() },
        ]
    } finally {
        loading.value = false
    }
}

const showCreate = ref(false)
const formError = ref('')
const form = reactive({
    name: '',
    owner: '',
    status: 'Active',
    tasksDone: 0,
    tasksTotal: 0,
    members: '',        // legacy text field (unused after dropdown)
    memberIds: [],      // new dropdown selection
    dueDate: '',
})

async function openCreate() {
  form.name = ''
  form.owner = sessionStorage.getItem('employee_name') || 'Unassigned'
  form.status = 'Active'
  form.tasksDone = 0
  form.tasksTotal = 0
  form.memberIds = []
  formError.value = ''

  // Load unassigned tasks for attachment list
  selectedExisting.value = []
  tasksLoading.value = true
  listTasks().then(ts => { allTasks.value = ts || [] }).finally(() => { tasksLoading.value = false })
  
  // Fetch project employees
  await fetchEmployees()
  showCreate.value = true
}

function cancelCreate() {
    showCreate.value = false
    formError.value = ''
}

async function submitCreate() {
    if (!form.name.trim()) {
        formError.value = 'Name is required.'
        return
    }
    try {
        const payload = {
            name: form.name.trim(),
            owner: form.owner || 'Unassigned',
            ownerId: Number(sessionStorage.getItem('employee_id')) || null,
            status: form.status,
            // Backend initializes counters to 0; they update based on tasks
            tasksDone: 0,
            tasksTotal: 0,
            members: Array.isArray(form.memberIds) ? form.memberIds : [],
            dueDate: form.dueDate && form.dueDate.length === 16 ? `${form.dueDate}:00` : form.dueDate,
        }
        const created = await createProject(payload)
        projects.value.unshift(created)

        // After project creation, optionally attach existing tasks
        const ops = []

        if (selectedExisting.value.length) {
            for (const id of selectedExisting.value) {
                const t = allTasks.value.find(x => x.task_id === id)
                if (t) {
                    ops.push(updateTaskProject(id, created.id, t.owner))
                }
            }
        }

        await Promise.allSettled(ops)
        showCreate.value = false
    } catch (e) {
        formError.value = 'Create failed. Please try again.'
    }
}

async function onArchive() {
    const row = filteredAndSorted.value[0]
    if (!row) return
    const ok = window.confirm(`Archive "${row.name}"?`)
    if (!ok) return
    const prev = row.status
    row.status = 'Archived'
    try {
        await archiveProject(row.id)
    } catch (e) {
        row.status = prev
        error.value = 'Archive failed.'
    }
}

onMounted(async () => {
  await Promise.allSettled([load(), fetchEmployees()])
})
</script>

<style scoped>
.projects-page { padding: 24px; }

.header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.header-row h1 { margin: 0; font-size: 28px; }

.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.search {
    width: 320px;
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    outline: none;
}

.btn-primary {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 10px;
    cursor: pointer;
}
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

.filters-row {
    display: flex;
    gap: 12px;
    margin: 12px 0 16px;
}

.filter {
    padding: 8px 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    background: white;
}

.card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    overflow: hidden;
    background: white;
}

.projects-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}

.projects-table th, .projects-table td {
    padding: 14px 16px;
    border-bottom: 1px solid #f1f5f9;
    text-align: left;
}
.projects-table tr:last-child td { border-bottom: none; }
.projects-table tbody tr:hover { background: #f8fafc; }
.name { font-weight: 600; }
.pid { color:#9ca3af; font-weight:500; margin-left:6px; }

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
.badge--active   { background: #d1fae5; color: #065f46; }
.badge--on-hold  { background: #fef3c7; color: #92400e; }
.badge--archived { background: #e5e7eb; color: #374151; }

.table-footer {
    display: flex;
    justify-content: flex-end;
    padding: 12px 16px;
    border-top: 1px solid #f1f5f9;
}

.link { color: #2563eb; text-decoration: none; }
.error { color: #b91c1c; margin-top: 12px; }

/* Modal */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    overflow: visible !important; /* Allow dropdown to extend outside overlay */
}
.modal {
    background: #fff;
    width: 80vw;
    max-width: 1100px;
    min-width: 900px;
    max-height: 85vh;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    overflow: visible !important; /* Allow dropdown to extend outside modal */
    font-family: 'Segoe UI', sans-serif;
    margin: 2rem auto;
}

/* Ensure MultiSelect dropdown has proper z-index */
:deep(.p-multiselect-panel) {
    z-index: 9999 !important;
}

/* Alternative: if the above doesn't work, try this */
:deep(.p-multiselect) {
    z-index: 1000;
}

:deep(.p-multiselect-panel) {
    z-index: 1001;
}

.custom-multiselect {
  position: relative;
  width: 100%;
}

.multiselect-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  min-height: 40px;
}

.multiselect-trigger:hover {
  border-color: #9ca3af;
}

.multiselect-trigger.open {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.placeholder {
  color: #9ca3af;
}

.selected-count {
  color: #374151;
  font-weight: 500;
}

.dropdown-arrow {
  color: #6b7280;
  transition: transform 0.2s;
}

.multiselect-trigger.open .dropdown-arrow {
  transform: rotate(180deg);
}

.multiselect-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 200px;
  overflow: hidden;
}

.dropdown-header {
  padding: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.search-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

.dropdown-options {
  max-height: 150px;
  overflow-y: auto;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  gap: 10px;
  border-radius: 4px;
  margin: 2px 8px;
  transition: background-color 0.2s;
}

.option-item:hover {
  background: #f3f4f6;
}

.option-item.selected {
  background: #eff6ff;
  color: #1d4ed8;
}

.checkbox {
  width: 16px;
  height: 16px;
  border: 2px solid #d1d5db;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.option-item.selected .checkbox {
  background: #3b82f6;
  border-color: #3b82f6;
}

.checkbox-inner {
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.option-text {
  flex: 1;
  font-size: 14px;
}
.modal h2 { margin-top: 0; }
.modal form { 
    display: grid; 
    gap: 12px; 
    min-height: 500px;
    max-height: 72vh;
    overflow-y: auto;
    word-wrap: break-word;
    overflow-wrap: anywhere;
    white-space: normal;
    box-sizing: border-box;
}
.modal label { display: grid; gap: 6px; font-weight: 600; }
.modal input, .modal select {
    padding: 8px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
}
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.attach-toolbar { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:8px; }
.muted { color:#6b7280; }
.attach-list { display:flex; flex-direction:column; gap:6px; margin-top:8px; max-height:200px; overflow:auto; border:1px solid #e5e7eb; border-radius: var(--radius-md); padding:8px; }
.attach-item { display:flex; align-items:flex-start; gap:10px; padding:8px; border:1px solid #e5e7eb; border-radius: var(--radius-md); background:#fff; }
.attach-item:hover { background:#f8fafc; }
.attach-title { font-weight:600; }
.attach-sub { color:#6b7280; font-size:12px; }
.btn { background: #e5e7eb; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; }
</style>