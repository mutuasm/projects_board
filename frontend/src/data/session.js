import { computed, reactive } from 'vue'
import { call, createResource, deleteLocal } from 'frappe-ui'

const API = 'project_board.api'
const BOOT_CACHE = 'pb:boot'

export const session = reactive({
  boot: createResource({
    url: `${API}.get_boot_info`,
    cache: BOOT_CACHE,
    auto: false,
  }),
})

export const user = computed(() => session.boot.data?.user || {})
export const options = computed(() => session.boot.data?.options || {})
export const brand = computed(() => session.boot.data?.brand || { name: 'Project Board', logo: null })
export const permissions = computed(() => ({
  canCreateProject: session.boot.data?.can_create_project ?? false,
  canCreateTask: session.boot.data?.can_create_task ?? false,
  canSubmitTimesheet: session.boot.data?.can_submit_timesheet ?? false,
  canPostUpdate: session.boot.data?.can_post_update ?? false,
  canRepeatTasks: session.boot.data?.can_repeat_tasks ?? false,
  isSystemManager: session.boot.data?.is_system_manager ?? false,
  isManager: session.boot.data?.is_manager ?? false,
}))

/** Board columns = native Task status options, minus the template state. */
export const boardStatuses = computed(() => options.value.task_statuses || [])
export const taskPriorities = computed(() => options.value.task_priorities || [])
export const taskTypes = computed(() => options.value.task_types || [])
export const projectStatuses = computed(() => options.value.project_statuses || [])
export const projectTypes = computed(() => options.value.project_types || [])
export const activityTypes = computed(() => options.value.activity_types || [])
export const departments = computed(() => options.value.departments || [])

let loggingOut = false

/**
 * Frappe only accepts logout as a POST (with the CSRF token), so a plain link
 * to /api/method/logout is refused. The cached boot holds this user's details
 * and goes too, so the next person on this browser never sees them.
 */
export async function logout() {
  if (loggingOut) return
  loggingOut = true
  try {
    await call('logout')
  } catch {
    // an expired session is already logged out; the login page sorts out the rest
  }
  await deleteLocal(JSON.stringify([BOOT_CACHE])).catch(() => {})
  window.location.href = '/login?redirect-to=/project-board'
}
