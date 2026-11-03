/**
 * Presentation-only mappings for the native ERPNext Select values.
 * Anything not listed here still renders, just with the neutral fallback.
 */

export const STATUS_STYLES = {
  Open: { theme: 'gray', dot: 'bg-gray-400', label: 'To Do' },
  Working: { theme: 'blue', dot: 'bg-blue-500', label: 'In Progress' },
  'Pending Review': { theme: 'orange', dot: 'bg-orange-500', label: 'In Review' },
  Overdue: { theme: 'red', dot: 'bg-red-500', label: 'Overdue' },
  Completed: { theme: 'green', dot: 'bg-green-500', label: 'Done' },
  Cancelled: { theme: 'gray', dot: 'bg-gray-300', label: 'Cancelled' },
  Template: { theme: 'gray', dot: 'bg-gray-300', label: 'Template' },
}

export const PRIORITY_STYLES = {
  Urgent: { theme: 'red', icon: 'chevrons-up', text: 'text-ink-red-3' },
  High: { theme: 'orange', icon: 'chevron-up', text: 'text-ink-amber-3' },
  Medium: { theme: 'blue', icon: 'minus', text: 'text-ink-blue-3' },
  Low: { theme: 'gray', icon: 'chevron-down', text: 'text-ink-gray-5' },
}

export const PRIORITY_ORDER = ['Urgent', 'High', 'Medium', 'Low']

export const PROJECT_STATUS_STYLES = {
  Open: { theme: 'blue' },
  'On hold': { theme: 'orange' },
  Completed: { theme: 'green' },
  Cancelled: { theme: 'gray' },
}

/** Columns we never render on the board even if meta lists them. */
export const HIDDEN_STATUSES = ['Template']

export function statusStyle(status) {
  return STATUS_STYLES[status] || { theme: 'gray', dot: 'bg-gray-400', label: status }
}

export function statusLabel(status) {
  return statusStyle(status).label || status
}

export function priorityStyle(priority) {
  return (
    PRIORITY_STYLES[priority] || { theme: 'gray', icon: 'minus', text: 'text-ink-gray-5' }
  )
}

export function sortByPriority(a, b) {
  const ai = PRIORITY_ORDER.indexOf(a.priority)
  const bi = PRIORITY_ORDER.indexOf(b.priority)
  return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
}


/**
 * Task Type is a free-form ERPNext doctype, so this only styles the types a
 * site is likely to have and falls back to the first three letters otherwise.
 */
const TASK_TYPE_STYLES = {
  Bug: { short: 'BUG', text: 'text-ink-red-3' },
  Story: { short: 'STORY', text: 'text-ink-green-3' },
  Epic: { short: 'EPIC', text: 'text-ink-blue-3' },
  Task: { short: 'TASK', text: 'text-ink-gray-5' },
  'Sub-task': { short: 'SUB', text: 'text-ink-gray-5' },
}

export function taskTypeStyle(type) {
  if (!type) return { short: '—', text: 'text-ink-gray-4' }
  return (
    TASK_TYPE_STYLES[type] || {
      short: type.slice(0, 4).toUpperCase(),
      text: 'text-ink-gray-5',
    }
  )
}

/**
 * ERPNext Projects have no colour field, so derive a stable one from the name:
 * the same project gets the same swatch in the sidebar, header and task panel.
 */
const PROJECT_COLORS = [
  '#d946ef', // fuchsia
  '#16a34a', // green
  '#2563eb', // blue
  '#f97316', // orange
  '#8b5cf6', // violet
  '#0891b2', // cyan
  '#e11d48', // rose
  '#ca8a04', // amber
]

export function projectColor(name) {
  let hash = 0
  for (const char of String(name || '')) hash = (hash * 31 + char.charCodeAt(0)) | 0
  return PROJECT_COLORS[Math.abs(hash) % PROJECT_COLORS.length]
}
