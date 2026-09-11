import { call } from 'frappe-ui'

const NS = 'project_board.api'

export const api = {
  // projects
  getProjects: (params) => call(`${NS}.get_projects`, params),
  getProject: (name) => call(`${NS}.get_project`, { name }),
  createProject: (values) => call(`${NS}.create_project`, values),
  updateProject: (name, values) => call(`${NS}.update_project`, { name, values }),
  setProjectMembers: (project, users) =>
    call(`${NS}.set_project_members`, { project, users }),
  getProjectStats: (project) => call(`${NS}.get_project_stats`, { project }),
  getActivity: (project, limit = 30) => call(`${NS}.get_activity`, { project, limit }),

  // tasks
  getTasks: (params) => call(`${NS}.get_tasks`, params),
  getMyTasks: (includeCompleted = 0) =>
    call(`${NS}.get_my_tasks`, { include_completed: includeCompleted }),
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

  // time
  logTime: (payload) => call(`${NS}.log_time`, payload),
  getTimeLogs: (task) => call(`${NS}.get_time_logs`, { task }),
}

export default api
