import { computed, reactive } from 'vue'
import { createResource } from 'frappe-ui'

const API = 'project_board.api'

export const session = reactive({
  boot: createResource({
    url: `${API}.get_boot_info`,
    cache: 'pb:boot',
    auto: false,
  }),
})

export const user = computed(() => session.boot.data?.user || {})
export const options = computed(() => session.boot.data?.options || {})
export const permissions = computed(() => ({
  canCreateProject: session.boot.data?.can_create_project ?? false,
  canCreateTask: session.boot.data?.can_create_task ?? false,
  canSubmitTimesheet: session.boot.data?.can_submit_timesheet ?? false,
  canPostUpdate: session.boot.data?.can_post_update ?? false,
  canRepeatTasks: session.boot.data?.can_repeat_tasks ?? false,
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

export function logout() {
  window.location.href = '/api/method/logout'
}
