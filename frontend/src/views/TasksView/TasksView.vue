<template src="./TasksView.template.html"></template>
<style scoped src="./TasksView.style.css"></style>

<script setup>
    import { ref, computed, onMounted, onUnmounted } from 'vue'
    import { getProjects } from '../../api/projects'
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

    // Comments state
    const comments = ref([])
    const newComment = ref('')
    const editingCommentId = ref(null)
    const editingContent = ref('')
    const commentError = ref('')

    // Mention suggestions
    const mentionable = ref([]) // [{employee_id, employee_name, role}]
    const showMentionList = ref(false)
    const mentionQuery = ref('')
    const mentionStartIdx = ref(-1)
    const filteredMentionable = computed(() => {
    const q = (mentionQuery.value || '').trim().toLowerCase()
    if (!q) return mentionable.value
    return (mentionable.value || []).filter(u => (u.employee_name || '').toLowerCase().includes(q))
    })

    const mentionHighlighted = ref(0)

    function onCommentInput(e) {
    const text = newComment.value || ''
    const cursor = e?.target?.selectionStart ?? text.length
    // find the last '@' before cursor that isn't preceded by whitespace
    let start = -1
    for (let i = cursor - 1; i >= 0; i--) {
        const ch = text[i]
        if (ch === '@') { start = i; break }
        if (ch === ' ' || ch === '\n' || ch === '\t') break
    }
    if (start >= 0) {
        mentionStartIdx.value = start
        mentionQuery.value = text.slice(start + 1, cursor)
        showMentionList.value = true
        mentionHighlighted.value = 0
    } else {
        hideMentionList()
    }
    }
    
    function printReport() {
        print();
        } 

    function hideMentionList() {
    showMentionList.value = false
    mentionQuery.value = ''
    mentionStartIdx.value = -1
    mentionHighlighted.value = 0
    }

    function moveMentionSelection(delta) {
    if (!showMentionList.value || filteredMentionable.value.length === 0) return
    const n = filteredMentionable.value.length
    mentionHighlighted.value = (mentionHighlighted.value + delta + n) % n
    }

    function applyMentionSelection() {
    if (!showMentionList.value || filteredMentionable.value.length === 0) return
    const user = filteredMentionable.value[mentionHighlighted.value]
    insertMention(user)
    }

    function insertMention(user) {
    const text = newComment.value || ''
    const start = mentionStartIdx.value
    if (start < 0) return
    const before = text.slice(0, start)
    const after = text.slice(start)
    // Replace the token starting at '@' up to next whitespace
    const match = after.match(/^@\S*/)
    const rest = match ? after.slice(match[0].length) : ''
    // Insert @{Employee Name} (the server supports names)
    const insertion = `@${user.employee_name}`
    newComment.value = before + insertion + (rest.startsWith(' ') ? rest : (' ' + rest))
    hideMentionList()
    }

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

    async function fetchTasks() {
    try {
        const res = await axios.get("http://localhost:5002/tasks", {
        withCredentials: true,
        // params: {
        //     eid: currentEmployeeId,
        //     role: currentRole
        // }
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
        await axios.post("http://localhost:5002/task", payload, { withCredentials: true })
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

    // Display labels for employee options (show role/team/department for HR & Senior Manager)
    const employeeDisplayList = computed(() => {
    const role = (currentRole || '').toLowerCase()
    const showMeta = role === 'senior manager' || role === 'hr'
    return (availableEmployees.value || []).map(emp => ({
        ...emp,
        display_label: showMeta
        ? `${emp.employee_name} [${[emp.role, emp.team, emp.department].filter(Boolean).join(' • ')}]`
        : emp.employee_name
    }))
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
    // Load comments for this task
    loadComments(task.id)
    // Load mentionable users for this task
    loadMentionable(task.id)
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

    // ----------------- Comments API -----------------
    async function loadComments(taskId) {
    comments.value = []
    try {
        const res = await axios.get(`http://localhost:5002/task/${taskId}/comments`, { withCredentials: true })
        comments.value = Array.isArray(res.data) ? res.data : []
    } catch (err) {
        comments.value = []
    }
    }

    async function loadMentionable(taskId) {
    mentionable.value = []
    try {
        const res = await axios.get(`http://localhost:5002/task/${taskId}/mentionable`, { withCredentials: true })
        mentionable.value = Array.isArray(res.data) ? res.data : []
    } catch (_) {
        mentionable.value = []
    }
    }

    async function addComment() {
    const taskId = selectedTask.value?.id
    if (!taskId) return
    const content = (newComment.value || '').trim()
    if (!content) return
    try {
        commentError.value = ''
        await axios.post(`http://localhost:5002/task/${taskId}/comments`, { content }, { withCredentials: true })
        newComment.value = ''
        await loadComments(taskId)
    } catch (e) {
        try {
        const msg = (e?.response?.data?.message || '').toString()
        commentError.value = msg || 'Failed to add comment'
        } catch {
        commentError.value = 'Failed to add comment'
        }
    }
    }

    function startEditComment(comment) {
    editingCommentId.value = comment.id
    editingContent.value = comment.content
    }

    function cancelEditComment() {
    editingCommentId.value = null
    editingContent.value = ''
    }

    async function saveEditComment(commentId) {
    const content = (editingContent.value || '').trim()
    if (!content) return
    try {
        commentError.value = ''
        await axios.put(`http://localhost:5002/comments/${commentId}`, { content }, { withCredentials: true })
        editingCommentId.value = null
        editingContent.value = ''
        if (selectedTask.value?.id) await loadComments(selectedTask.value.id)
    } catch (e) {
        try {
        const msg = (e?.response?.data?.message || '').toString()
        commentError.value = msg || 'Failed to update comment'
        } catch {
        commentError.value = 'Failed to update comment'
        }
    }
    }

    async function deleteComment(commentId) {
    try {
        await axios.delete(`http://localhost:5002/comments/${commentId}`, { withCredentials: true })
        if (selectedTask.value?.id) await loadComments(selectedTask.value.id)
    } catch (_) {}
    }
</script>