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
/** Group tasks (epics) for the board's epic rail. */
export const epics = ref([])
export const loading = ref(false)
export const error = ref(null)

export const filters = reactive({
  search: '',
  priorities: [],
  assignee: null,
  epic: null,
  type: '',
  tags: [],
  includeCompleted: true,
  swimlane: 'none',
})

/** Tasks ticked in the list view, for bulk actions. */
export const selection = ref(new Set())

export function toggleSelected(name) {
  const next = new Set(selection.value)
  next.has(name) ? next.delete(name) : next.add(name)
  selection.value = next
}

export function selectMany(names, on = true) {
  const next = new Set(selection.value)
  for (const name of names) (on ? next.add : next.delete).call(next, name)
  selection.value = next
}

export function clearSelection() {
  selection.value = new Set()
}

export function resetFilters() {
  filters.search = ''
  filters.priorities = []
  filters.assignee = null
  filters.epic = null
  filters.type = ''
  filters.tags = []
  filters.includeCompleted = true
}

/** Snapshot/restore for the saved-views feature. */
export function currentFilterState() {
  return {
    search: filters.search,
    priorities: [...filters.priorities],
    assignee: filters.assignee,
    epic: filters.epic,
    type: filters.type,
    tags: [...filters.tags],
    includeCompleted: filters.includeCompleted,
    swimlane: filters.swimlane,
  }
}

export function applyFilterState(state = {}) {
  filters.search = state.search || ''
  filters.priorities = [...(state.priorities || [])]
  filters.assignee = state.assignee || null
  filters.epic = state.epic || null
  filters.type = state.type || ''
  filters.tags = [...(state.tags || [])]
  filters.includeCompleted = state.includeCompleted !== false
  filters.swimlane = state.swimlane || 'none'
}

export const hasActiveFilters = computed(
  () =>
    Boolean(filters.search) ||
    filters.priorities.length > 0 ||
    Boolean(filters.assignee) ||
    Boolean(filters.epic) ||
    Boolean(filters.type) ||
    filters.tags.length > 0 ||
    !filters.includeCompleted,
)

export async function loadProject(name, { force = false } = {}) {
  if (currentProject.value === name && projectDoc.value && !force) return

  currentProject.value = name
  loading.value = true
  error.value = null

  try {
    const [project, rows, epicRows] = await Promise.all([
      api.getProject(name),
      api.getTasks({ project: name, include_completed: 1 }),
      api.getProjectEpics(name),
    ])
    projectDoc.value = project.doc
    members.value = project.members || []
    tasks.value = rows || []
    epics.value = epicRows || []
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
    if (filters.epic) {
      // an epic row itself belongs to its own filtered view too
      if (task.parent_task !== filters.epic && task.name !== filters.epic) return false
    }
    if (filters.tags.length) {
      const taskTags = task.tags || []
      if (!filters.tags.every((tag) => taskTags.includes(tag))) return false
    }
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

/**
 * Swimlanes. Columns are always Task.status -- that is what a board *is* --
 * while lanes slice the same tasks by a second dimension, the way Jira does.
 */
export const SWIMLANE_OPTIONS = [
  { label: 'No swimlanes', value: 'none' },
  { label: 'Assignee', value: 'assignee' },
  { label: 'Priority', value: 'priority' },
  { label: 'Type', value: 'type' },
  { label: 'Epic', value: 'epic' },
]

function laneKeysFor(task, dimension) {
  if (dimension === 'assignee') {
    const people = task.assignees || []
    return people.length
      ? people.map((u) => ({ key: u.name, label: u.full_name || u.name, user: u }))
      : [{ key: '__none__', label: 'Unassigned' }]
  }
  if (dimension === 'priority')
    return [{ key: task.priority || '__none__', label: task.priority || 'No priority' }]
  if (dimension === 'type')
    return [{ key: task.type || '__none__', label: task.type || 'No type' }]
  if (dimension === 'epic')
    return [
      {
        key: task.parent_task || '__none__',
        // the raw parent id is meaningless to a reader; use the epic's subject
        label: task.epic?.subject || 'No epic',
        color: task.epic?.color,
      },
    ]
  return [{ key: '__all__', label: '' }]
}

export function buildLanes(statuses, dimension = 'none') {
  const lanes = new Map()

  const emptyColumns = () => Object.fromEntries(statuses.map((s) => [s, []]))

  for (const task of boardTasks.value) {
    for (const lane of laneKeysFor(task, dimension)) {
      if (!lanes.has(lane.key)) {
        lanes.set(lane.key, { ...lane, columns: emptyColumns(), count: 0 })
      }
      const entry = lanes.get(lane.key)
      if (!entry.columns[task.status]) entry.columns[task.status] = []
      entry.columns[task.status].push(task)
      entry.count += 1
    }
  }

  // Always render every column, even in a lane that has none of them.
  if (!lanes.size) {
    lanes.set('__all__', { key: '__all__', label: '', columns: emptyColumns(), count: 0 })
  }

  const sorter = (a, b) => {
    const byPriority = sortByPriority(a, b)
    if (byPriority !== 0) return byPriority
    if (a.exp_end_date && b.exp_end_date) return a.exp_end_date < b.exp_end_date ? -1 : 1
    if (a.exp_end_date) return -1
    if (b.exp_end_date) return 1
    return a.name < b.name ? -1 : 1
  }

  const result = [...lanes.values()]
  for (const lane of result) {
    for (const status of Object.keys(lane.columns)) lane.columns[status].sort(sorter)
  }

  // Unassigned/none buckets belong at the bottom.
  result.sort((a, b) => {
    if (a.key === '__none__') return 1
    if (b.key === '__none__') return -1
    return String(a.label).localeCompare(String(b.label))
  })

  return result
}

/**
 * Epics are containers, not work items, so they do not get cards on the board
 * -- they live in the epic rail and in the list's tree, the way Jira does it.
 */
export const boardTasks = computed(() => visibleTasks.value.filter((t) => !t.is_group))

/** Every label currently in play, for the filter menu. */
export const availableTags = computed(() => {
  const seen = new Set()
  for (const task of tasks.value) for (const tag of task.tags || []) seen.add(tag)
  return [...seen].sort()
})

export async function loadEpics(project) {
  epics.value = (await api.getProjectEpics(project)) || []
  return epics.value
}

/**
 * Hierarchy for the list view.
 *
 * Tasks nest through `parent_task`, and ERPNext only allows a group task as a
 * parent, so the tree is naturally shallow -- but this walks it to any depth.
 * A task whose parent is filtered out is promoted to the root rather than
 * disappearing with it.
 */
export function buildTaskTree(rows, sorter) {
  const byName = new Map(rows.map((t) => [t.name, t]))
  const children = new Map()
  const roots = []

  for (const task of rows) {
    const parent = task.parent_task
    if (parent && byName.has(parent)) {
      if (!children.has(parent)) children.set(parent, [])
      children.get(parent).push(task)
    } else {
      roots.push(task)
    }
  }

  for (const list of children.values()) list.sort(sorter)
  roots.sort(sorter)

  return { roots, children }
}

/** Depth-first flatten, honouring which branches the user has collapsed. */
export function flattenTree({ roots, children }, collapsed) {
  const out = []

  const walk = (task, depth) => {
    const kids = children.get(task.name) || []
    out.push({ task, depth, hasChildren: kids.length > 0, childCount: kids.length })
    if (kids.length && !collapsed.has(task.name)) {
      for (const kid of kids) walk(kid, depth + 1)
    }
  }

  for (const root of roots) walk(root, 0)
  return out
}
