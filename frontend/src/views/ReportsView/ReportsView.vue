<template src="./ReportsView.template.html"></template>
<style src="./ReportsView.style.css"></style>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
    import { getProjects } from '../../api/projects'
    import Dialog from 'primevue/dialog'
    import Button from 'primevue/button'
    import Card from 'primevue/card'
    import InputText from 'primevue/inputtext'
    import Textarea from 'primevue/textarea'
    import Dropdown from 'primevue/dropdown'
    import FileUpload from 'primevue/fileupload'
    import MultiSelect from 'primevue/multiselect'
    import axios from 'axios'

const router = useRouter()
const route = useRoute()

          
    // ----------------- State -----------------
    const tasks = ref([]) // my tasks
    const teamTasksData = ref({}) // team tasks organized by employee name
    const companyTasksData = ref({}) 
    const projects = ref([])
    const currentTab = ref('individual_report')
    const teamSearch = ref('')
    const teamSelectedEmployeeId = ref(null)
    const selectedTask = ref(null)
    const showModal = ref(false)
    const isEditing = ref(false)
    const availableEmployees = ref([])
    const assignmentEmployees = ref([]) 
    const fileUploadRef = ref(null)

    // Filter state
    const taskFilter = ref('all') // 'all', 'ongoing', 'overdue', 'completed'

    // Comments state
    const comments = ref([])
    const newComment = ref('')
    const newCommentAttachments = ref([])
    const editingCommentId = ref(null)
    const editingContent = ref('')
    const commentError = ref('')

    // Form validation state
    const formErrors = ref({})
    const showValidationErrors = ref(false)
    

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

    //running on comment input
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

    function goToTimeline() {
        router.push({ name: 'tasks-timeline' })
    }

    function hideMentionList() {
    showMentionList.value = false
    mentionQuery.value = ''
    mentionStartIdx.value = -1
    mentionHighlighted.value = 0
    }

    // If came from project page/timeline, go back when modal closes
    watch(showModal, (v) => {
        if (!v && route.query.from === 'project-timeline' && route.query.projectId) {
            router.push({ name: 'project-timeline', params: { id: Number(route.query.projectId) } })
        } else if (!v && route.query.from === 'project' && route.query.projectId) {
            router.push({ name: 'project-detail', params: { id: Number(route.query.projectId) } })
        }
    })

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

    function handleCommentEnter(event) {
        // Always prevent form submission
        event.preventDefault()
        
        // If mention list is shown, apply selection
        if (showMentionList.value && filteredMentionable.value.length > 0) {
            applyMentionSelection()
        }
        // Otherwise, do nothing (don't submit the form)
    }

    function insertMention(user) {
    const text = newComment.value || ''
    const start = mentionStartIdx.value
    if (start < 0) return
    const before = text.slice(0, start)
    const after = text.slice(start)
    const match = after.match(/^@\S*/)
    const rest = match ? after.slice(match[0].length) : ''
    const insertion = `@${user.employee_name}`
    newComment.value = before + insertion + (rest.startsWith(' ') ? rest : (' ' + rest))
    hideMentionList()
    }

    // Department view state
    const departments = ref([])
    const selectedDepartment = ref(null)
   
    const departmentSearch = ref('')
    const departmentSelectedEmployeeId = ref(null) 

    // Logged-in user info
    const currentEmployeeId = Number(sessionStorage.getItem("employee_id"))
    const currentRole = sessionStorage.getItem("role")
    const currentEmployeeName = sessionStorage.getItem("employee_name")
    const currentDep = sessionStorage.getItem("department")
    const currentTeam = sessionStorage.getItem("team")

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

    const recurrenceUnitOptions = [
        { label: 'No recurrence', value: 'none' },
        { label: 'Daily', value: 'day' },
        { label: 'Weekly', value: 'week' },
        { label: 'Monthly', value: 'month' },
        { label: 'Yearly', value: 'year' }
    ]

    const filterOptions = computed(() => {
        const baseOptions = [
            { label: 'All Tasks', value: 'all' },
            { label: 'Ongoing', value: 'ongoing' },
            { label: 'Under Review', value: 'under_review' },
            { label: 'Overdue', value: 'overdue' },
            { label: 'Done', value: 'completed' },
            { label: 'Recurring', value: 'recurring' }
        ]
        
        const role = (currentRole || '').toLowerCase()
        if (role === 'manager' || role === 'senior manager' || role === 'director') {
            baseOptions.splice(2, 0, { label: 'Unassigned', value: 'unassigned' })
        }
        
        return baseOptions
    })

    const taskForm = ref(resetForm())

    // Subtasks state
    const subtasks = ref([])
    const newSubtask = ref({
    name: '',
    description: '',
    due_date: null,
    status: 'ongoing',
    priority: null,
    owner: currentEmployeeId,
    collaborators: [],
    attachments: []
    })
    const showSubtaskForm = ref(false)
    const subtaskFileUploadRef = ref(null)
    const subtaskEditFileUploadRef = ref(null)
    const editingSubtaskId = ref(null)
    const editingSubtaskBackup = ref(null)

    function resetForm() {
    const defaultStatus = (currentRole || '').toLowerCase() === 'staff' ? 'ongoing' : 'unassigned'
    
    return {
        id: null,
        name: '',
        description: '',
        due_date: null,
        status: defaultStatus,
        priority: null,
        owner: currentEmployeeId, 
        collaborators: [], 
        project_id: null,
        attachments: [],
        recurrence_unit: 'none',
        recurrence_frequency: 1
    }
    }

    function resetSubtaskForm() {
    const parentCollaborators = [
        taskForm.value.owner,
        ...(Array.isArray(taskForm.value.collaborators) ? taskForm.value.collaborators : [])
    ].filter((id, index, self) => self.indexOf(id) === index) // Remove duplicates
    
    // figure out the default status based on PARENT TASK OWNER's role
    const parentOwner = (availableEmployees.value || []).find(emp => emp.employee_id === taskForm.value.owner)
    const parentOwnerRole = parentOwner ? (parentOwner.role || '').toLowerCase() : 'manager'
    const defaultStatus = parentOwnerRole === 'staff' ? 'ongoing' : 'unassigned'
    
    return {
        name: '',
        description: '',
        due_date: null,
        status: defaultStatus,
        priority: 5,
        owner: currentEmployeeId,
        collaborators: parentCollaborators,  
        project_id: null,
        attachments: []
    }
    }

    function validateSubtaskForm() {
    const errors = {}
    
    if (!newSubtask.value.name || (typeof newSubtask.value.name === 'string' && newSubtask.value.name.trim() === '')) {
        errors.subtask_name = 'Subtask name is required'
    }
    
    if (!newSubtask.value.description || (typeof newSubtask.value.description === 'string' && newSubtask.value.description.trim() === '')) {
        errors.subtask_description = 'Subtask description is required'
    }
    
    if (!newSubtask.value.due_date) {
        errors.subtask_due_date = 'Subtask deadline is required'
    }
    
    if (!newSubtask.value.priority || newSubtask.value.priority === null || newSubtask.value.priority === '') {
        errors.subtask_priority = 'Subtask priority is required'
    }
    
    if (!newSubtask.value.owner || newSubtask.value.owner === null || newSubtask.value.owner === '') {
        errors.subtask_owner = 'Subtask must be assigned to someone'
    }
    
    if (newSubtask.value.due_date) {
        const dueDate = new Date(newSubtask.value.due_date)
        const now = new Date()
        if (dueDate < now) {
            errors.subtask_due_date = 'Subtask deadline must be in the future'
        }
        
        if (taskForm.value.due_date) {
            const subtaskDate = new Date(newSubtask.value.due_date)
            const parentDate = new Date(taskForm.value.due_date)
            if (subtaskDate > parentDate) {
                errors.subtask_due_date = 'Subtask deadline cannot be after parent task deadline'
            }
        }
    }
    
    formErrors.value = errors
    showValidationErrors.value = Object.keys(errors).length > 0
    
    return Object.keys(errors).length === 0
    }

    function addSubtask() {
    clearValidationErrors()
    
    console.log('Validating subtask:', newSubtask.value)
    
    if (!validateSubtaskForm()) {
        console.log('Validation failed. Errors:', formErrors.value)
        return
    }
    
    console.log('Validation passed. Adding subtask.')
    subtasks.value.push({
        ...newSubtask.value 
    })
    newSubtask.value = resetSubtaskForm()
    showSubtaskForm.value = false
    clearValidationErrors()
    }

    function toggleSubtaskForm() {
    showSubtaskForm.value = !showSubtaskForm.value
    if (showSubtaskForm.value) {
        // Reset form when opening
        newSubtask.value = resetSubtaskForm()
        clearValidationErrors()
    } else {
        newSubtask.value = resetSubtaskForm()
        clearValidationErrors()
    }
    }

    async function handleSubtaskAttachment(event) {
    await handleAttachmentWithUpload(event, newSubtask.value.attachments, subtaskFileUploadRef.value)
    }

    function removeSubtaskAttachment(index) {
    removeAttachment(index, newSubtask.value.attachments)
    }

    async function handleSubtaskEditAttachment(event) {
    const editingSubtask = subtasks.value.find(s => 
        (s.id && s.id === editingSubtaskId.value) || 
        subtasks.value.indexOf(s) === editingSubtaskId.value
    )
    if (editingSubtask) {
        if (!editingSubtask.attachments) {
            editingSubtask.attachments = []
        }
        await handleAttachmentWithUpload(event, editingSubtask.attachments, subtaskEditFileUploadRef.value)
    }
    }

    function removeSubtaskEditAttachment(index) {
    const editingSubtask = subtasks.value.find(s => 
        (s.id && s.id === editingSubtaskId.value) || 
        subtasks.value.indexOf(s) === editingSubtaskId.value
    )
    if (editingSubtask && editingSubtask.attachments) {
        removeAttachment(index, editingSubtask.attachments)
    }
    }
    


    async function updateSubtaskStatus(subtask, newStatus) {
    // If subtask already exists (has id), update via API
    if (subtask.id) {
        try {
            await axios.patch(`http://localhost:5002/task/status/${subtask.id}`, { 
                status: newStatus, 
                employee_id: currentEmployeeId 
            }, { withCredentials: true })
            subtask.status = newStatus
        } catch (error) {
            console.error("Error updating subtask status:", error)
            
            const backendMessage = error.response?.data?.message || 'Error updating subtask status'
            
            formErrors.value = { backend: backendMessage }
            showValidationErrors.value = true
            
            const modalContent = document.querySelector('.modal-content')
            if (modalContent) {
                modalContent.scrollTo({ top: 0, behavior: 'smooth' })
            }
        }
    } else {
        subtask.status = newStatus
    }
    }

    function startEditingSubtask(subtask) {
    editingSubtaskId.value = subtask.id || subtasks.value.indexOf(subtask)
    editingSubtaskBackup.value = JSON.parse(JSON.stringify(subtask))
    }

    function cancelEditingSubtask() {
    if (editingSubtaskBackup.value) {
        const index = subtasks.value.findIndex(s => 
            (s.id && s.id === editingSubtaskId.value) || 
            subtasks.value.indexOf(s) === editingSubtaskId.value
        )
        if (index !== -1) {
            subtasks.value[index] = editingSubtaskBackup.value
        }
    }
    editingSubtaskId.value = null
    editingSubtaskBackup.value = null
    }

    function saveEditingSubtask(subtask) {
    editingSubtaskId.value = null
    editingSubtaskBackup.value = null
    }

    function isEditingSubtask(subtask) {
    return editingSubtaskId.value === (subtask.id || subtasks.value.indexOf(subtask))
    }

    function canEdit(task) {
    if (!task) return true 
    
    if (currentTab.value === 'departments' && task.owner !== currentEmployeeId) {
        return false
    }
    
    if (currentTab.value === 'team' && task.owner !== currentEmployeeId) {
        return false
    }
    
    return isOwner(task)
    }

    function canAssignTasks() {
    const role = (currentRole || '').toLowerCase()
    return role === 'manager' || role === 'director' || role === 'senior manager'
    }

    function canAssignOwners() {
    const role = (currentRole || '').toLowerCase()
    return role === 'manager' || role === 'director' || role === 'senior manager'
    }

    const isManagerRole = computed(() => (currentRole || '').toLowerCase() !== 'staff')
    const canViewTeamTasks = computed(() => {
    const role = (currentRole || '').toLowerCase()
    return role === 'manager' || role === 'staff'
    })
    const isSeniorManagerOrHR = computed(() => {
    const role = (currentRole || '').toLowerCase()
    const dept = (currentDep || '')
    return role === 'senior manager' || dept === 'HR' || role === 'director'
    })

    const myTasks = computed(() => {
    const collabIncludes = (task) => Array.isArray(task.collaborators) && task.collaborators.includes(currentEmployeeId)
    return (tasks.value || []).filter(task => task.owner === currentEmployeeId || collabIncludes(task))
    })

    const displayTasks = computed(() => {
    let filteredTasks = []
    
    if (currentTab.value === 'team' || currentTab.value === 'dept_report' ) {
        if (!teamSelectedEmployeeId.value) return []
        const targetId = Number(teamSelectedEmployeeId.value)
        if (targetId === currentEmployeeId) return []
        
        const selectedEmployee = availableEmployees.value.find(emp => emp.employee_id === targetId)
        if (!selectedEmployee) return []
        
        filteredTasks = teamTasksData.value[selectedEmployee.employee_name] || []
    } else if (currentTab.value === 'departments') {
        if (!departmentSelectedEmployeeId.value) return []
        const targetId = Number(departmentSelectedEmployeeId.value)
        if (targetId === currentEmployeeId) return myTasks.value
        
        // Find the employee name for the selected employee ID
        const selectedEmployee = departmentEmployees.value.find(emp => emp.employee_id === targetId)
        if (!selectedEmployee) return []
        
        // Get tasks for the selected employee from companyTasksData
        const deptName = selectedEmployee.department
        const teamName = selectedEmployee.team
        const employeeName = selectedEmployee.employee_name
        
        if (companyTasksData.value[deptName] && 
            companyTasksData.value[deptName][teamName] && 
            companyTasksData.value[deptName][teamName][employeeName]) {
            filteredTasks = companyTasksData.value[deptName][teamName][employeeName]
        } else {
            filteredTasks = []
        }
    } else {
        // 'my' tab - show my tasks
        filteredTasks = myTasks.value
    }
    
    // Apply status filter
    if (taskFilter.value !== 'all') {
        filteredTasks = filteredTasks.filter(task => {
            if (taskFilter.value === 'ongoing') {
                return task.status === 'ongoing'
            } else if (taskFilter.value === 'unassigned') {
                return task.status === 'unassigned'
            } else if (taskFilter.value === 'under_review') {
                return task.status === 'under review'
            } else if (taskFilter.value === 'overdue') {
                return isOverdue(task)
            } else if (taskFilter.value === 'completed') {
                return task.status === 'done'
            } else if (taskFilter.value === 'recurring') {
                return task.recurrence && task.recurrence > 0
            }
            return true
        })
    }
    
    return filteredTasks.sort((a, b) => {
        const priorityA = a.priority || 5
        const priorityB = b.priority || 5
        return priorityB - priorityA
    })
    })
    

const tasksByPriority = computed(() => {
  // Only show the user's visible tasks
  const visibleTasks = displayTasks.value

  // Sort by priority score first, then due date (ascending)
  const sortedTasks = [...visibleTasks].sort((a, b) => {
    const priorityA = a.priority || 5
    const priorityB = b.priority || 5

    if (priorityA === priorityB) {
      const dateA = new Date(a.due_date)
      const dateB = new Date(b.due_date)
      return dateA - dateB // earliest due date first
    }

    // Higher priority first
    return priorityB - priorityA
  })

  const groups = {
    high: [],
    medium: [],
    low: []
  }

  sortedTasks.forEach(task => {
    const score = task.priority || 5
    if (score >= 8) groups.high.push(task)
    else if (score >= 5) groups.medium.push(task)
    else groups.low.push(task)
  })

  return groups
})



// ------------------------------------Individual Report-----------------------------------------------------------------

const report_displayTasks = computed(() => {
  // 1️⃣ Start with only user's tasks
  let filteredTasks = myTasks.value

  // 2️⃣ Prepare date range
  const start = startDate.value ? new Date(startDate.value) : null
  const end = endDate.value ? new Date(endDate.value) : null

  if (start && end) {
    filteredTasks = filteredTasks.filter(t => {
      if (!t.created_at || !t.due_date) return false

      const created = new Date(t.created_at)
      const due = new Date(t.due_date)
      if (isNaN(created) || isNaN(due)) return false

      // ✅ Include tasks that *overlap* with the range
      // Meaning: task started before the end date AND ends after the start date
      return created <= end && due >= start
    })
  }

  // 3️⃣ Sort: higher priority first, then earliest due date
  return filteredTasks.sort((a, b) => {
    const pA = a.priority || 5
    const pB = b.priority || 5
    if (pA === pB) return new Date(a.due_date) - new Date(b.due_date)
    return pB - pA
  })
})



const report_tasksByPriority = computed(() => {
  const tasks = report_displayTasks.value
  const groups = { high: [], medium: [], low: [] }

  tasks.forEach(task => {
    const score = task.priority || 5
    if (score >= 8) groups.high.push(task)
    else if (score >= 5) groups.medium.push(task)
    else groups.low.push(task)
  })

  return groups
})

const report_overdueTasks = computed(() => 
  report_displayTasks.value.filter(t => isOverdue(t))
)

const report_overallProgress = computed(() => {
  const total = report_displayTasks.value.length
  if (total === 0) return 'Nil'

  const overdueCount = report_overdueTasks.value.length
  if (overdueCount === 0) return 'Good'
  if (overdueCount === 1) return 'Average'
  return 'Poor'
})





// ----------------- Department Report Logic -----------------------------------------------------------------------------------------------------------------------

// -------------------- Department Report Logic --------------------
const showDeptFilterMenu = ref(false)
const deptFilterByEmployee = ref(false)
const deptFilterByTask = ref(true)
const deptSelectedEmployeeIds = ref([])
const deptStartDate = ref(null)
const deptEndDate = ref(null)

const departmentEmployees = ref([]) // employees in currentDep
const dept_displayTasks = ref([])

watch(currentTab, (newTab) => {
  if (newTab === 'dept_report') loadDeptReport()
})

// 1️⃣ load all dept employees & tasks initially
function loadDeptReport() {
  const all = availableEmployees.value || []
  departmentEmployees.value = all.filter(
    (emp) => emp.department === currentDep
  )

  // collect all department tasks
  let collected = []
  departmentEmployees.value.forEach((emp) => {
    const empTasks = teamTasksData.value[emp.employee_name] || []
    collected.push(...empTasks)
  })

  // ✅ Default date range: last 30 days (or within current month)
  const today = new Date()
  const oneMonthAgo = new Date(today)
  oneMonthAgo.setMonth(today.getMonth() - 1)

  deptStartDate.value = oneMonthAgo.toISOString().split('T')[0]
  deptEndDate.value = today.toISOString().split('T')[0]

  // ✅ Apply the date filter by default
  const start = new Date(deptStartDate.value)
  const end = new Date(deptEndDate.value)

  const filtered = collected.filter((t) => {
    if (!t.created_at || !t.due_date) return false
    const created = new Date(t.created_at)
    const due = new Date(t.due_date)
    return created <= end && due >= start
  })

  dept_displayTasks.value = filtered.sort(sortByPriorityAndDate)
  deptSelectedEmployeeIds.value = departmentEmployees.value.map(
    (e) => e.employee_id
  )
}


// 2️⃣ toggle filter menu
function toggleDeptFilterMenu() {
  showDeptFilterMenu.value = !showDeptFilterMenu.value
}


function sortByPriorityAndDate(a, b) {
  const pA = a.priority || 5
  const pB = b.priority || 5
  if (pA === pB) return new Date(a.due_date) - new Date(b.due_date)
  return pB - pA
}

// 4️⃣ computed groupings
const dept_tasksByPriority = computed(() => {
  const tasks = dept_displayTasks.value
  const groups = { high: [], medium: [], low: [] }
  tasks.forEach((t) => {
    const score = t.priority || 5
    if (score >= 8) groups.high.push(t)
    else if (score >= 5) groups.medium.push(t)
    else groups.low.push(t)
  })
  return groups
})

const dept_overdueTasks = computed(() =>
  dept_displayTasks.value.filter((t) => isOverdue(t))
)

const formattedDeptDateRange = computed(() => {
  const options = { day: 'numeric', month: 'long', year: 'numeric' }

  if (!deptStartDate.value && !deptEndDate.value) {
    // fallback (shouldn't occur now since defaults are set)
    return 'All time'
  }

  const s = deptStartDate.value
    ? new Date(deptStartDate.value).toLocaleDateString('en-SG', options)
    : '—'
  const e = deptEndDate.value
    ? new Date(deptEndDate.value).toLocaleDateString('en-SG', options)
    : '—'

  return `${s} - ${e}`
})

const dept_overallProgress = computed(() => {
  const total = dept_displayTasks.value.length
  if (total === 0) return 'Nil'

  const overdueCount = dept_overdueTasks.value.length
  console.log(overdueCount)
  if (overdueCount === 0) return 'Good'
  if (overdueCount === 1) return 'Average'
  return 'Poor'
})

// new reactive variable
const dept_employeeReports = ref([])

function applyDeptFilters() {
  let filtered = []
  dept_employeeReports.value = [] // reset multi-report view

  // ✅ If filter by employee and multiple are selected
  if (deptFilterByEmployee.value && deptSelectedEmployeeIds.value.length) {
    deptSelectedEmployeeIds.value.forEach((empId) => {
      const emp = departmentEmployees.value.find(
        (e) => e.employee_id === empId
      )
      if (!emp) return

      let empTasks = teamTasksData.value[emp.employee_name] || []

      // date filtering
      const start = deptStartDate.value ? new Date(deptStartDate.value) : null
      const end = deptEndDate.value ? new Date(deptEndDate.value) : null
      if (start && end) {
        empTasks = empTasks.filter((t) => {
          if (!t.created_at || !t.due_date) return false
          const created = new Date(t.created_at)
          const due = new Date(t.due_date)
          return created <= end && due >= start
        })
      }

      // sort
      empTasks = empTasks.sort(sortByPriorityAndDate)

      // push to employee reports list
      dept_employeeReports.value.push({
        employee: emp,
        tasks: empTasks,
      })

      filtered.push(...empTasks)
    })

    // still maintain master task list
    dept_displayTasks.value = filtered.sort(sortByPriorityAndDate)
  } else {
    // ✅ If not filtering by employee → show all dept tasks
    let collected = []
    departmentEmployees.value.forEach((emp) => {
      const empTasks = teamTasksData.value[emp.employee_name] || []
      collected.push(...empTasks)
    })

    // date filtering
    const start = deptStartDate.value ? new Date(deptStartDate.value) : null
    const end = deptEndDate.value ? new Date(deptEndDate.value) : null

    if (start && end) {
      collected = collected.filter((t) => {
        if (!t.created_at || !t.due_date) return false
        const created = new Date(t.created_at)
        const due = new Date(t.due_date)
        return created <= end && due >= start
      })
    }

    dept_displayTasks.value = collected.sort(sortByPriorityAndDate)
    dept_employeeReports.value = [] // no multi-view
  }

  showDeptFilterMenu.value = false
}

function groupTasksByPriority(taskList) {
  const groups = { high: [], medium: [], low: [] }
  taskList.forEach((t) => {
    const score = t.priority || 5
    if (score >= 8) groups.high.push(t)
    else if (score >= 5) groups.medium.push(t)
    else groups.low.push(t)
  })
  return groups
}

// ------------------------------------SubTasks-----------------------------------------------------------------

function hasTasksInSection(section) {
  const groups = report_tasksByPriority.value
  return groups[section] && groups[section].length > 0
}


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

    const minDate = computed(() => {
    return new Date().toISOString().slice(0, 16)  
    })

    const subtaskMinDate = computed(() => {
    return new Date().toISOString().slice(0, 16)  
    })

    const subtaskMaxDate = computed(() => {
    return taskForm.value.due_date 
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
    
    const filteredStatusOptions = computed(() => {
    const role = (sessionStorage.getItem('role') || '').toLowerCase();
    if (role === 'staff') {
        return statusOptions.filter(opt => opt.value !== 'unassigned');
    }
    return statusOptions;
    });

    // For viewing existing tasks, show all status options except unassigned for staff
    const allStatusOptions = computed(() => {
        const role = (sessionStorage.getItem('role') || '').toLowerCase();
        if (role === 'staff') {
            return statusOptions.filter(opt => opt.value !== 'unassigned');
        }
        return statusOptions;
    });

    // Function to get status options for a specific task (includes current status even if filtered)
    function getStatusOptionsForTask(task) {
        const role = (sessionStorage.getItem('role') || '').toLowerCase();
        let options = [...statusOptions];
        
        if (role === 'staff') {
            options = statusOptions.filter(opt => opt.value !== 'unassigned');
            
            if (task && task.status === 'unassigned') {
                options.push({ label: 'Unassigned', value: 'unassigned' });
            }
        }
        return options;
    }

    // Function to get status options for a specific subtask (includes current status even if filtered)
    function getStatusOptionsForSubtask(subtask) {
        const role = (sessionStorage.getItem('role') || '').toLowerCase();
        let options = [...statusOptions];
        
        if (role === 'staff') {
            options = statusOptions.filter(opt => opt.value !== 'unassigned');
            
            if (subtask && subtask.status === 'unassigned') {
                options.push({ label: 'Unassigned', value: 'unassigned' });
            }
        }
        return options;
    }

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

    // Separate function for getting employees for task assignment
    async function fetchEmployeesForAssignment() {
    try {
        const role = (currentRole || '').toLowerCase()
        const dept = (currentDep || '').toLowerCase()
        
        if (role === 'senior manager' || role === 'director') {
        // Senior managers and directors can only see employees in their department
        const depRaw = sessionStorage.getItem("department") || ""
        console.log('Fetching employees for department:', depRaw)
        const res = await axios.get(`http://localhost:5000/employees/${encodeURIComponent(depRaw)}`, { withCredentials: true })
        console.log('Department employees response:', res.data)
        return Array.isArray(res.data) ? res.data : []
        } else {
        // For managers and staff, use the existing availableEmployees (team members)
        return availableEmployees.value || []
        }
    } catch (err) {
        console.error("Error fetching employees for assignment:", err)
        return []
    }
    }

    async function fetchEmployees() {
    try {
        const role = (currentRole || '').toLowerCase()
        if (role === 'senior manager' || role === 'hr' || role === 'director') {
        const res = await axios.get("http://localhost:5000/employees/all", { withCredentials: true })
        availableEmployees.value = Array.isArray(res.data) ? res.data : []
        } else {
        // For managers and staff, fetch team members
        const depRaw = sessionStorage.getItem("department") || ""
        const teamRaw = sessionStorage.getItem("team") || ""
        const res = await axios.get(`http://localhost:5000/employees/department/${encodeURIComponent(depRaw)}/team/${encodeURIComponent(teamRaw)}`, { withCredentials: true })
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

        })
        console.log("API Response:", res.data)
        
        // Helper function to transform task data
        const transformTask = (t) => {
            let attachments = []
            if (t.attachment) {
                try {
                const parsed = JSON.parse(t.attachment)
                attachments = Array.isArray(parsed) ? parsed.map(filename => ({
                    name: filename.split(/[/\\]/).pop() || "File",
                    url: `http://localhost:5002/attachments/${filename}`
                })) : []
                } catch (e) {
                attachments = [{
                    name: t.attachment.split(/[/\\]/).pop() || "File",
                    url: `http://localhost:5002/attachments/${t.attachment}`
                }]
                }
            }

            const toLocal = iso => {
            if (!iso) return null
            // Handle both ISO format and MySQL DATETIME format
            let date
            if (iso.includes('T')) {
                // ISO format: "2025-10-30T15:18:00.000Z"
                date = new Date(iso)
            } else {
                // MySQL DATETIME format: "2025-10-30 15:18:00"
                date = new Date(iso.replace(' ', 'T'))
            }
            return date.toLocaleString(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
            })
        }
            
            return {
                id: t.task_id,
                name: t.title,
                description: t.description,
                due_date: toLocal(t.deadline),  // Keep ISO format from backend
                start_date: toLocal(t.created_at),  // Use created_at as start date
                created_at: toLocal(t.created_at),  // Keep ISO format
                status: t.status,
                priority: t.priority || 5,
                owner: t.owner,
                project_id: t.project_id,
                parent_id: t.parent_id,
                recurrence: t.recurrence,
                collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(id => Number(id)) : [],
                attachments: attachments,
                subtasks: Array.isArray(t.subtasks) ? t.subtasks.map(sub => {
                    let subAttachments = []
                    if (sub.attachment) {
                        try {
                            const parsed = JSON.parse(sub.attachment)
                            subAttachments = Array.isArray(parsed) ? parsed.map(filename => ({
                                name: filename.split(/[/\\]/).pop() || "File",
                                url: `http://localhost:5002/attachments/${filename}`
                            })) : []
                        } catch (e) {
                            subAttachments = [{
                                name: sub.attachment.split(/[/\\]/).pop() || "File",
                                url: `http://localhost:5002/attachments/${sub.attachment}`
                            }]
                        }
                    }
                    return {
                        id: sub.task_id,
                        name: sub.title,
                        description: sub.description,
                        due_date: toLocal(sub.deadline),
                        start_date: toLocal(sub.created_at),  // Use created_at as start date for subtasks
                        status: sub.status,
                        priority: sub.priority || 5,
                        owner: sub.owner,
                        project_id: sub.project_id,
                        parent_id: sub.parent_id,
                        collaborators: Array.isArray(sub.collaborators) ? sub.collaborators.map(id => Number(id)) : [],
                        attachments: subAttachments
                    }
                }) : []
            }
        }

        if (res.data.my_tasks && res.data.team_tasks) {
            // staff/ manager
            const myTasks = (res.data.my_tasks || []).map(transformTask)
            const teamTasks = {}
            
            for (const [employeeName, employeeTasks] of Object.entries(res.data.team_tasks || {})) {
                teamTasks[employeeName] = (employeeTasks || []).map(transformTask)
            }
            
            tasks.value = myTasks
            teamTasksData.value = teamTasks
            companyTasksData.value = {}
        } else if (res.data.my_tasks && res.data.company_tasks) {
            // Director/Senior Manager/HR structure: {my_tasks: [...], company_tasks: {...}}
            const myTasks = (res.data.my_tasks || []).map(transformTask)
            const companyTasks = {}
            
            for (const [deptName, deptData] of Object.entries(res.data.company_tasks || {})) {
                companyTasks[deptName] = {}
                for (const [teamName, teamData] of Object.entries(deptData || {})) {
                    companyTasks[deptName][teamName] = {}
                    for (const [employeeName, employeeTasks] of Object.entries(teamData || {})) {
                        companyTasks[deptName][teamName][employeeName] = (employeeTasks || []).map(transformTask)
                    }
                }
            }
            
            tasks.value = myTasks
            teamTasksData.value = {}
            companyTasksData.value = companyTasks
        } 
        
        if (!availableEmployees.value || availableEmployees.value.length === 0) {
        try { await fetchEmployees() } catch (_) {}
        }
    } catch (err) {
        console.error("Error fetching tasks:", err)
    }
    }

    async function saveTask() {
    console.log('🔍 saveTask called! Stack trace:', new Error().stack)
    clearValidationErrors()
    
    if (!validateForm()) {
        const firstErrorField = Object.keys(formErrors.value)[0]
        if (firstErrorField) {
            const errorElement = document.querySelector(`[data-field="${firstErrorField}"]`)
            if (errorElement) {
                errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                errorElement.focus()
            }
        }
        return
    }

    try {
        let uploadedAttachments = []

        for (const attachment of taskForm.value.attachments) {
        if (attachment.file) {
            const formData = new FormData()
            formData.append('attachment', attachment.file)

            const uploadRes = await axios.post('http://localhost:5002/upload-attachment', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            withCredentials: true
            })
            
            uploadedAttachments.push(uploadRes.data.file_path)
        } else if (attachment.url) {
            const urlParts = attachment.url.split('/')
            uploadedAttachments.push(urlParts[urlParts.length - 1])
        }
        }

        let deadlineDate
        if (taskForm.value.due_date) {
            let localDate
            
            if (taskForm.value.due_date.includes('T')) {
                localDate = new Date(taskForm.value.due_date)
            } else if (taskForm.value.due_date.includes(',')) {
                localDate = new Date(taskForm.value.due_date)
            } else {
                localDate = new Date(taskForm.value.due_date)
            }
            
            if (isNaN(localDate.getTime())) {
                console.error('Invalid date format:', taskForm.value.due_date)
                alert('Invalid date format. Please use a valid date.')
                return
            }
            
            // Convert to ISO string for backend
            deadlineDate = localDate.toISOString()
            console.log('Converted deadline:', taskForm.value.due_date, '→', deadlineDate)
        } else {
            const futureDate = new Date()
            futureDate.setDate(futureDate.getDate() + 7)
            deadlineDate = futureDate.toISOString()
        }

        // Prepare subtasks for payload
        const subtasksPayload = await Promise.all(subtasks.value.map(async (subtask) => {
            let subtaskDeadlineDate
            if (subtask.due_date) {
                const local = new Date(subtask.due_date)
                subtaskDeadlineDate = local.toISOString()
            } else {
                const futureDate = new Date()
                futureDate.setDate(futureDate.getDate() + 7)
                subtaskDeadlineDate = futureDate.toISOString()
            }

            // Process subtask attachments (same as main task)
            let uploadedSubtaskAttachments = []
            if (subtask.attachments && subtask.attachments.length > 0) {
                for (const attachment of subtask.attachments) {
                    if (attachment.file) {
                        const formData = new FormData()
                        formData.append('attachment', attachment.file)

                        const uploadRes = await axios.post('http://localhost:5002/upload-attachment', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' },
                            withCredentials: true
                        })
                        
                        uploadedSubtaskAttachments.push(uploadRes.data.file_path)
                    } else if (attachment.url) {
                        const urlParts = attachment.url.split('/')
                        uploadedSubtaskAttachments.push(urlParts[urlParts.length - 1])
                    }
                }
            }

            const payload = {
                title: subtask.name,
                description: subtask.description,
                deadline: subtaskDeadlineDate,
                status: subtask.status || 'ongoing',
                priority: subtask.priority,
                owner: subtask.owner || taskForm.value.owner,
                attachments: uploadedSubtaskAttachments, 
                collaborators: subtask.collaborators || []
            }

            if (subtask.id) {
                payload.task_id = subtask.id
            }

            return payload
        }))

        const payload = {
        title: taskForm.value.name,
        description: taskForm.value.description,
        attachments: uploadedAttachments,  // Array of filenames
        deadline: deadlineDate,
        status: taskForm.value.status,
        priority: taskForm.value.priority,
        parent_id: null,
        employee_id: currentEmployeeId,
        owner: taskForm.value.owner,
        project_id: taskForm.value.project_id,
        recurrence: convertRecurrenceToDays(taskForm.value.recurrence_unit, taskForm.value.recurrence_frequency),
        collaborators: (() => {
            const selected = Array.isArray(taskForm.value.collaborators) ? taskForm.value.collaborators : []
            const role = (currentRole || '').toLowerCase()
            let allowedIds = []

            if (role === 'staff' || role === 'manager') {
                allowedIds = (availableEmployees.value || []).map(e => e.employee_id)
            } 
            else {
                // Senior managers, directors, and HR: use assignment employees (properly filtered)
                allowedIds = (assignmentEmployees.value || []).map(e => e.employee_id)
            }

            return selected.filter(id => allowedIds.includes(id))
        })(),
        role: currentRole,
        subtasks: subtasksPayload,
        actor_id: currentEmployeeId  // Add actor_id for notifications
        }

        let createdTaskId = null
        if (taskForm.value.id) {
        console.log('Updating task with payload:', payload)
        const updateRes = await axios.put(`http://localhost:5002/task/${taskForm.value.id}`, payload, { withCredentials: true })
        console.log("Task updated:", updateRes.data)
        createdTaskId = taskForm.value.id
        } else {
        console.log('Creating task with payload:', payload)
        const createRes = await axios.post("http://localhost:5002/tasks", payload, { withCredentials: true })
        console.log("Task created:", createRes.data)
        createdTaskId = createRes.data.task_id || createRes.data.id
        }

        // Save temporary comments for new tasks
        if (createdTaskId && !taskForm.value.id) {
        const tempComments = comments.value.filter(c => c.is_temp)
        for (const comment of tempComments) {
            try {
            const attachments = (comment.attachments || []).map(a => a.filename)
            await axios.post(
                `http://localhost:5002/task/${createdTaskId}/comments`,
                { content: comment.content, attachments },
                {
                withCredentials: true,
                headers: { 'X-Employee-Id': String(currentEmployeeId) }
                }
            )
            } catch (err) {
            console.error("Error saving comment:", err)
            }
        }
        }

        await fetchTasks()

        if (taskForm.value.id) {
        selectedTask.value = tasks.value.find(t => t.id === taskForm.value.id)
        }

        showModal.value = false
        taskForm.value = resetForm()
        subtasks.value = [] 
        comments.value = [] 
        isEditing.value = false
    } catch (error) {
        console.error("Error saving task:", error)
        
        const backendMessage = error.response?.data?.message || 'An unexpected error occurred'
        formErrors.value = { backend: backendMessage }
        showValidationErrors.value = true
        
        const modalContent = document.querySelector('.modal-content')
        if (modalContent) {
            modalContent.scrollTo({ top: 0, behavior: 'smooth' })
        }
    }
    }

    // Form validation functions
    function validateForm() {
        const errors = {}
        
        // Required fields validation - ALL basic information must be filled
        if (!taskForm.value.name || taskForm.value.name.trim() === '') {
            errors.name = 'Task name is required'
        }
        
        if (!taskForm.value.description || taskForm.value.description.trim() === '') {
            errors.description = 'Description is required'
        }
        
        if (!taskForm.value.due_date || taskForm.value.due_date.trim() === '') {
            errors.due_date = 'Due date is required'
        }
        
        if (!taskForm.value.priority || taskForm.value.priority === null || taskForm.value.priority === '') {
            errors.priority = 'Priority is required'
        }
        
        if (taskForm.value.due_date) {
            const dueDate = new Date(taskForm.value.due_date)
            const now = new Date()
            if (dueDate < now) {
                errors.due_date = 'Deadline must be in the future'
            }
        }
        
        if (taskForm.value.recurrence_unit !== null && taskForm.value.recurrence_unit !== undefined) {
            if (!taskForm.value.recurrence_frequency || taskForm.value.recurrence_frequency < 1) {
                errors.recurrence_frequency = 'Frequency must be at least 1'
            }
        }
        
        formErrors.value = errors
        showValidationErrors.value = Object.keys(errors).length > 0
        
        return Object.keys(errors).length === 0
    }

    function clearValidationErrors() {
        formErrors.value = {}
        showValidationErrors.value = false
    }

    function getFieldError(fieldName) {
        return formErrors.value[fieldName] || ''
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
    } catch (error) {
        console.error("Error updating status:", error)
        
        const backendMessage = error.response?.data?.message || 'Error updating task status'
        
        if (showModal.value) {
            formErrors.value = { backend: backendMessage }
            showValidationErrors.value = true
            
            const modalContent = document.querySelector('.modal-content')
            if (modalContent) {
                modalContent.scrollTo({ top: 0, behavior: 'smooth' })
            }
        } else {
            alert(backendMessage)
        }
    }
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

    const employeeDisplayList = computed(() => {
    const role = (currentRole || '').toLowerCase()
    const showMeta = role === 'senior manager' || role === 'hr' || role === 'director'
    return (assignmentEmployees.value || []).map(emp => ({
        ...emp,
        display_label: showMeta
        ? `${emp.employee_name} [${[emp.role, emp.team, emp.department].filter(Boolean).join(' • ')}]`
        : emp.employee_name
    }))
    })

    // Employee list for owner assignment (excludes current user)
    const ownerAssignmentList = computed(() => {
    const role = (currentRole || '').toLowerCase()
    const showMeta = role === 'senior manager' || role === 'hr' || role === 'director'
    return (assignmentEmployees.value || [])
        .filter(emp => emp.employee_id !== currentEmployeeId) // Exclude current user
        .map(emp => ({
            ...emp,
            display_label: showMeta
            ? `${emp.employee_name} [${[emp.role, emp.team, emp.department].filter(Boolean).join(' • ')}]`
            : emp.employee_name
        }))
    })

    const subtaskOwnerList = computed(() => {
    const role = (currentRole || '').toLowerCase()
    const showMeta = role === 'senior manager' || role === 'hr' || role === 'director'
    
    // parent task collaborators + owner
    const allowedIds = new Set([
        taskForm.value.owner,
        ...(Array.isArray(taskForm.value.collaborators) ? taskForm.value.collaborators : [])
    ])
    
    return (assignmentEmployees.value || [])
        .filter(emp => allowedIds.has(emp.employee_id))
        .map(emp => ({
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

    // Helper function to convert recurrence unit + frequency to days
    function convertRecurrenceToDays(unit, frequency) {
        if (!unit || unit === 'none' || !frequency) return null
        
        switch (unit) {
            case 'day':
                return frequency
            case 'week':
                return frequency * 7
            case 'month':
                return frequency * 30 // Approximate
            case 'year':
                return frequency * 365 // Approximate
            default:
                return null
        }
    }
    
    // Helper function to convert days back to unit + frequency format
    function convertDaysToRecurrence(days) {
        if (!days) return { unit: 'none', frequency: 1 }
        
        // Try to find the best match
        if (days % 365 === 0) {
            return { unit: 'year', frequency: days / 365 }
        } else if (days % 30 === 0) {
            return { unit: 'month', frequency: days / 30 }
        } else if (days % 7 === 0) {
            return { unit: 'week', frequency: days / 7 }
        } else {
            return { unit: 'day', frequency: days }
        }
    }

    function getRecurrenceLabel(unit, frequency) {
        if (!unit || unit === 'none' || !frequency) return 'No recurrence'
        
        const unitLabel = frequency === 1 ? unit : unit + 's'
        return `Every ${frequency} ${unitLabel}`
    }

    // Helper function to display recurrence from days (for task cards)
    function getRecurrenceLabelFromDays(days) {
        if (!days) return 'No recurrence'
        const { unit, frequency } = convertDaysToRecurrence(days)
        return getRecurrenceLabel(unit, frequency)
    }

    async function openAdd() {
    isEditing.value = true
    selectedTask.value = null
    taskForm.value = resetForm()
    subtasks.value = [] 
    comments.value = [] // Clear any temporary comments
    clearValidationErrors() 
    editingSubtaskId.value = null 
    editingSubtaskBackup.value = null
    await fetchEmployees()
    assignmentEmployees.value = await fetchEmployeesForAssignment()
    console.log('Assignment employees loaded:', assignmentEmployees.value)
    showModal.value = true
    }

    // convert ISO date to locale string for display
    function toLocal(iso) {
    if (!iso) return null
    const date = new Date(iso)
    if (isNaN(date.getTime())) return null
    return date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short"
    })
    }

    function openDetails(task) {
    selectedTask.value = task
    isEditing.value = false
    clearValidationErrors() // Clear any validation errors
    editingSubtaskId.value = null 
    editingSubtaskBackup.value = null
    
    // Convert displayed date back to datetime-local format for editing
    let formattedDueDate = null
    if (task.due_date) {
        try {
            // Parse the displayed date and convert to datetime-local format
            const date = new Date(task.due_date)
            if (!isNaN(date.getTime())) {
                // Convert to YYYY-MM-DDTHH:MM format for datetime-local input
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
        start_date: task.created_at,  // Use created_at as start date (read-only)
        status: task.status,
        priority: task.priority,
        owner: task.owner,
        project_id: task.project_id || null,
        collaborators: (task.collaborators || []).filter(id => id !== task.owner),
        attachments: task.attachments || [],
        recurrence_unit: convertDaysToRecurrence(task.recurrence).unit || 'none',
        recurrence_frequency: convertDaysToRecurrence(task.recurrence).frequency || 1
    }
    // Initialize subtasks and format dates for datetime-local inputs
    subtasks.value = (task.subtasks || []).map(subtask => {
        let formattedDate = subtask.due_date
        if (formattedDate) {
            formattedDate = formattedDate.replace(/:\d{2}[.Z].*$/, '')
        }
        return { ...subtask, due_date: formattedDate }
    })
    // Load comments for this task
    loadComments(task.id)
    // Load mentionable users for this task
    loadMentionable(task.id)
    showModal.value = true
    }

    async function startEditing() {
    isEditing.value = true
    await fetchEmployees()
    assignmentEmployees.value = await fetchEmployeesForAssignment()
    
    // Fetch department employees for owner assignment (managers/directors/senior managers only)
    if (canAssignOwners()) {
        const depRaw = sessionStorage.getItem("department") || ""
        await fetchDepartmentEmployees(depRaw)
    }
    
    if (taskForm.value.status === null) {
        taskForm.value.status = (currentRole || '').toLowerCase() === 'staff' ? 'ongoing' : 'unassigned'
    }
    if (taskForm.value.priority === null) {
        taskForm.value.priority = 5
    }
    }

    function formatDate(date) {
    return toLocal(date) || '-'
    }

    function formatDateRelative(date) {
    if (!date) return '-'
    const d = new Date(date)
    const now = new Date()
    const diffMs = d.getTime() - now.getTime()
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Tomorrow'
    if (diffDays === -1) return 'Yesterday'
    if (diffDays > 0) return `In ${diffDays} days`
    return `${Math.abs(diffDays)} days ago`
    }

    async function handleAttachmentWithUpload(event, targetArray, fileUploadRef) {
    const files = event.files
    
    if (fileUploadRef && typeof fileUploadRef.clear === 'function') {
        fileUploadRef.clear()
    }
    
    for (const file of files) {
        try {
            const formData = new FormData()
            formData.append('attachment', file)

            const uploadRes = await axios.post('http://localhost:5002/upload-attachment', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                withCredentials: true
            })
            
            targetArray.push({
                name: file.name,
                file: null, 
                url: `http://localhost:5002/attachments/${uploadRes.data.file_path}`
            })
        } catch (error) {
            console.error('Error uploading file:', error)
            targetArray.push({
                name: file.name,
                file: file,
                url: null
            })
        }
    }
    }

    function removeAttachment(index, targetArray) {
    targetArray.splice(index, 1)
    }

    async function handleMainTaskAttachment(event) {
    await handleAttachmentWithUpload(event, taskForm.value.attachments, fileUploadRef.value)
    }

    function removeMainTaskAttachment(index) {
    removeAttachment(index, taskForm.value.attachments)
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
    // Auto-open modal when navigated with a taskId from project details
    const qId = Number(route.query.taskId || 0)
    const openMode = String(route.query.open || 'details')

    if (qId) {
        const tryOpen = () => {
        const t = tasks.value.find(x => x.id === qId || x.task_id === qId)
        if (!t) {
            setTimeout(tryOpen, 150)
            return
        }
        openDetails(t)
        if (openMode === 'edit') {
            isEditing.value = true
        }
        }
        tryOpen()
    }
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
    
    //fetches mentionable users from /task/<id>/mentionable
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
    const content = (newComment.value || '').trim()
    if (!content) return
    
    // If creating a new task, store comment temporarily
    if (!taskId) {
        const tempComment = {
            id: Date.now(), // Temporary ID
            content: content,
            attachments: [...newCommentAttachments.value],
            author_id: currentEmployeeId,
            created_at: new Date().toISOString(),
            is_temp: true
        }
        comments.value.push(tempComment)
        newComment.value = ''
        newCommentAttachments.value = []
        return
    }
    
    // For existing tasks, add comment via API
    try {
        commentError.value = ''
        const attachments = (newCommentAttachments.value || []).map(a => a.filename)
        await axios.post(
          `http://localhost:5002/task/${taskId}/comments`,
          { content, attachments },
          {
            withCredentials: true,
            headers: { 'X-Employee-Id': String(currentEmployeeId) }
          }
        )
        newComment.value = ''
        newCommentAttachments.value = []
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

    function onCommentFileUploaded(e) {
        try {
            const res = JSON.parse(e?.xhr?.response || '{}')
            if (res?.filename) {
                const original = (e?.files?.[0]?.name) || res.filename
                newCommentAttachments.value.push({ filename: res.filename, original_name: original })
            }
        } catch {}
    }

    function removeNewAttachment(idx) {
        newCommentAttachments.value.splice(idx, 1)
    }

    function isOverdue(task) {
        if (!task?.due_date || !task?.status) return false
        const due = new Date(task.due_date)
        if (isNaN(due.getTime())) return false
        const now = new Date()
        return due < now && task.status.toLowerCase() !== 'done'
    }

// ----------------- Report Filter & Summary -----------------
const startDate = ref('')
const endDate = ref('')

// Default filter: past month
onMounted(() => {
  const today = new Date()
  const lastMonth = new Date()
  lastMonth.setMonth(today.getMonth() - 1)
  startDate.value = lastMonth.toISOString().split('T')[0]
  endDate.value = today.toISOString().split('T')[0]
})

// Compute filtered tasks based on selected dates
const filteredTasks = computed(() => {
  if (!tasks.value?.length) return []
  const start = new Date(startDate.value)
  const end = new Date(endDate.value)
  return tasks.value.filter((task) => {
    if (!task.due_date) return false
    const due = new Date(task.due_date)
    return due >= start && due <= end
  })
})

const totalTasks = computed(() => displayTasks.value.length)
const completedTasks = computed(() =>
//   filteredTasks.value.filter(
//     (t) => t.status?.toLowerCase() === 'done' || t.status?.toLowerCase() === 'completed'
//   )
displayTasks.value.filter(
    (t) => t.status?.toLowerCase() === 'done' || t.status?.toLowerCase() === 'completed'
  )
)

const ongoingTasks = computed(() =>
//   filteredTasks.value.filter((t) => t.status?.toLowerCase() === 'ongoing')
    displayTasks.value.filter((t) => t.status?.toLowerCase() === 'ongoing')
)

const overdueTasks = computed(() =>
  displayTasks.value.filter((t) => {
    if (!t.due_date) return false
    const due = new Date(t.due_date)
    const today = new Date()
    return due < today && (t.status?.toLowerCase() !== 'done' && t.status?.toLowerCase() !== 'completed')
  })
)

const highPriorityCount = computed(() => tasksByPriority.value.high.length)
const mediumPriorityCount = computed(() => tasksByPriority.value.medium.length)
const lowPriorityCount = computed(() => tasksByPriority.value.low.length)

const overallProgress = computed(() => {
  const total = totalTasks.value
  if (total === 0) return 'No Data'
  const ratio = completedTasks.value.length / total
  if (ratio >= 0.7) return 'Good'
  if (ratio >= 0.4) return 'Average'
  return 'Poor'
})

function formatDateDisplay(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-SG', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

const formattedDateRange = computed(() => {
  if (!startDate.value || !endDate.value) return ''
  return `${formatDateDisplay(startDate.value)} - ${formatDateDisplay(endDate.value)}`
})

// Trigger recomputation manually if needed
function updateDateFilter() {
  // Nothing needed — computed handles reactivity
}

// -------------------- Company Report Logic --------------------
const companyStartDate = ref(null)
const companyEndDate = ref(null)
const companySelectedDept = ref('')
const companyAllTasks = ref([])
const companyFilteredData = ref({})
const companyDepartmentCount = ref(0)
watch(currentTab, async (tab) => {
  if (tab === 'company_report') {
    await fetchDepartments()   // ✅ ensures dropdown has departments
    loadCompanyReport()
  }
})

watch(currentTab, (tab) => {
  if (tab === 'company_report') loadCompanyReport()
})

function loadCompanyReport() {
const today = new Date()
  const oneMonthAgo = new Date(today)
  oneMonthAgo.setMonth(today.getMonth() - 1)

  companyStartDate.value = oneMonthAgo.toISOString().split('T')[0]
  companyEndDate.value = today.toISOString().split('T')[0]
  
  buildCompanyData()
}


function applyCompanyFilters() {
  buildCompanyData()
}



// Computed Metrics
const companyCompletedTasks = computed(() =>
  companyAllTasks.value.filter(t => t.status?.toLowerCase() === 'done' || t.status?.toLowerCase() === 'completed')
)

const companyOverdueTasks = computed(() =>
  companyAllTasks.value.filter(t => isOverdue(t))
)

const companyCompletionRate = computed(() => {
  const total = companyAllTasks.value.length
  const completed = companyCompletedTasks.value.length
  return total ? Math.round((completed / total) * 100) : 0
})

// Identify top & overloaded departments
const topProductiveDept = computed(() => {
  let max = -1, best = ''
  for (const [dept, data] of Object.entries(companyFilteredData.value)) {
    if (data.completionRate > max) { max = data.completionRate; best = dept }
  }
  return best
})

const overloadedDept = computed(() => {
  let max = -1, name = ''
  for (const [dept, data] of Object.entries(companyFilteredData.value)) {
    if (data.overdue > max) { max = data.overdue; name = dept }
  }
  return name
})

const formattedCompanyDateRange = computed(() => {
  if (!companyStartDate.value || !companyEndDate.value) return 'All time'
  const opts = { day: 'numeric', month: 'long', year: 'numeric' }
  const s = new Date(companyStartDate.value).toLocaleDateString('en-SG', opts)
  const e = new Date(companyEndDate.value).toLocaleDateString('en-SG', opts)
  return `${s} - ${e}`
})

// Export functions
function exportCompanyReport(type) {
  if (type === 'pdf') print() // quick PDF print
  else if (type === 'excel') {
    const rows = []
    for (const [dept, data] of Object.entries(companyFilteredData.value)) {
      rows.push({
        Department: dept,
        Total_Tasks: data.tasks.length,
        Completed: data.completed,
        Overdue: data.overdue,
        Completion_Rate: data.completionRate + '%'
      })
    }
    exportToExcel(rows, 'Company_Productivity_Report.xlsx')
  }
}

function buildCompanyData() {
  const start = companyStartDate.value ? new Date(companyStartDate.value) : null
  const end = companyEndDate.value ? new Date(companyEndDate.value) : null

  const filtered = {}
  let allTasks = []

  for (const [deptName, deptObj] of Object.entries(companyTasksData.value || {})) {
    // ✅ If user selected a specific department, only process that one
    if (companySelectedDept.value && deptName !== companySelectedDept.value) continue
    console.log(companySelectedDept.value ,"hi")
    let deptTasks = []
    for (const team of Object.values(deptObj || {})) {
      for (const employeeTasks of Object.values(team || {})) {
        deptTasks.push(...employeeTasks)
      }
    }

    // ✅ Apply timeframe filter
    if (start && end) {
      deptTasks = deptTasks.filter((t) => {
        const created = new Date(t.created_at)
        const due = new Date(t.due_date)
        return created <= end && due >= start
      })
    }

    const completed = deptTasks.filter(
      (t) => t.status?.toLowerCase() === "done" || t.status?.toLowerCase() === "completed"
    ).length
    const overdue = deptTasks.filter((t) => isOverdue(t)).length
    const ontime = deptTasks.length - overdue
    const completionRate = deptTasks.length
      ? Math.round((completed / deptTasks.length) * 100)
      : 0

    filtered[deptName] = {
      tasks: deptTasks,
      completed,
      overdue,
      ontime,
      completionRate,
    }
    allTasks.push(...deptTasks)
  }

  companyFilteredData.value = filtered
  companyAllTasks.value = allTasks
  companyDepartmentCount.value = Object.keys(filtered).length
}



// ---------------- Project Report Logic -----------------
const projectReportLoading = ref(false)
const projectReportError = ref('')
const projectReportProjects = ref([])        // list of projects for filter dropdown
const projectReportSelectedId = ref(null)    // selected project id for report
const projectReportSelected = ref(null)      // selected project metadata
const projectReportTasks = ref([])           // tasks for selected project (flattened)
const projectReportTeamMembers = ref([])     // team members returned by timeline endpoint
const projectReportDateRange = ref(null)     // optional project date range from timeline
const showProjectFilterMenu = ref(false)
const projectReportGenerating = ref(false)

// Default: show recent project when loaded
onMounted(() => {
    // load list of projects for the filter dropdown
    loadProjectListForReport()
})

// Load project list for the project filter dropdown
async function loadProjectListForReport() {
    console.log("hi")
    projectReportLoading.value = true
    projectReportError.value = ''
    try {
        // Try backend projects endpoint (adjust if you have a shared getProjects helper)
        const res = await axios.get('http://localhost:5002/projects', { withCredentials: true })
        projectReportProjects.value = Array.isArray(res.data) ? res.data : []
        // default to first project if none selected
        if (!projectReportSelectedId.value && projectReportProjects.value.length > 0) {
            projectReportSelectedId.value = projectReportProjects.value[0].id
            projectReportSelected.value = projectReportReportFind(projectReportSelectedId.value)
            // load timeline for that project
            await loadProjectReportTimeline(projectReportSelectedId.value)
        }
    } catch (err) {
        console.error('Error loading projects for report:', err)
        projectReportError.value = 'Failed to load projects'
        projectReportProjects.value = []
    } finally {
        projectReportLoading.value = false
    }
}

// Helper to find project metadata by id
function projectReportReportFind(id) {
    return projectReportProjects.value.find(p => p.id === id) || null
}

// Toggle project filter menu (consistent with other filter toggles)
function toggleProjectFilterMenu() {
    showProjectFilterMenu.value = !showProjectFilterMenu.value
}

// When user selects a project from dropdown / radio list
async function selectProjectForReport(id) {
    projectReportSelectedId.value = id
    projectReportSelected.value = projectReportReportFind(id)
    await loadProjectReportTimeline(id)
    showProjectFilterMenu.value = false
}

// Load timeline data (tasks, team members, project_date_range) for the selected project
async function loadProjectReportTimeline(projectId) {
    if (!projectId) {
        projectReportTasks.value = []
        projectReportTeamMembers.value = []
        projectReportDateRange.value = null
        return
    }

    projectReportLoading.value = true
    projectReportError.value = ''
    try {
        const res = await axios.get(`http://localhost:5002/projects/${projectId}/timeline`, { withCredentials: true })
        const data = res.data || {}

        // tasks come from the timeline endpoint
        projectReportTasks.value = Array.isArray(data.tasks) ? data.tasks.map(t => ({
            id: t.task_id ?? t.id,
            name: t.title ?? t.name,
            description: t.description ?? t.desc ?? '',
            created_at: t.created_at ?? t.start_date ?? t.start,
            due_date: t.deadline ?? t.due_date ?? t.due,
            status: t.status ?? 'unassigned',
            priority: t.priority ?? 5,
            owner: t.owner ?? t.employee_id ?? null,
            collaborators: Array.isArray(t.collaborators) ? t.collaborators.map(c => Number(c)) : []
        })) : []

        // team members and project date range
        projectReportTeamMembers.value = Array.isArray(data.team_members) ? data.team_members : []
        projectReportDateRange.value = data.project_date_range || null

    } catch (err) {
        console.error('Error loading project timeline for report:', err)
        projectReportError.value = 'Failed to load project timeline'
        projectReportTasks.value = []
        projectReportTeamMembers.value = []
        projectReportDateRange.value = null
    } finally {
        projectReportLoading.value = false
    }
}

// Compute only tasks that are accessible (project scope) - similar to displayTasks style
const projectReportDisplayTasks = computed(() => {
    return projectReportTasks.value || []
})

// Compute project overall progress (percentage of completed tasks)
const projectReportCompletedTasks = computed(() =>
    projectReportDisplayTasks.value.filter(t => (t.status || '').toLowerCase() === 'done' || (t.status || '').toLowerCase() === 'completed')
)

const projectReportTotalTasks = computed(() => projectReportDisplayTasks.value.length)

const projectReportProgress = computed(() => {
    const total = projectReportTotalTasks.value
    if (!total) return 0
    return Math.round((projectReportCompletedTasks.value.length / total) * 100)
})

// Human-readable overall progress label (Good / Average / Poor), same logic as other reports
const projectReportProgressLabel = computed(() => {
    const total = projectReportTotalTasks.value
    if (total === 0) return 'No Data'
    const ratio = projectReportCompletedTasks.value.length / total
    if (ratio >= 0.7) return 'Good'
    if (ratio >= 0.4) return 'Average'
    return 'Poor'
})

// Helper to format date similar to your other formatters
function projectReportFormatDate(dateStr) {
    if (!dateStr) return '-'
    try {
        const d = new Date(dateStr)
        if (isNaN(d.getTime())) return '-'
        return d.toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
    } catch (_) {
        return '-'
    }
}

// Resolve collaborator names (uses projectReportTeamMembers first then falls back to id)
function projectReportGetCollaboratorNames(collabIds) {
    if (!Array.isArray(collabIds) || collabIds.length === 0) return 'None'
    const names = collabIds.map(id => {
        const m = projectReportTeamMembers.value.find(x => Number(x.employee_id || x.id) === Number(id))
        if (m) return m.employee_name || m.name || `#${id}`
        return `#${id}`
    })
    return names.join(', ')
}

// Export current project report to PDF
async function exportProjectReportPDF() {
    if (!projectReportSelectedId.value) {
        alert('Please select a project first.')
        return
    }

    if (!projectReportDisplayTasks.value.length) {
        alert('No tasks to export for this project.')
        return
    }

    projectReportGenerating.value = true
    try {
        const projectName = (projectReportSelected.value && (projectReportSelected.value.name || projectReportSelected.value.title)) || `Project_${projectReportSelectedId.value}`
        const generatedOn = new Date().toLocaleString('en-SG')

        const doc = new jsPDF()
        doc.setFontSize(16)
        doc.text('Project Schedule Report', 14, 20)
        doc.setFontSize(11)
        doc.text(`Project: ${projectName}`, 14, 30)
        doc.text(`Generated: ${generatedOn}`, 14, 36)
        doc.text(`Overall Progress: ${projectReportProgress.value}% (${projectReportProgressLabel.value})`, 14, 42)
        doc.text(`Total Tasks: ${projectReportTotalTasks.value}`, 14, 48)
        doc.line(14, 52, 195, 52)

        const body = projectReportDisplayTasks.value.map(t => ([
            t.name || 'Untitled Task',
            projectReportFormatDate(t.created_at),
            projectReportFormatDate(t.due_date),
            t.status || '-',
            projectReportGetCollaboratorNames(t.collaborators)
        ]))

        autoTable(doc, {
            startY: 58,
            head: [['Task', 'Start', 'Due', 'Status', 'Collaborators']],
            body,
            styles: { fontSize: 9, cellPadding: 3 },
            headStyles: { fillColor: [41, 128, 185], textColor: 255 },
            columnStyles: { 0: { cellWidth: 50 }, 1: { cellWidth: 30 }, 2: { cellWidth: 30 }, 3: { cellWidth: 30 }, 4: { cellWidth: 50 } }
        })

        doc.save(`${projectName.replace(/\s+/g, '_')}_Schedule_Report.pdf`)
    } catch (err) {
        console.error('Error exporting project report PDF:', err)
        alert('Failed to export PDF. Check console for details.')
    } finally {
        projectReportGenerating.value = false
    }
}

// Auto-load when switching to the project_report tab (consistent with other report watchers)
watch(currentTab, async (tab) => {
    if (tab === 'project_report') {
        // Ensure projects list is ready and timeline loaded for selected project
        if (!projectReportProjects.value.length) {
            await loadProjectListForReport()
        } else if (projectReportSelectedId.value) {
            await loadProjectReportTimeline(projectReportSelectedId.value)
        }
    }
})
// ---------------- /Project Report Logic -----------------



</script>