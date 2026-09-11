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
| Labels | `Tag` / `Tag Link` (`_user_tags`) |
| Project templates | `Project Template` + `Project Template Task` |
| Status check-ins | `Project Update` |
| Saved views | `List Filter` (per user) |
| Task history | `Version` (Frappe's audit trail) |
| Costing & billing | `Project` rollups from Timesheet, Sales Order, Purchase Invoice |

### Desk integration

The app adds **no tile of its own** to the apps screen. On install it repoints the
existing ERPNext **Projects** workspace at `/project-board`, so Projects stays the
single entry point. It also enables `track_changes` on Task (via a Property
Setter) so Frappe writes the Version records the task history reads. Both are
reapplied after `bench migrate` and undone by `bench uninstall-app`.

### Screens

- **My Work** — every task assigned to you across projects, bucketed by due date.
- **Projects** — portfolio of projects as cards or a table, with live task rollups.
- **Board** — drag-and-drop Kanban; dropping a card writes `Task.status`.
- **List** — grouped table with inline status / priority editing.
- **Timeline** — Gantt bars from the expected start/end dates.
- **Overview** — completion meter, status/priority breakdowns, workload, costing and billing.
- **Updates** — post and read native Project Updates as a status timeline.

### Working in it

- **Epics** — `is_group` tasks are containers, not cards. They live in the board's
  epic rail (colour, done/total, progress) and head their own branch in the list
  tree; every child card carries a coloured epic chip that filters the board.
- **Tree list** — the list nests children under their parent to any depth, with
  expand/collapse per branch. Status and flat views are a click away.
- **Swimlanes** — group the board by assignee, priority, type or epic.
- **Command palette** — `⌘K` to jump to a project, view or task; `?` lists every shortcut.
- **Bulk actions** — multi-select in the list to restatus, reprioritise, reassign or delete.
- **Saved views** — name a filter set; it follows you across devices.
- **Timer** — start/stop on a task, filed as a Timesheet entry on stop.
- **Labels, blockers, attachments** — all editable inline from the task panel.
- **Dark mode** — light / dark / system, remembered per browser.

### On a phone

The portal is responsive down to ~360px, not a separate mobile build:

- the sidebar becomes a slide-in drawer behind a menu button;
- the board keeps its columns, one snapped per screen, and a **long press**
  starts a drag so a normal swipe still scrolls the column;
- the List view collapses from a table into stacked cards;
- board filters collapse into a single row plus a Filters sheet;
- the task detail panel opens as a full-screen sheet;
- "New task" becomes a floating action button;
- `env(safe-area-inset-*)` is honoured for notches and home indicators.

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
