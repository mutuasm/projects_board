## Project Board

A Jira-style project management portal for ERPNext Projects, built the same way
as the Frappe HR portal: a Vue 3 + frappe-ui single-page app served by the
Frappe web server at `/project-board`.

It introduces **no custom doctypes**. Every screen reads and writes the native
ERPNext records, so anything you do in the portal shows up in the desk UI and
vice versa:

| Portal concept | Native field / doctype |
| --- | --- |
| Board column | `Task.status` |
| Card priority | `Task.priority` |
| Assignee | `_assign` (ToDo-backed assignment) |
| Epic / parent | `Task.parent_task` + `Task.is_group` |
| Story points | `Task.task_weight` |
| Label | `Task.type` → `Task Type` |
| Due date / start | `Task.exp_end_date` / `Task.exp_start_date` |
| Milestone | `Task.is_milestone` |
| Blocked by | `Task Depends On` |
| Comments | `Comment` |
| Attachments | `File` |
| Time logging | `Timesheet` + `Timesheet Detail` |
| Project team | `Project.users` → `Project User` |
| Progress | `Project.percent_complete` (native % complete method) |

### Screens

- **My Work** — every task assigned to you across projects, bucketed by due date.
- **Projects** — portfolio of projects as cards or a table, with live task rollups.
- **Board** — drag-and-drop Kanban; dropping a card writes `Task.status`.
- **List** — grouped table with inline status / priority editing.
- **Timeline** — Gantt bars from the expected start/end dates.
- **Overview** — completion meter, status and priority breakdowns, workload, activity.

### Install

```bash
bench get-app project_board <repo-url>
bench --site <site> install-app project_board
```

### Development

```bash
cd apps/project_board/frontend
yarn install
yarn dev        # vite on :8081, proxying /api to the bench
```

Then open `http://<site>:8081/project-board`.

### Build

```bash
cd apps/project_board/frontend
yarn build
```

The build writes to `project_board/public/frontend` and copies the entry point to
`project_board/www/project-board.html`.

### License

MIT
