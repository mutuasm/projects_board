import { call } from 'frappe-ui'

const NS = 'project_board.api'

export const api = {
  // projects
  getProjects: (params) => call(`${NS}.get_projects`, params),
  getProject: (name) => call(`${NS}.get_project`, { name }),
  createProject: (values) => call(`${NS}.create_project`, values),
  updateProject: (name, values) => call(`${NS}.update_project`, { name, values }),
  closeProject: (name, { status, note, cancelOpenTasks = false }) =>
    call(`${NS}.close_project`, {
      name,
      status,
      note,
      cancel_open_tasks: cancelOpenTasks ? 1 : 0,
    }),
  setProjectMembers: (project, users) =>
    call(`${NS}.set_project_members`, { project, users }),
  getProjectStats: (project) => call(`${NS}.get_project_stats`, { project }),
  getProjectEpics: (project) => call(`${NS}.get_project_epics`, { project }),
  getActivity: (project, limit = 30) => call(`${NS}.get_activity`, { project, limit }),

  // tasks
  getTasks: (params) => call(`${NS}.get_tasks`, params),
  getMyDoneTasks: (start = 0, limit = 50) =>
    call(`${NS}.get_my_done_tasks`, { start, limit }),
  getMyTasks: (includeCompleted = 0, completedDays = 0) =>
    call(`${NS}.get_my_tasks`, {
      include_completed: includeCompleted,
      completed_days: completedDays,
    }),
  getTask: (name) => call(`${NS}.get_task`, { name }),
  createTask: (values) => call(`${NS}.create_task`, values),
  updateTask: (name, values) => call(`${NS}.update_task`, { name, values }),
  moveTask: (name, status) => call(`${NS}.move_task`, { name, status }),
  deleteTask: (name) => call(`${NS}.delete_task`, { name }),
  setAssignees: (task, users) => call(`${NS}.set_assignees`, { task, users }),
  setDependencies: (task, dependsOn) =>
    call(`${NS}.set_task_dependencies`, { task, depends_on: dependsOn }),

  // collaboration
  addComment: (doctype, name, content) =>
    call(`${NS}.add_comment`, { doctype, name, content }),
  deleteComment: (name) => call(`${NS}.delete_comment`, { name }),
  getComments: (doctype, name) => call(`${NS}.get_comments`, { doctype, name }),

  // people
  searchUsers: (txt = '', limit = 20) => call(`${NS}.search_users`, { txt, limit }),

  // labels (native Tag / Tag Link)
  getAllTags: (txt = '') => call(`${NS}.get_all_tags`, { txt }),
  setTaskTags: (task, tags) => call(`${NS}.set_task_tags`, { task, tags }),

  // project templates + status updates (native Projects doctypes)
  getProjectTemplates: () => call(`${NS}.get_project_templates`),
  getProjectUpdates: (project, limit = 20) =>
    call(`${NS}.get_project_updates`, { project, limit }),
  addProjectUpdate: (project, status) =>
    call(`${NS}.add_project_update`, { project, status }),

  // scheduled check-ins (ERPNext progress collection)
  getCheckinSettings: (project) => call(`${NS}.get_checkin_settings`, { project }),
  saveCheckinSettings: (project, values) =>
    call(`${NS}.save_checkin_settings`, { project, values }),
  sendCheckinNow: (project) => call(`${NS}.send_checkin_now`, { project }),

  // reviews
  getReviewQueue: () => call(`${NS}.get_review_queue`),

  // recurring tasks (Frappe Auto Repeat)
  setTaskRepeat: (task, rule) => call(`${NS}.set_task_repeat`, { task, rule }),
  stopTaskRepeat: (task) => call(`${NS}.stop_task_repeat`, { task }),

  // live updates + inbox
  getTaskRows: (names) => call(`${NS}.get_task_rows`, { names }),
  getNotifications: (limit = 30, start = 0) =>
    call(`${NS}.get_notifications`, { limit, start }),
  markNotificationsRead: (names = null) =>
    call(`${NS}.mark_notifications_read`, names ? { names } : {}),

  // attachments
  deleteAttachment: (name) => call(`${NS}.delete_attachment`, { name }),

  // dependencies
  searchTasks: (params) => call(`${NS}.search_tasks`, params),

  // bulk actions
  bulkUpdateTasks: (names, values) =>
    call(`${NS}.bulk_update_tasks`, { names, values }),
  bulkDeleteTasks: (names) => call(`${NS}.bulk_delete_tasks`, { names }),

  // saved views (native List Filter)
  getSavedViews: () => call(`${NS}.get_saved_views`),
  saveView: (label, filters) => call(`${NS}.save_view`, { label, filters }),
  deleteSavedView: (name) => call(`${NS}.delete_saved_view`, { name }),

  // audit trail (native Version)
  getTaskHistory: (task, limit = 30) => call(`${NS}.get_task_history`, { task, limit }),

  // time
  logTime: (payload) => call(`${NS}.log_time`, payload),
  getTimeLogs: (task) => call(`${NS}.get_time_logs`, { task }),
}

export default api
