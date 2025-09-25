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
                        <th>Last Updated</th>
                    </tr>
                </thead>

                <tbody>
                    <tr v-if="loading">
                        <td colspan="6">Loading…</td>
                    </tr>

                    <tr v-else-if="!loading && filteredAndSorted.length === 0">
                        <td colspan="6">No projects found.</td>
                    </tr>

                    <tr v-for="p in filteredAndSorted" :key="p.id">
                        <td class="name">{{ p.name }}</td>
                        <td>{{ p.owner }}</td>
                        <td>
                            <span class="badge" :class="badgeClass(p.status)">
                                {{ p.status }}
                            </span>
                        </td>
                        <td>{{ p.tasksDone }} / {{ p.tasksTotal }}</td>
                        <td>{{ (p.memberNames && p.memberNames.length) ? p.memberNames.join(', ') : '-' }}</td>
                        <td>{{ fromNow(p.updatedAt) }}</td>
                    </tr>
                </tbody>
            </table>

            <div class="table-footer">
                <a href="#" @click.prevent="onArchive" class="link">Archive</a>
            </div>
        </div>

        <!-- Create Project Modal -->
        <div v-if="showCreate" class="modal-overlay" @click.self="cancelCreate">
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
                            Tasks done
                            <input type="number" min="0" v-model.number="form.tasksDone" />
                        </label>
                        <label>
                            Tasks total
                            <input type="number" min="0" v-model.number="form.tasksTotal" />
                        </label>
                    </div>

                    <label>
                        Members (IDs, comma-separated)
                        <input v-model="form.members" placeholder="e.g. 1,2,3" />
                    </label>

                    <div class="actions">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { getProjects, createProject, archiveProject } from '../api/projects'

const projects = ref([])
const loading = ref(false)
const error = ref('')

const search = ref('')
const owner = ref('')
const status = ref('')
const sort = ref('updated_desc')

const statuses = ['Active', 'On hold', 'Archived']

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
    members: '',
})

function openCreate() {
    form.name = ''
    form.owner = sessionStorage.getItem('employee_name') || 'Unassigned'
    form.status = 'Active'
    form.tasksDone = 0
    form.tasksTotal = 0
    formError.value = ''
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
            tasksDone: Number(form.tasksDone) || 0,
            tasksTotal: Number(form.tasksTotal) || 0,
            members: (form.members || '')
                .split(',')
                .map(s => parseInt(s.trim(), 10))
                .filter(n => Number.isFinite(n)),
        }
        const created = await createProject(payload)
        projects.value.unshift(created)
        // Optionally clear filters so new item is visible:
        // search.value = ''; owner.value = ''; status.value = ''; sort.value = 'updated_desc'
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

onMounted(load)
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
}
.modal {
    background: #fff;
    width: 520px;
    max-width: 90vw;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.modal h2 { margin-top: 0; }
.modal form { display: grid; gap: 12px; }
.modal label { display: grid; gap: 6px; font-weight: 600; }
.modal input, .modal select {
    padding: 8px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
}
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.btn { background: #e5e7eb; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; }
</style>