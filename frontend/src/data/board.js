import { computed, reactive, ref } from 'vue'
import api from './api'
import { EVENTS, emit } from './bus'
import { sortByPriority } from '@/utils/constants'

/**
 * One shared store per visited project, so Board / List / Timeline / Overview
 * all read the same task array and a drag on the board is instantly visible
 * on the other tabs.
 */
export const currentProject = ref(null)
export const projectDoc = ref(null)
export const members = ref([])
export const tasks = ref([])
export const loading = ref(false)
export const error = ref(null)

export const filters = reactive({
  search: '',
  priorities: [],
  assignee: null,
  type: '',
  includeCompleted: true,
  groupBy: 'status',
})

export function resetFilters() {
  filters.search = ''
  filters.priorities = []
  filters.assignee = null
  filters.type = ''
  filters.includeCompleted = true
}

export const hasActiveFilters = computed(
  () =>
    Boolean(filters.search) ||
    filters.priorities.length > 0 ||
    Boolean(filters.assignee) ||
    Boolean(filters.type) ||
    !filters.includeCompleted,
)

export async function loadProject(name, { force = false } = {}) {
  if (currentProject.value === name && projectDoc.value && !force) return

  currentProject.value = name
  loading.value = true
  error.value = null

  try {
    const [project, rows] = await Promise.all([
      api.getProject(name),
      api.getTasks({ project: name, include_completed: 1 }),
    ])
    projectDoc.value = project.doc
    members.value = project.members || []
    tasks.value = rows || []
  } catch (e) {
    error.value = e
    projectDoc.value = null
    tasks.value = []
  } finally {
    loading.value = false
  }
}

export async function reloadTasks() {
  if (!currentProject.value) return
  tasks.value =
    (await api.getTasks({ project: currentProject.value, include_completed: 1 })) || []
}

/** Merge a server response back into the local array without a full refetch. */
export function upsertTask(task) {
  if (!task) return
  const index = tasks.value.findIndex((t) => t.name === task.name)
  if (index === -1) {
    tasks.value = [task, ...tasks.value]
  } else {
    tasks.value[index] = { ...tasks.value[index], ...task }
  }
  emit(EVENTS.TASK_UPDATED, task)
}

export function removeTask(name) {
  tasks.value = tasks.value.filter((t) => t.name !== name)
  emit(EVENTS.TASK_DELETED, name)
}

export const visibleTasks = computed(() => {
  const term = filters.search.trim().toLowerCase()

  return tasks.value.filter((task) => {
    if (!filters.includeCompleted && ['Completed', 'Cancelled'].includes(task.status))
      return false
    if (filters.priorities.length && !filters.priorities.includes(task.priority))
      return false
    if (filters.type && task.type !== filters.type) return false
    if (filters.assignee) {
      const assigned = (task.assignees || []).some((u) => u.name === filters.assignee)
      if (filters.assignee === '__unassigned__') {
        if ((task.assignees || []).length) return false
      } else if (!assigned) {
        return false
      }
    }
    if (term) {
      const haystack = `${task.subject} ${task.name}`.toLowerCase()
      if (!haystack.includes(term)) return false
    }
    return true
  })
})

/** { status: Task[] } with each column sorted the way a board should read. */
export function groupByStatus(statuses) {
  const groups = {}
  for (const status of statuses) groups[status] = []

  for (const task of visibleTasks.value) {
    if (!groups[task.status]) groups[task.status] = []
    groups[task.status].push(task)
  }

  for (const status of Object.keys(groups)) {
    groups[status].sort((a, b) => {
      const byPriority = sortByPriority(a, b)
      if (byPriority !== 0) return byPriority
      if (a.exp_end_date && b.exp_end_date)
        return a.exp_end_date < b.exp_end_date ? -1 : 1
      if (a.exp_end_date) return -1
      if (b.exp_end_date) return 1
      return a.name < b.name ? -1 : 1
    })
  }

  return groups
}
