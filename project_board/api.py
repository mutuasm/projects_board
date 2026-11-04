"""Whitelisted endpoints backing the Project Board SPA.

Everything here reads and writes *native* ERPNext Projects doctypes --
Project, Task, Project User, Task Type, Project Type, Timesheet -- plus the
core Frappe primitives Task already relies on (ToDo based assignment via
``_assign``, Comment, File). No custom doctypes are introduced, so the desk UI
and the board stay in sync in both directions.
"""

import json

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign_to_add
from frappe.desk.form.assign_to import remove as assign_to_remove
from frappe.query_builder.functions import Count
from frappe.utils import add_days, cint, flt, get_datetime, getdate, now_datetime, nowtime, today

# Fields the board is allowed to write on a Task. Anything else has to go
# through the desk form, which keeps this endpoint from becoming a generic
# "set any field" hole.
TASK_WRITABLE_FIELDS = {
	"subject",
	"status",
	"priority",
	"description",
	"exp_start_date",
	"exp_end_date",
	"expected_time",
	"task_weight",
	"progress",
	"type",
	"parent_task",
	"is_group",
	"is_milestone",
	"color",
	"department",
	"project",
	"review_date",
	"closing_date",
}

PROJECT_WRITABLE_FIELDS = {
	"project_name",
	"status",
	"priority",
	"is_active",
	"project_type",
	"expected_start_date",
	"expected_end_date",
	"percent_complete_method",
	"percent_complete",
	"notes",
	"customer",
	"department",
	"cost_center",
	"estimated_costing",
	"project_template",
	"holiday_list",
	"sales_order",
}

TASK_LIST_FIELDS = [
	"name",
	"subject",
	"project",
	"status",
	"priority",
	"type",
	"color",
	"parent_task",
	"is_group",
	"is_milestone",
	"exp_start_date",
	"exp_end_date",
	"expected_time",
	"actual_time",
	"task_weight",
	"progress",
	"completed_by",
	"completed_on",
	"review_date",
	"closing_date",
	"department",
	"_assign",
	"_user_tags",
	"depends_on_tasks",
	"modified",
	"creation",
	"owner",
	"idx",
]

def _task_list_fields() -> list[str]:
	"""TASK_LIST_FIELDS, plus the Auto Repeat link once install has added it.

	The field only exists after `bench migrate` has run this app's
	after_migrate, so asking for it before then would break every list.
	"""
	if frappe.get_meta("Task").has_field("auto_repeat"):
		return [*TASK_LIST_FIELDS, "auto_repeat"]
	return TASK_LIST_FIELDS


CLOSED_PROJECT_STATUSES = ("Completed", "Cancelled")

# Auto Repeat's own frequencies, in the order the board offers them.
REPEAT_FREQUENCIES = ("Daily", "Weekly", "Fortnightly", "Monthly", "Quarterly", "Half-yearly", "Yearly")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# ERPNext's "progress collection" settings on Project. Written only through
# save_checkin_settings(), which validates them, never the generic update.
CHECKIN_FIELDS = (
	"collect_progress",
	"frequency",
	"daily_time_to_send",
	"first_email",
	"second_email",
	"day_to_send",
	"weekly_time_to_send",
	"subject",
	"message",
)
# ERPNext also offers "Hourly", but its hourly_reminder() checks
# `now >= from_time or now <= to_time`, which is always true - it would email
# the team every hour around the clock. So the board does not offer it.
CHECKIN_FREQUENCIES = ("Daily", "Twice Daily", "Weekly")

# "Template" only exists to support Project Templates; it is not a workflow
# state a human ever drags a card into.
HIDDEN_TASK_STATUSES = {"Template"}


def check_app_permission():
	"""Gate the app tile on the /apps screen."""
	if frappe.session.user == "Administrator":
		return True

	return bool(
		frappe.has_permission("Project", ptype="read") and frappe.has_permission("Task", ptype="read")
	)


# ---------------------------------------------------------------------------
# boot / metadata
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_boot_info():
	"""Everything the SPA needs once, at startup."""
	# Administrator has no User row on some sites, so fall back to the session.
	user = frappe.db.get_value(
		"User",
		frappe.session.user,
		["name", "full_name", "user_image", "email"],
		as_dict=True,
	) or frappe._dict(
		name=frappe.session.user,
		full_name=frappe.utils.get_fullname() or frappe.session.user,
		user_image=None,
		email=frappe.session.user,
	)

	return {
		"user": {
			"name": user.name,
			"full_name": user.full_name or user.name,
			"user_image": user.user_image,
			"email": user.email,
		},
		"is_manager": "Projects Manager" in frappe.get_roles(),
		"can_create_project": frappe.has_permission("Project", ptype="create"),
		"can_create_task": frappe.has_permission("Task", ptype="create"),
		"can_submit_timesheet": frappe.has_permission("Timesheet", ptype="create"),
		"can_post_update": frappe.has_permission("Project Update", ptype="create"),
		# false until `bench migrate` has switched Auto Repeat on for Task
		"can_repeat_tasks": _repeat_ready(),
		"is_system_manager": "System Manager" in frappe.get_roles(),
		"options": get_field_options(),
	}


def _select_options(doctype: str, fieldname: str) -> list[str]:
	"""Read Select options off the live meta so customised options come through."""
	df = frappe.get_meta(doctype).get_field(fieldname)
	if not df or not df.options:
		return []
	return [o.strip() for o in df.options.split("\n") if o.strip()]


@frappe.whitelist()
def get_field_options():
	task_statuses = [s for s in _select_options("Task", "status") if s not in HIDDEN_TASK_STATUSES]

	return {
		"task_statuses": task_statuses,
		"task_priorities": _select_options("Task", "priority"),
		"project_statuses": _select_options("Project", "status"),
		"project_priorities": _select_options("Project", "priority"),
		"percent_complete_methods": _select_options("Project", "percent_complete_method"),
		"task_types": frappe.get_all("Task Type", pluck="name", order_by="name"),
		"project_types": frappe.get_all("Project Type", pluck="name", order_by="name"),
		"activity_types": frappe.get_all("Activity Type", pluck="name", order_by="name"),
		"departments": frappe.get_all("Department", pluck="name", order_by="name", limit_page_length=200),
	}


# ---------------------------------------------------------------------------
# users / assignment
# ---------------------------------------------------------------------------


def _user_map(emails: set[str]) -> dict[str, dict]:
	emails = {e for e in emails if e}
	if not emails:
		return {}

	users = frappe.get_all(
		"User",
		filters={"name": ("in", list(emails))},
		fields=["name", "full_name", "user_image"],
		ignore_permissions=True,
	)
	return {u.name: u for u in users}


def _parse_assign(value) -> list[str]:
	if not value:
		return []
	if isinstance(value, list):
		return value
	try:
		return json.loads(value) or []
	except (ValueError, TypeError):
		return []


def _attach_assignees(rows: list[dict]) -> list[dict]:
	"""Replace the raw ``_assign`` JSON blob with resolved user objects."""
	wanted: set[str] = set()
	for row in rows:
		row["assignees"] = _parse_assign(row.get("_assign"))
		wanted.update(row["assignees"])

	users = _user_map(wanted)
	for row in rows:
		row["assignees"] = [
			users.get(email) or {"name": email, "full_name": email, "user_image": None}
			for email in row["assignees"]
		]
		row.pop("_assign", None)
		row["tags"] = _parse_tags(row.pop("_user_tags", None))

	return rows


def _parse_tags(value) -> list[str]:
	"""`_user_tags` is a comma-joined string with a leading comma."""
	if not value:
		return []
	return [t for t in str(value).split(",") if t.strip()]


def _attach_comment_counts(rows: list[dict]) -> list[dict]:
	"""Task has no comment-count column, so roll it up from Comment in one query."""
	names = [r["name"] for r in rows]
	if not names:
		return rows

	Comment = frappe.qb.DocType("Comment")
	counts = dict(
		(
			frappe.qb.from_(Comment)
			.select(Comment.reference_name, Count(Comment.name))
			.where(
				(Comment.reference_doctype == "Task")
				& (Comment.reference_name.isin(names))
				& (Comment.comment_type == "Comment")
			)
			.groupby(Comment.reference_name)
		).run()
	)

	for row in rows:
		row["comment_count"] = counts.get(row["name"], 0)
	return rows


@frappe.whitelist()
def search_users(txt: str = "", limit: int = 20):
	filters = [
		["enabled", "=", 1],
		["user_type", "=", "System User"],
		["name", "not in", ["Administrator", "Guest"]],
	]
	if txt:
		return frappe.get_all(
			"User",
			or_filters=[["full_name", "like", f"%{txt}%"], ["name", "like", f"%{txt}%"]],
			filters=filters,
			fields=["name", "full_name", "user_image"],
			limit_page_length=cint(limit),
			order_by="full_name",
			ignore_permissions=True,
		)

	return frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image"],
		limit_page_length=cint(limit),
		order_by="full_name",
		ignore_permissions=True,
	)


@frappe.whitelist()
def set_assignees(task: str, users):
	"""Sync a Task's assignees. Uses the native ToDo-backed assignment."""
	frappe.has_permission("Task", ptype="write", doc=task, throw=True)

	if isinstance(users, str):
		users = json.loads(users)
	users = [u for u in (users or []) if u]

	current = set(_parse_assign(frappe.db.get_value("Task", task, "_assign")))
	wanted = set(users)

	for user in current - wanted:
		assign_to_remove("Task", task, user)

	to_add = wanted - current
	if to_add:
		assign_to_add(
			{
				"doctype": "Task",
				"name": task,
				"assign_to": list(to_add),
				"description": frappe.db.get_value("Task", task, "subject"),
			}
		)

	return _attach_assignees(
		[{"name": task, "_assign": frappe.db.get_value("Task", task, "_assign")}]
	)[0]["assignees"]


# ---------------------------------------------------------------------------
# projects
# ---------------------------------------------------------------------------


def _outgoing_email_configured() -> bool:
	"""Whether ERPNext will be able to send the Project collaboration invite.

	Project.send_welcome_email() calls frappe.sendmail() for every new Project
	User, which raises OutgoingEmailError on a site with no default outgoing
	account -- that would make the portal unable to create a project at all.
	"""
	from frappe.email.doctype.email_account.email_account import EmailAccount

	try:
		return bool(EmailAccount.find_default_outgoing())
	except Exception:
		return False


def _append_members(doc, users):
	"""Add Project User rows, suppressing the invite mail when it cannot be sent."""
	skip_welcome_email = not _outgoing_email_configured()
	for user in users or []:
		doc.append("users", {"user": user, "welcome_email_sent": 1 if skip_welcome_email else 0})


@frappe.whitelist()
def get_projects(status: str | None = None, search: str | None = None, only_mine: int = 0):
	"""Project cards for the portfolio screen, with live task rollups."""
	filters = []
	if status:
		filters.append(["status", "=", status])
	if search:
		filters.append(["project_name", "like", f"%{search}%"])

	if cint(only_mine):
		mine = frappe.get_all(
			"Project User",
			filters={"user": frappe.session.user, "parenttype": "Project"},
			pluck="parent",
		)
		if not mine:
			return []
		filters.append(["name", "in", mine])

	projects = frappe.get_list(
		"Project",
		filters=filters,
		fields=[
			"name",
			"project_name",
			"status",
			"priority",
			"is_active",
			"project_type",
			"percent_complete",
			"percent_complete_method",
			"expected_start_date",
			"expected_end_date",
			"actual_start_date",
			"actual_end_date",
			"customer",
			"department",
			"company",
			"estimated_costing",
			"total_costing_amount",
			"total_billable_amount",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=0,
	)

	if not projects:
		return []

	names = [p.name for p in projects]
	counts = _task_counts_by_project(names)
	members = _members_by_project(names)

	for project in projects:
		project["task_counts"] = counts.get(project.name, {})
		project["members"] = members.get(project.name, [])
		project["open_tasks"] = sum(
			count
			for status_, count in project["task_counts"].items()
			if status_ not in ("Completed", "Cancelled", "Template")
		)
		project["total_tasks"] = sum(project["task_counts"].values())

	return projects


def _task_counts_by_project(projects: list[str]) -> dict[str, dict[str, int]]:
	if not projects:
		return {}

	Task = frappe.qb.DocType("Task")
	rows = (
		frappe.qb.from_(Task)
		.select(Task.project, Task.status, Count(Task.name).as_("count"))
		.where(Task.project.isin(projects))
		.groupby(Task.project, Task.status)
	).run(as_dict=True)

	out: dict[str, dict[str, int]] = {}
	for row in rows:
		out.setdefault(row.project, {})[row.status] = row.count
	return out


def _members_by_project(projects: list[str]) -> dict[str, list[dict]]:
	if not projects:
		return {}

	rows = frappe.get_all(
		"Project User",
		filters={"parent": ("in", projects), "parenttype": "Project"},
		fields=["parent", "user", "full_name", "image"],
		ignore_permissions=True,
	)

	out: dict[str, list[dict]] = {}
	for row in rows:
		out.setdefault(row.parent, []).append(
			{"name": row.user, "full_name": row.full_name or row.user, "user_image": row.image}
		)
	return out


@frappe.whitelist()
def get_project(name: str):
	frappe.has_permission("Project", ptype="read", doc=name, throw=True)
	doc = frappe.get_doc("Project", name)

	return {
		"doc": doc.as_dict(),
		"members": [
			{"name": u.user, "full_name": u.full_name or u.user, "user_image": u.image}
			for u in doc.users
		],
		"task_counts": _task_counts_by_project([name]).get(name, {}),
		"can_write": bool(frappe.has_permission("Project", ptype="write", doc=name)),
	}


@frappe.whitelist()
def create_project(**kwargs):
	frappe.has_permission("Project", ptype="create", throw=True)

	values = {k: v for k, v in kwargs.items() if k in PROJECT_WRITABLE_FIELDS and v not in (None, "")}
	if not values.get("project_name"):
		frappe.throw(_("Project Name is required"))

	doc = frappe.new_doc("Project")
	doc.update(values)

	members = kwargs.get("members")
	if isinstance(members, str):
		members = json.loads(members)
	_append_members(doc, members)

	doc.insert()
	return doc.name


@frappe.whitelist()
def update_project(name: str, values):
	frappe.has_permission("Project", ptype="write", doc=name, throw=True)

	if isinstance(values, str):
		values = json.loads(values)

	unknown = set(values) - PROJECT_WRITABLE_FIELDS
	if unknown:
		frappe.throw(_("Cannot update field(s) from the board: {0}").format(", ".join(sorted(unknown))))

	doc = frappe.get_doc("Project", name)
	doc.update(values)
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def set_project_members(project: str, users):
	frappe.has_permission("Project", ptype="write", doc=project, throw=True)

	if isinstance(users, str):
		users = json.loads(users)

	doc = frappe.get_doc("Project", project)
	doc.users = []
	_append_members(doc, users)
	doc.save()

	return [{"name": u.user, "full_name": u.full_name or u.user, "user_image": u.image} for u in doc.users]


@frappe.whitelist()
def close_project(name: str, status: str = "Completed", note: str | None = None, cancel_open_tasks: int = 0):
	"""Close a project as Completed or Cancelled.

	Optionally cancels the tasks still open in it and posts the closing note as
	a Project Update. All of it happens in one request, so a task that refuses
	to cancel leaves the project untouched.
	"""
	frappe.has_permission("Project", ptype="write", doc=name, throw=True)

	if status not in CLOSED_PROJECT_STATUSES:
		frappe.throw(_("A project can only be closed as {0}").format(" or ".join(CLOSED_PROJECT_STATUSES)))

	if cint(cancel_open_tasks):
		open_tasks = frappe.get_all(
			"Task",
			filters={"project": name, "status": ("not in", ["Completed", "Cancelled", "Template"])},
			pluck="name",
		)
		for task in open_tasks:
			doc = frappe.get_doc("Task", task)
			doc.check_permission("write")
			doc.status = "Cancelled"
			doc.save()

	# Loaded after the tasks: each task save rolls its progress up into the project.
	doc = frappe.get_doc("Project", name)
	doc.status = status
	doc.save()

	# Unless the method is Manual, ERPNext recomputes the status from task
	# progress on save and only keeps Completed at 100%. Refuse rather than
	# report a close that did not stick.
	if doc.status != status:
		frappe.throw(
			_(
				"ERPNext sets this project's status from its tasks ({0}), which are {1}% done. "
				"Close the remaining tasks first, or close the project as Cancelled."
			).format(_(doc.percent_complete_method), flt(doc.percent_complete, 1))
		)

	if (note or "").strip():
		add_project_update(name, note)

	return doc.as_dict()


# ---------------------------------------------------------------------------
# tasks
# ---------------------------------------------------------------------------


def _build_task_filters(
	project=None,
	statuses=None,
	priorities=None,
	assignee=None,
	task_type=None,
	parent_task=None,
	search=None,
	overdue_only=0,
	include_completed=1,
):
	filters = [["is_template", "=", 0]]
	or_filters = []

	if project:
		filters.append(["project", "=", project])
	if task_type:
		filters.append(["type", "=", task_type])
	if parent_task:
		filters.append(["parent_task", "=", parent_task])
	if search:
		or_filters = [["subject", "like", f"%{search}%"], ["name", "like", f"%{search}%"]]

	if isinstance(statuses, str):
		statuses = json.loads(statuses) if statuses.startswith("[") else [statuses]
	if statuses:
		filters.append(["status", "in", statuses])
	elif not cint(include_completed):
		filters.append(["status", "not in", ["Completed", "Cancelled"]])

	if isinstance(priorities, str):
		priorities = json.loads(priorities) if priorities.startswith("[") else [priorities]
	if priorities:
		filters.append(["priority", "in", priorities])

	if assignee:
		filters.append(["_assign", "like", f"%{assignee}%"])

	if cint(overdue_only):
		filters.append(["exp_end_date", "<", now_datetime()])
		filters.append(["status", "not in", ["Completed", "Cancelled"]])

	return filters, or_filters


@frappe.whitelist()
def get_tasks(
	project: str | None = None,
	statuses=None,
	priorities=None,
	assignee: str | None = None,
	task_type: str | None = None,
	parent_task: str | None = None,
	search: str | None = None,
	overdue_only: int = 0,
	include_completed: int = 1,
	order_by: str = "modified desc",
	limit: int = 0,
):
	"""The board / list / timeline all pull from here."""
	filters, or_filters = _build_task_filters(
		project=project,
		statuses=statuses,
		priorities=priorities,
		assignee=assignee,
		task_type=task_type,
		parent_task=parent_task,
		search=search,
		overdue_only=overdue_only,
		include_completed=include_completed,
	)

	tasks = frappe.get_list(
		"Task",
		filters=filters,
		or_filters=or_filters or None,
		fields=_task_list_fields(),
		order_by=order_by,
		limit_page_length=cint(limit) or 0,
	)

	return _attach_epics(_attach_blocked_state(_attach_comment_counts(_attach_assignees(tasks))))


@frappe.whitelist()
def get_my_tasks(include_completed: int = 0, completed_days: int = 0):
	"""Every task the logged-in user is assigned to, across the projects they can see.

	`completed_days` keeps finished tasks from that recent window even when
	`include_completed` is off, for the page's "recently completed" list. Older
	finished work is paged in through get_my_done_tasks().
	"""
	open_assignments, names = _my_task_names()
	if not names:
		return []

	filters = [["name", "in", list(names)], ["is_template", "=", 0]]
	or_filters = None
	if not cint(include_completed):
		if cint(completed_days):
			or_filters = [
				["status", "not in", ["Completed", "Cancelled"]],
				["modified", ">=", add_days(now_datetime(), -cint(completed_days))],
			]
		else:
			filters.append(["status", "not in", ["Completed", "Cancelled"]])

	tasks = frappe.get_list(
		"Task",
		filters=filters,
		or_filters=or_filters,
		fields=_task_list_fields(),
		order_by="exp_end_date asc, priority desc, modified desc",
		limit_page_length=0,
	)

	return _my_task_rows(tasks, open_assignments)


@frappe.whitelist()
def get_my_done_tasks(start: int = 0, limit: int = 50):
	"""Finished tasks you were on, newest first, a page at a time ("Show done")."""
	open_assignments, names = _my_task_names()
	if not names:
		return []

	tasks = frappe.get_list(
		"Task",
		filters=[
			["name", "in", list(names)],
			["is_template", "=", 0],
			["status", "in", ["Completed", "Cancelled"]],
		],
		fields=_task_list_fields(),
		order_by="modified desc",
		limit_start=cint(start),
		limit_page_length=min(cint(limit) or 50, 200),
	)
	return _my_task_rows(tasks, open_assignments)


def _my_task_names() -> tuple[set[str], set[str]]:
	"""(tasks with an open assignment for you, every task you were assigned to).

	`_assign` only lists *open* assignments, and ERPNext closes an assignment
	when its task is completed or the assignee marks their part done - so the
	ToDo table is read too. A cancelled ToDo is an un-assignment.
	"""
	user = frappe.session.user
	todos = frappe.get_all(
		"ToDo",
		filters={"allocated_to": user, "reference_type": "Task", "status": ("!=", "Cancelled")},
		fields=["reference_name", "status"],
	)
	open_assignments = {t.reference_name for t in todos if t.status == "Open"}
	# the JSON quotes make this an exact match, not a substring of another email
	open_assignments |= set(
		frappe.get_all("Task", filters=[["_assign", "like", f'%"{user}"%']], pluck="name")
	)
	return open_assignments, open_assignments | {t.reference_name for t in todos}


def _my_task_rows(tasks: list[dict], open_assignments: set[str]) -> list[dict]:
	tasks = _attach_epics(_attach_blocked_state(_attach_comment_counts(_attach_assignees(tasks))))
	_attach_project_titles(tasks)
	for task in tasks:
		# "done" = you finished your part (or the task closed your assignment)
		task["my_assignment"] = "open" if task.name in open_assignments else "done"
	return tasks


def _attach_project_titles(tasks: list[dict]):
	project_names = {t.get("project") for t in tasks if t.get("project")}
	if not project_names:
		return tasks

	titles = dict(
		frappe.get_all(
			"Project",
			filters={"name": ("in", list(project_names))},
			fields=["name", "project_name"],
			as_list=True,
			ignore_permissions=True,
		)
	)
	for task in tasks:
		task["project_title"] = titles.get(task.get("project")) or task.get("project")
	return tasks


@frappe.whitelist()
def get_task(name: str):
	frappe.has_permission("Task", ptype="read", doc=name, throw=True)
	doc = frappe.get_doc("Task", name)
	data = doc.as_dict()

	data["assignees"] = _attach_assignees([{"name": name, "_assign": doc._assign}])[0]["assignees"]
	data["project_title"] = (
		frappe.db.get_value("Project", doc.project, "project_name") if doc.project else None
	)
	data["comments"] = get_comments("Task", name)
	data["attachments"] = get_attachments("Task", name)
	data["time_logs"] = get_time_logs(name)
	data["subtasks"] = _attach_assignees(
		frappe.get_list(
			"Task",
			filters={"parent_task": name},
			fields=["name", "subject", "status", "priority", "exp_end_date", "_assign"],
			order_by="creation asc",
			limit_page_length=0,
		)
	)
	subtasks = data["subtasks"]
	data["subtask_progress"] = {
		"total": len(subtasks),
		"done": sum(1 for t in subtasks if t["status"] in ("Completed", "Cancelled")),
	}
	data["epic"] = _attach_epics([{"parent_task": doc.parent_task}])[0]["epic"]
	# ERPNext files every child under its parent's `depends_on`; those are
	# contents, not blockers, so they belong in Child issues instead.
	data["depends_on"] = [
		d
		for d in _dependency_details([d.task for d in doc.depends_on])
		if d.get("parent_task") != name
	]
	data["is_blocked"] = any(
		d["status"] not in ("Completed", "Cancelled") for d in data["depends_on"]
	)
	data["tags"] = _parse_tags(doc._user_tags)
	data["history"] = get_task_history(name, limit=20)
	data["blocks"] = [
		b
		for b in frappe.get_all(
			"Task",
			filters={"depends_on_tasks": ("like", f"%{name}%")},
			fields=["name", "subject", "status", "priority"],
			ignore_permissions=True,
		)
		if b.name != doc.parent_task
	]
	data["can_write"] = frappe.has_permission("Task", ptype="write", doc=name)
	data["can_delete"] = frappe.has_permission("Task", ptype="delete", doc=name)
	data["created_by"] = _user_map({doc.owner}).get(doc.owner) or {"name": doc.owner, "full_name": doc.owner}
	data["repeat"] = _repeat_info(doc)

	return data


def _dependency_details(task_names: list[str]) -> list[dict]:
	if not task_names:
		return []
	return frappe.get_all(
		"Task",
		filters={"name": ("in", task_names)},
		fields=["name", "subject", "status", "priority", "parent_task"],
		ignore_permissions=True,
	)


@frappe.whitelist()
def create_task(**kwargs):
	frappe.has_permission("Task", ptype="create", throw=True)

	values = {k: v for k, v in kwargs.items() if k in TASK_WRITABLE_FIELDS and v not in (None, "")}
	if not values.get("subject"):
		frappe.throw(_("Subject is required"))

	# ERPNext's Task.validate_status() calls close_all_assignments() while the
	# document is still unsaved, which blows up on a task created directly in a
	# closed state. Insert it open, then move it - by then the row exists.
	closed_status = None
	if values.get("status") in ("Completed", "Cancelled"):
		closed_status = values.pop("status")
		values["status"] = "Open"

	doc = frappe.new_doc("Task")
	doc.update(values)
	doc.insert()

	if closed_status:
		doc.status = closed_status
		doc.save()

	assignees = kwargs.get("assignees")
	if isinstance(assignees, str):
		assignees = json.loads(assignees)
	if assignees:
		set_assignees(doc.name, assignees)

	repeat = kwargs.get("repeat")
	if isinstance(repeat, str):
		repeat = json.loads(repeat) if repeat.strip() else None
	if repeat:
		set_task_repeat(doc.name, repeat)

	return get_task(doc.name)


@frappe.whitelist()
def update_task(name: str, values):
	"""Single entry point for every inline edit on the board."""
	frappe.has_permission("Task", ptype="write", doc=name, throw=True)

	if isinstance(values, str):
		values = json.loads(values)

	assignees = values.pop("assignees", None)

	unknown = set(values) - TASK_WRITABLE_FIELDS
	if unknown:
		frappe.throw(_("Cannot update field(s) from the board: {0}").format(", ".join(sorted(unknown))))

	if values:
		doc = frappe.get_doc("Task", name)
		doc.update(values)
		_stamp_completion(doc)
		doc.save()

	if assignees is not None:
		set_assignees(name, assignees)

	return get_task(name)


def _stamp_completion(doc):
	"""Fill the "who/when" fields ERPNext leaves blank when a task is completed.

	`closing_date` is the date the desk shows on a completed task; ERPNext
	never sets it itself.
	"""
	if doc.status != "Completed" or doc.get_db_value("status") == "Completed":
		return
	doc.completed_by = doc.completed_by or frappe.session.user
	doc.completed_on = doc.completed_on or today()
	doc.closing_date = doc.closing_date or today()


@frappe.whitelist()
def move_task(name: str, status: str):
	"""Drag-and-drop between board columns."""
	frappe.has_permission("Task", ptype="write", doc=name, throw=True)

	if status in HIDDEN_TASK_STATUSES:
		frappe.throw(_("{0} is not a board column").format(status))

	doc = frappe.get_doc("Task", name)
	if doc.status == status:
		return _move_task_response(name)

	doc.status = status
	_stamp_completion(doc)
	doc.save()

	return _move_task_response(name)


def _move_task_response(name: str) -> dict:
	"""Re-read via get_list so the row has the exact shape the board renders."""
	row = frappe.get_list("Task", filters={"name": name}, fields=_task_list_fields())[0]
	return _attach_epics(_attach_blocked_state(_attach_comment_counts(_attach_assignees([row]))))[0]


@frappe.whitelist()
def delete_task(name: str):
	frappe.has_permission("Task", ptype="delete", doc=name, throw=True)
	frappe.delete_doc("Task", name)
	return True


@frappe.whitelist()
def set_task_dependencies(task: str, depends_on):
	frappe.has_permission("Task", ptype="write", doc=task, throw=True)

	if isinstance(depends_on, str):
		depends_on = json.loads(depends_on)

	doc = frappe.get_doc("Task", task)
	doc.depends_on = []
	for dep in depends_on or []:
		if dep == task:
			continue
		doc.append("depends_on", {"task": dep})
	doc.save()

	return _dependency_details([d.task for d in doc.depends_on])


# ---------------------------------------------------------------------------
# comments & attachments
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_comments(doctype: str, name: str):
	frappe.has_permission(doctype, ptype="read", doc=name, throw=True)

	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"comment_type": "Comment",
		},
		fields=["name", "content", "owner", "comment_email", "comment_by", "creation", "modified"],
		order_by="creation asc",
		ignore_permissions=True,
	)

	users = _user_map({c.owner for c in comments})
	for comment in comments:
		user = users.get(comment.owner) or {}
		comment["full_name"] = user.get("full_name") or comment.comment_by or comment.owner
		comment["user_image"] = user.get("user_image")

	return comments


@frappe.whitelist()
def add_comment(doctype: str, name: str, content: str):
	frappe.has_permission(doctype, ptype="read", doc=name, throw=True)

	if not (content or "").strip():
		frappe.throw(_("Comment cannot be empty"))

	doc = frappe.get_doc(doctype, name)
	comment = doc.add_comment(
		"Comment", content, comment_email=frappe.session.user, comment_by=frappe.utils.get_fullname()
	)

	return {
		"name": comment.name,
		"content": comment.content,
		"owner": comment.owner,
		"creation": comment.creation,
		"full_name": frappe.utils.get_fullname(),
		"user_image": frappe.db.get_value("User", frappe.session.user, "user_image"),
	}


@frappe.whitelist()
def delete_comment(name: str):
	comment = frappe.get_doc("Comment", name)
	if comment.owner != frappe.session.user and "System Manager" not in frappe.get_roles():
		frappe.throw(_("You can only delete your own comments"), frappe.PermissionError)
	comment.delete()
	return True


@frappe.whitelist()
def get_attachments(doctype: str, name: str):
	frappe.has_permission(doctype, ptype="read", doc=name, throw=True)

	return frappe.get_all(
		"File",
		filters={"attached_to_doctype": doctype, "attached_to_name": name},
		fields=["name", "file_name", "file_url", "file_size", "is_private", "owner", "creation"],
		order_by="creation desc",
		ignore_permissions=True,
	)


# ---------------------------------------------------------------------------
# time tracking (native Timesheet)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_time_logs(task: str):
	rows = frappe.get_all(
		"Timesheet Detail",
		filters={"task": task, "docstatus": ("<", 2)},
		fields=[
			"name",
			"parent",
			"activity_type",
			"from_time",
			"to_time",
			"hours",
			"description",
			"is_billable",
			"billing_hours",
			"completed",
			"docstatus",
		],
		order_by="from_time desc",
		ignore_permissions=True,
	)

	owners = dict(
		frappe.get_all(
			"Timesheet",
			filters={"name": ("in", [r.parent for r in rows])} if rows else {"name": ""},
			fields=["name", "employee_name"],
			as_list=True,
			ignore_permissions=True,
		)
	)
	for row in rows:
		row["logged_by"] = owners.get(row.parent)

	return rows


@frappe.whitelist()
def log_time(
	task: str,
	hours: float,
	description: str | None = None,
	from_time: str | None = None,
	activity_type: str | None = None,
	is_billable: int = 0,
	submit: int = 1,
):
	"""Append a Timesheet Detail row against a Task.

	Reuses today's draft Timesheet for the user when one exists so the portal
	does not litter the system with one-row timesheets.
	"""
	frappe.has_permission("Task", ptype="read", doc=task, throw=True)
	frappe.has_permission("Timesheet", ptype="create", throw=True)

	hours = flt(hours)
	if hours <= 0:
		frappe.throw(_("Hours must be greater than zero"))

	project = frappe.db.get_value("Task", task, "project")
	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
	if not employee:
		frappe.throw(_("No Employee record is linked to your user, so time cannot be logged."))

	# Timesheet.validate_mandatory_fields() rejects a submitted row without one.
	if cint(submit) and not activity_type:
		frappe.throw(_("Activity Type is required to submit a timesheet."))

	from_time = get_datetime(from_time) if from_time else now_datetime()

	timesheet = None
	if not cint(submit):
		existing = frappe.db.get_value(
			"Timesheet",
			{"employee": employee, "docstatus": 0, "start_date": getdate(from_time)},
			"name",
		)
		if existing:
			timesheet = frappe.get_doc("Timesheet", existing)

	if not timesheet:
		timesheet = frappe.new_doc("Timesheet")
		timesheet.employee = employee
		timesheet.parent_project = project

	timesheet.append(
		"time_logs",
		{
			"activity_type": activity_type,
			"from_time": from_time,
			"hours": hours,
			"project": project,
			"task": task,
			"description": description,
			"is_billable": cint(is_billable),
		},
	)
	timesheet.save()

	if cint(submit):
		timesheet.submit()

	return {"timesheet": timesheet.name, "docstatus": timesheet.docstatus}


# ---------------------------------------------------------------------------
# analytics
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_project_stats(project: str):
	"""Numbers for the project overview tab, all derived from native fields."""
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)

	doc = frappe.get_cached_doc("Project", project)
	by_status = _task_counts_by_project([project]).get(project, {})

	Task = frappe.qb.DocType("Task")
	by_priority = (
		frappe.qb.from_(Task)
		.select(Task.priority, Count(Task.name).as_("count"))
		.where((Task.project == project) & (Task.is_template == 0))
		.groupby(Task.priority)
	).run(as_dict=True)

	overdue = frappe.db.count(
		"Task",
		{
			"project": project,
			"is_template": 0,
			"status": ("not in", ["Completed", "Cancelled"]),
			"exp_end_date": ("<", now_datetime()),
		},
	)

	unassigned = frappe.db.count(
		"Task",
		{
			"project": project,
			"is_template": 0,
			"status": ("not in", ["Completed", "Cancelled"]),
			"_assign": ("in", ["", "[]", None]),
		},
	)

	rows = frappe.get_all(
		"Task",
		filters={"project": project, "is_template": 0},
		fields=["_assign", "status", "expected_time", "actual_time"],
		ignore_permissions=True,
	)

	workload: dict[str, dict] = {}
	for row in rows:
		for user in _parse_assign(row._assign) or ["__unassigned__"]:
			bucket = workload.setdefault(user, {"total": 0, "open": 0, "done": 0})
			bucket["total"] += 1
			if row.status in ("Completed", "Cancelled"):
				bucket["done"] += 1
			else:
				bucket["open"] += 1

	users = _user_map(set(workload) - {"__unassigned__"})
	workload_list = []
	for user, bucket in sorted(workload.items(), key=lambda kv: -kv[1]["open"]):
		info = users.get(user) or {}
		workload_list.append(
			{
				"user": user,
				"full_name": "Unassigned" if user == "__unassigned__" else (info.get("full_name") or user),
				"user_image": info.get("user_image"),
				**bucket,
			}
		)

	return {
		"by_status": by_status,
		"by_priority": {r.priority or "Unset": r.count for r in by_priority},
		"overdue": overdue,
		"unassigned": unassigned,
		"workload": workload_list,
		"percent_complete": flt(doc.percent_complete),
		"expected_time": sum(flt(r.expected_time) for r in rows),
		"actual_time": flt(doc.actual_time),
		"estimated_costing": flt(doc.estimated_costing),
		"total_costing_amount": flt(doc.total_costing_amount),
		"total_billable_amount": flt(doc.total_billable_amount),
		"total_billed_amount": flt(doc.total_billed_amount),
		"total_sales_amount": flt(doc.total_sales_amount),
		"total_purchase_cost": flt(doc.total_purchase_cost),
		"total_consumed_material_cost": flt(doc.total_consumed_material_cost),
		"gross_margin": flt(doc.gross_margin),
		"per_gross_margin": flt(doc.per_gross_margin),
		"currency": frappe.get_cached_value("Company", doc.company, "default_currency")
		if doc.company
		else None,
		"blocked": frappe.db.count(
			"Task",
			{
				"project": project,
				"is_template": 0,
				"status": ("not in", ["Completed", "Cancelled"]),
				"depends_on_tasks": ("!=", ""),
			},
		),
	}


@frappe.whitelist()
def get_activity(project: str, limit: int = 30):
	"""Recent versions + comments on the project's tasks, newest first."""
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)

	task_names = frappe.get_all("Task", filters={"project": project}, pluck="name")
	if not task_names:
		return []

	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": "Task",
			"reference_name": ("in", task_names),
			"comment_type": ("in", ["Comment", "Created", "Edit", "Assigned", "Assignment Completed"]),
		},
		fields=["name", "content", "comment_type", "owner", "creation", "reference_name"],
		order_by="creation desc",
		limit_page_length=cint(limit),
		ignore_permissions=True,
	)

	subjects = dict(
		frappe.get_all(
			"Task",
			filters={"name": ("in", [c.reference_name for c in comments])} if comments else {"name": ""},
			fields=["name", "subject"],
			as_list=True,
			ignore_permissions=True,
		)
	)
	users = _user_map({c.owner for c in comments})

	for comment in comments:
		comment["task_subject"] = subjects.get(comment.reference_name)
		info = users.get(comment.owner) or {}
		comment["full_name"] = info.get("full_name") or comment.owner
		comment["user_image"] = info.get("user_image")

	return comments


# ---------------------------------------------------------------------------
# blocked-by state
# ---------------------------------------------------------------------------


def _attach_blocked_state(rows: list[dict]) -> list[dict]:
	"""Mark tasks whose dependencies are not finished yet.

	`Task.depends_on_tasks` is the comma-joined mirror ERPNext keeps of the
	`Task Depends On` child table, so one extra query covers the whole board.
	"""
	blockers: set[str] = set()
	for row in rows:
		for name in _parse_csv(row.get("depends_on_tasks")):
			blockers.add(name)

	open_blockers: dict[str, str | None] = {}
	if blockers:
		open_blockers = {
			d.name: d.parent_task
			for d in frappe.get_all(
				"Task",
				filters={"name": ("in", list(blockers)), "status": ("not in", ["Completed", "Cancelled"])},
				fields=["name", "parent_task"],
				ignore_permissions=True,
			)
		}

	for row in rows:
		deps = _parse_csv(row.pop("depends_on_tasks", None))
		# ERPNext's populate_depends_on() files every child under its parent's
		# `depends_on`, so an epic would otherwise look blocked by its own
		# contents. A parent waiting on its children is containment, not a block.
		row["blocked_by"] = [
			d for d in deps if d in open_blockers and open_blockers[d] != row.get("name")
		]
		row["is_blocked"] = bool(row["blocked_by"])

	return rows


def _parse_csv(value) -> list[str]:
	if not value:
		return []
	return [v.strip() for v in str(value).split(",") if v.strip()]


# ---------------------------------------------------------------------------
# labels (native Tag / Tag Link)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_all_tags(txt: str = ""):
	"""Existing Tags, for the label autocomplete."""
	return frappe.get_all(
		"Tag",
		filters=[["name", "like", f"%{txt}%"]] if txt else None,
		pluck="name",
		limit_page_length=50,
		order_by="name",
	)


@frappe.whitelist()
def set_task_tags(task: str, tags):
	"""Sync a Task's labels through Frappe's own tag API."""
	from frappe.desk.doctype.tag.tag import add_tag, remove_tag

	frappe.has_permission("Task", ptype="write", doc=task, throw=True)

	if isinstance(tags, str):
		tags = json.loads(tags)
	wanted = {t.strip() for t in (tags or []) if t and t.strip()}

	current = set(_parse_tags(frappe.db.get_value("Task", task, "_user_tags")))

	for tag in current - wanted:
		remove_tag(tag, "Task", task)
	for tag in wanted - current:
		add_tag(tag, "Task", task)

	return sorted(wanted)


# ---------------------------------------------------------------------------
# project templates (native Project Template)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_project_templates():
	"""Templates a new project can be created from, with their task counts."""
	templates = frappe.get_all(
		"Project Template",
		filters={"disabled": 0},
		fields=["name", "project_type"],
		order_by="name",
	)

	if not templates:
		return []

	counts = {}
	for row in frappe.get_all(
		"Project Template Task",
		filters={"parent": ("in", [t.name for t in templates])},
		fields=["parent", "subject"],
		ignore_permissions=True,
	):
		counts.setdefault(row.parent, []).append(row.subject)

	for template in templates:
		tasks = counts.get(template.name, [])
		template["task_count"] = len(tasks)
		template["sample_tasks"] = tasks[:4]

	return templates


# ---------------------------------------------------------------------------
# project updates (native Project Update)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_project_updates(project: str, limit: int = 20):
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)

	updates = frappe.get_all(
		"Project Update",
		filters={"project": project, "docstatus": ("<", 2)},
		fields=["name", "date", "time", "owner", "creation", "docstatus"],
		order_by="creation desc",
		limit_page_length=cint(limit),
	)
	if not updates:
		return []

	notes = {}
	for row in frappe.get_all(
		"Project User",
		filters={"parent": ("in", [u.name for u in updates]), "parenttype": "Project Update"},
		fields=["parent", "user", "project_status", "idx"],
		order_by="idx asc",
		ignore_permissions=True,
	):
		notes.setdefault(row.parent, []).append(row)

	users = _user_map({u.owner for u in updates} | {n.user for rows in notes.values() for n in rows})
	for update in updates:
		info = users.get(update.owner) or {}
		update["full_name"] = info.get("full_name") or update.owner
		update["user_image"] = info.get("user_image")
		# ERPNext's scheduled check-ins use their own naming series; each email
		# reply is appended to that update as one more row.
		update["is_checkin"] = update.name.startswith("UPDATE-")
		update["notes"] = notes.get(update.name, [])
		for note in update["notes"]:
			author = users.get(note.user) or {}
			note["full_name"] = author.get("full_name") or note.user
			note["user_image"] = author.get("user_image")
		update["status_text"] = "\n\n".join(
			n.project_status for n in update["notes"] if n.project_status
		)

	return updates


@frappe.whitelist()
def add_project_update(project: str, status: str):
	"""Post a status check-in against the project."""
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)
	frappe.has_permission("Project Update", ptype="create", throw=True)

	if not (status or "").strip():
		frappe.throw(_("Write something before posting an update"))

	doc = frappe.new_doc("Project Update")
	doc.project = project
	doc.date = today()
	doc.time = nowtime()
	doc.append(
		"users",
		{"user": frappe.session.user, "project_status": status.strip()},
	)
	doc.insert()

	return get_project_updates(project, limit=1)[0]


def _checkin_readiness(doc) -> dict:
	"""What ERPNext needs before a scheduled check-in can go out and come back."""
	from frappe.utils.scheduler import is_scheduler_disabled

	recipients = [
		{"name": u.user, "full_name": u.full_name or u.user, "email": u.email}
		for u in doc.users
		if u.email and frappe.db.get_value("User", u.user, "enabled")
	]
	return {
		"outgoing": _outgoing_email_configured(),
		# replies are threaded back through the default incoming account
		"incoming": bool(
			frappe.db.get_value("Email Account", {"enable_incoming": 1, "default_incoming": 1})
		),
		"scheduler": not is_scheduler_disabled(verbose=False),
		"recipients": recipients,
	}


@frappe.whitelist()
def get_checkin_settings(project: str):
	"""ERPNext's progress-collection settings for a project, plus a readiness check."""
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)
	doc = frappe.get_doc("Project", project)

	settings = {field: doc.get(field) for field in CHECKIN_FIELDS}
	for field in ("daily_time_to_send", "first_email", "second_email", "weekly_time_to_send"):
		if settings[field]:
			settings[field] = str(settings[field])[:5]  # HH:MM for <input type="time">

	return {
		"settings": settings,
		"frequencies": list(CHECKIN_FREQUENCIES),
		"readiness": _checkin_readiness(doc),
		"holiday_list": doc.holiday_list,
		"can_edit": bool(frappe.has_permission("Project", ptype="write", doc=project)),
	}


@frappe.whitelist()
def save_checkin_settings(project: str, values):
	frappe.has_permission("Project", ptype="write", doc=project, throw=True)
	if isinstance(values, str):
		values = json.loads(values)

	unknown = set(values) - set(CHECKIN_FIELDS)
	if unknown:
		frappe.throw(_("Not a check-in setting: {0}").format(", ".join(sorted(unknown))))

	doc = frappe.get_doc("Project", project)
	doc.update(values)

	if cint(doc.collect_progress):
		if doc.frequency not in CHECKIN_FREQUENCIES:
			frappe.throw(_("Pick how often to send the check-in"))
		required = {
			"Daily": ["daily_time_to_send"],
			"Twice Daily": ["first_email", "second_email"],
			"Weekly": ["day_to_send", "weekly_time_to_send"],
		}[doc.frequency]
		if any(not doc.get(field) for field in required):
			frappe.throw(_("Set when the check-in should go out"))
		if not (doc.subject or "").strip() or not (doc.message or "").strip():
			frappe.throw(_("Write the email subject and message"))

		# Without these, ERPNext would still create an empty update every day.
		readiness = _checkin_readiness(doc)
		if not readiness["outgoing"]:
			frappe.throw(_("Set up an outgoing email account before turning check-ins on"))
		if not readiness["recipients"]:
			frappe.throw(_("Add team members to the project - they are who the check-in goes to"))

	doc.save()
	return get_checkin_settings(project)


@frappe.whitelist()
def send_checkin_now(project: str):
	"""Send the check-in email right away, the same way the scheduler does."""
	from erpnext.projects.doctype.project.project import send_project_update_email_to_users
	from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

	frappe.has_permission("Project", ptype="write", doc=project, throw=True)
	doc = frappe.get_doc("Project", project)

	readiness = _checkin_readiness(doc)
	if not readiness["outgoing"]:
		frappe.throw(_("Set up an outgoing email account first"))
	if not readiness["recipients"]:
		frappe.throw(_("The project has no team members to email"))
	if not (doc.subject or "").strip() or not (doc.message or "").strip():
		frappe.throw(_("Save a subject and message first"))
	if doc.holiday_list and is_holiday(doc.holiday_list):
		frappe.throw(_("Today is a holiday in {0}, so ERPNext will not send it").format(doc.holiday_list))

	send_project_update_email_to_users(project)
	return {"recipients": len(readiness["recipients"])}


# ---------------------------------------------------------------------------
# recurring tasks (Frappe Auto Repeat; see recurring.py)
# ---------------------------------------------------------------------------


def _repeat_info(task) -> dict | None:
	"""The repeat rule a task belongs to, if any.

	The task the series was set up on is its template ("is_template"); every
	occurrence Auto Repeat makes links back to the same record.
	"""
	name = task.get("auto_repeat") if task.meta.has_field("auto_repeat") else None
	if not name:
		# a stopped series unlinks its template; show it as not repeating
		return None

	rule = frappe.db.get_value(
		"Auto Repeat",
		name,
		[
			"name",
			"reference_document",
			"frequency",
			"repeat_on_day",
			"repeat_on_last_day",
			"start_date",
			"end_date",
			"next_schedule_date",
			"status",
			"disabled",
		],
		as_dict=True,
	)
	if not rule:
		return None

	rule["repeat_on_days"] = frappe.get_all(
		"Auto Repeat Day", filters={"parent": name}, pluck="day", order_by="idx asc"
	)
	rule["is_template"] = rule.reference_document == task.name
	rule["template_subject"] = (
		task.subject
		if rule["is_template"]
		else frappe.db.get_value("Task", rule.reference_document, "subject")
	)
	return rule


def _repeat_ready() -> bool:
	"""Auto Repeat allowed on Task *and* the link field it needs exists."""
	meta = frappe.get_meta("Task")
	return bool(meta.allow_auto_repeat and meta.has_field("auto_repeat"))


@frappe.whitelist()
def enable_repeating_tasks():
	"""Switch Auto Repeat on for Task from the app - what `bench migrate` does.

	For a site where migrate has not run yet, or where it could not do it; a
	failure comes back as the real error instead of only an Error Log entry.
	"""
	frappe.only_for("System Manager")
	from project_board.install import enable_task_auto_repeat

	enable_task_auto_repeat()
	frappe.db.commit()  # nosemgrep: schema change; the boot read that follows must see it
	if not _repeat_ready():
		frappe.throw(_("Auto Repeat is still not available for Task"))
	return True


@frappe.whitelist()
def set_task_repeat(task: str, rule):
	"""Make a task repeat, or change how it repeats.

	Only System Managers and Accounts users may create Auto Repeat records, so
	the board creates it on the user's behalf - after checking they can edit the
	task. Occurrences are still made with the series owner's access to it.
	"""
	frappe.has_permission("Task", ptype="write", doc=task, throw=True)
	if not _repeat_ready():
		frappe.throw(_("Repeating tasks are not switched on yet - run `bench migrate`"))
	if isinstance(rule, str):
		rule = json.loads(rule)

	frequency = rule.get("frequency")
	if frequency not in REPEAT_FREQUENCIES:
		frappe.throw(_("Pick how often the task repeats"))
	days = [d for d in rule.get("repeat_on_days") or [] if d in WEEKDAYS] if frequency == "Weekly" else []

	doc = frappe.get_doc("Task", task)
	existing = _repeat_info(doc)
	if existing and not existing["is_template"]:
		frappe.throw(
			_("This task is one occurrence of a repeating series; change the series on {0}").format(
				existing["reference_document"]
			)
		)

	if existing:
		series = frappe.get_doc("Auto Repeat", existing["name"])
	else:
		series = frappe.new_doc("Auto Repeat")
		series.reference_doctype = "Task"
		series.reference_document = task
		# the task itself is the first occurrence; Auto Repeat makes the next
		# one a period after this (and moves a past date up to today)
		series.start_date = doc.exp_start_date or doc.exp_end_date or today()

	series.frequency = frequency
	series.repeat_on_last_day = cint(rule.get("repeat_on_last_day")) if frequency not in ("Daily", "Weekly", "Fortnightly") else 0
	series.end_date = rule.get("end_date") or None
	series.disabled = 0
	series.set("repeat_on_days", [{"day": d} for d in days])
	series.flags.ignore_permissions = True
	if existing:
		series.save(ignore_permissions=True)
	else:
		series.insert(ignore_permissions=True)

	return _repeat_info(frappe.get_doc("Task", task))


@frappe.whitelist()
def stop_task_repeat(task: str):
	"""Stop a series. Occurrences already made stay; no new ones are created."""
	frappe.has_permission("Task", ptype="write", doc=task, throw=True)
	info = _repeat_info(frappe.get_doc("Task", task))
	if not info:
		return None

	series = frappe.get_doc("Auto Repeat", info["name"])
	series.disabled = 1
	series.save(ignore_permissions=True)
	return None


# ---------------------------------------------------------------------------
# reviews (Task.review_date, Pending Review)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_review_queue():
	"""Tasks in review that are waiting on the current user.

	ERPNext has no reviewer field. The person who handed the work out - the
	`assigned_by` on its assignment, or the task's creator - is the one who
	signs it off, so those are the reviews that land here. Your own work in
	review is not your review to do.
	"""
	user = frappe.session.user
	assigned_by_me = set(
		frappe.get_all(
			"ToDo",
			filters={"assigned_by": user, "reference_type": "Task", "status": ("!=", "Cancelled")},
			pluck="reference_name",
		)
	)
	candidates = frappe.get_list(
		"Task",
		filters=[["status", "=", "Pending Review"], ["is_template", "=", 0]],
		or_filters=[["name", "in", list(assigned_by_me) or [""]], ["owner", "=", user]],
		fields=_task_list_fields(),
		order_by="review_date asc, exp_end_date asc",
		limit_page_length=0,
	)
	rows = [
		t
		for t in _attach_assignees(candidates)
		if user not in {a["name"] for a in t.get("assignees") or []}
	]
	rows = _attach_epics(_attach_comment_counts(rows))
	_attach_project_titles(rows)
	return rows


# ---------------------------------------------------------------------------
# live updates
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_task_rows(names):
	"""Fresh board rows for tasks a realtime event says have changed.

	Names that come back missing were deleted, or are no longer visible to the
	user, and should drop off the board.
	"""
	if isinstance(names, str):
		names = json.loads(names)
	names = [n for n in (names or [])[:200] if n]
	if not names:
		return []

	rows = frappe.get_list("Task", filters={"name": ("in", names)}, fields=_task_list_fields())
	return _attach_epics(_attach_blocked_state(_attach_comment_counts(_attach_assignees(rows))))


# ---------------------------------------------------------------------------
# notifications (native Notification Log)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_notifications(limit: int = 30, start: int = 0):
	"""The current user's inbox, newest first, with enough context to route a click."""
	user = frappe.session.user
	logs = frappe.get_all(
		"Notification Log",
		filters={"for_user": user},
		fields=[
			"name",
			"subject",
			"type",
			"document_type",
			"document_name",
			"from_user",
			"email_content",
			"read",
			"creation",
		],
		order_by="creation desc",
		limit_start=cint(start),
		limit_page_length=min(cint(limit) or 30, 100),
	)

	senders = _user_map({log.from_user for log in logs})
	task_projects = dict(
		frappe.get_all(
			"Task",
			filters={"name": ("in", [log.document_name for log in logs if log.document_type == "Task"] or [""])},
			fields=["name", "project"],
			as_list=True,
		)
	)
	for log in logs:
		info = senders.get(log.from_user) or {}
		log["from_full_name"] = info.get("full_name") or log.from_user
		log["from_user_image"] = info.get("user_image")
		if log.document_type == "Task":
			log["project"] = task_projects.get(log.document_name)

	unread = frappe.db.count("Notification Log", {"for_user": user, "read": 0})
	return {"items": logs, "unread": unread}


@frappe.whitelist()
def mark_notifications_read(names=None):
	"""Mark some (or, with no names, all) of the current user's notifications read."""
	if isinstance(names, str):
		names = json.loads(names)

	filters = {"for_user": frappe.session.user, "read": 0}
	if names:
		filters["name"] = ("in", names)
	frappe.db.set_value("Notification Log", filters, "read", 1, update_modified=False)
	return frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})


# ---------------------------------------------------------------------------
# attachments
# ---------------------------------------------------------------------------


@frappe.whitelist()
def delete_attachment(name: str):
	"""Remove a File attached to a Task the user can write to."""
	file = frappe.db.get_value(
		"File", name, ["attached_to_doctype", "attached_to_name", "owner"], as_dict=True
	)
	if not file:
		frappe.throw(_("Attachment not found"))

	if file.attached_to_doctype and file.attached_to_name:
		frappe.has_permission(
			file.attached_to_doctype, ptype="write", doc=file.attached_to_name, throw=True
		)
	elif file.owner != frappe.session.user:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	frappe.delete_doc("File", name)
	return True


# ---------------------------------------------------------------------------
# dependencies
# ---------------------------------------------------------------------------


@frappe.whitelist()
def search_tasks(project: str | None = None, txt: str = "", exclude=None, limit: int = 20):
	"""Task picker for the 'blocked by' and parent-task fields."""
	filters = [["is_template", "=", 0]]
	if project:
		filters.append(["project", "=", project])

	if isinstance(exclude, str):
		exclude = json.loads(exclude) if exclude.startswith("[") else [exclude]
	if exclude:
		filters.append(["name", "not in", exclude])

	return frappe.get_list(
		"Task",
		filters=filters,
		or_filters=[["subject", "like", f"%{txt}%"], ["name", "like", f"%{txt}%"]] if txt else None,
		fields=["name", "subject", "status", "priority"],
		limit_page_length=cint(limit),
		order_by="modified desc",
	)


# ---------------------------------------------------------------------------
# bulk actions
# ---------------------------------------------------------------------------


@frappe.whitelist()
def bulk_update_tasks(names, values):
	"""Apply the same change to several tasks, reporting per-task failures."""
	if isinstance(names, str):
		names = json.loads(names)
	if isinstance(values, str):
		values = json.loads(values)

	assignees = values.pop("assignees", None)
	unknown = set(values) - TASK_WRITABLE_FIELDS
	if unknown:
		frappe.throw(_("Cannot update field(s) from the board: {0}").format(", ".join(sorted(unknown))))

	updated, failed = [], []
	for name in names or []:
		try:
			if not frappe.has_permission("Task", ptype="write", doc=name):
				raise frappe.PermissionError(_("No write access"))
			if values:
				doc = frappe.get_doc("Task", name)
				doc.update(values)
				_stamp_completion(doc)
				doc.save()
			if assignees is not None:
				set_assignees(name, assignees)
			updated.append(name)
		except Exception as e:
			# one bad task must not sink the whole batch
			frappe.db.rollback()
			failed.append({"task": name, "error": str(e)})

	rows = (
		_attach_blocked_state(
			_attach_comment_counts(
				_attach_assignees(
					frappe.get_list("Task", filters={"name": ("in", updated)}, fields=_task_list_fields())
				)
			)
		)
		if updated
		else []
	)

	return {"updated": rows, "failed": failed}


@frappe.whitelist()
def bulk_delete_tasks(names):
	if isinstance(names, str):
		names = json.loads(names)

	deleted, failed = [], []
	for name in names or []:
		try:
			frappe.has_permission("Task", ptype="delete", doc=name, throw=True)
			frappe.delete_doc("Task", name)
			deleted.append(name)
		except Exception as e:
			frappe.db.rollback()
			failed.append({"task": name, "error": str(e)})

	return {"deleted": deleted, "failed": failed}


# ---------------------------------------------------------------------------
# saved views (native List Filter)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_saved_views():
	"""Per-user saved filters, stored in Frappe's own List Filter doctype."""
	return [
		{"name": v.name, "label": v.filter_name, "filters": frappe.parse_json(v.filters or "{}")}
		for v in frappe.get_all(
			"List Filter",
			filters={"reference_doctype": "Task", "for_user": frappe.session.user},
			fields=["name", "filter_name", "filters"],
			order_by="filter_name",
		)
	]


@frappe.whitelist()
def save_view(label: str, filters):
	if not (label or "").strip():
		frappe.throw(_("Name this view before saving it"))

	if not isinstance(filters, str):
		filters = frappe.as_json(filters)

	existing = frappe.db.get_value(
		"List Filter",
		{"reference_doctype": "Task", "for_user": frappe.session.user, "filter_name": label.strip()},
		"name",
	)
	if existing:
		doc = frappe.get_doc("List Filter", existing)
		doc.filters = filters
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "List Filter",
				"reference_doctype": "Task",
				"for_user": frappe.session.user,
				"filter_name": label.strip(),
				"filters": filters,
			}
		).insert(ignore_permissions=True)

	return {"name": doc.name, "label": doc.filter_name, "filters": frappe.parse_json(doc.filters)}


@frappe.whitelist()
def delete_saved_view(name: str):
	doc = frappe.get_doc("List Filter", name)
	if doc.for_user != frappe.session.user:
		frappe.throw(_("You can only delete your own views"), frappe.PermissionError)
	doc.delete(ignore_permissions=True)
	return True


# ---------------------------------------------------------------------------
# audit trail (native Version)
# ---------------------------------------------------------------------------

TRACKED_LABELS = {
	"status": "status",
	"priority": "priority",
	"subject": "subject",
	"exp_end_date": "due date",
	"exp_start_date": "start date",
	"task_weight": "weight",
	"progress": "progress",
	"type": "type",
	"parent_task": "parent",
}


@frappe.whitelist()
def get_task_history(task: str, limit: int = 30):
	"""Field-level change log, read from the Version records Frappe already writes."""
	frappe.has_permission("Task", ptype="read", doc=task, throw=True)

	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": "Task", "docname": task},
		fields=["name", "owner", "creation", "data"],
		order_by="creation desc",
		limit_page_length=cint(limit),
		ignore_permissions=True,
	)

	users = _user_map({v.owner for v in versions})
	entries = []
	for version in versions:
		data = frappe.parse_json(version.data or "{}")
		changes = []
		for change in data.get("changed") or []:
			fieldname, old, new = (change + [None, None, None])[:3]
			if fieldname not in TRACKED_LABELS:
				continue
			changes.append({"field": TRACKED_LABELS[fieldname], "from": old, "to": new})

		if not changes:
			continue

		info = users.get(version.owner) or {}
		entries.append(
			{
				"name": version.name,
				"owner": version.owner,
				"full_name": info.get("full_name") or version.owner,
				"user_image": info.get("user_image"),
				"creation": version.creation,
				"changes": changes,
			}
		)

	return entries


# ---------------------------------------------------------------------------
# epics (native is_group / parent_task)
# ---------------------------------------------------------------------------


def _attach_epics(rows: list[dict]) -> list[dict]:
	"""Resolve each task's parent into a usable epic chip.

	`parent_task` is only an id, so the board would otherwise render
	"TASK-2026-00008" where a name belongs.
	"""
	parents = {r.get("parent_task") for r in rows if r.get("parent_task")}
	lookup = {}
	if parents:
		lookup = {
			d.name: d
			for d in frappe.get_all(
				"Task",
				filters={"name": ("in", list(parents))},
				fields=["name", "subject", "color"],
				ignore_permissions=True,
			)
		}

	for row in rows:
		parent = lookup.get(row.get("parent_task"))
		row["epic"] = (
			{"name": parent.name, "subject": parent.subject, "color": parent.color}
			if parent
			else None
		)

	return rows


@frappe.whitelist()
def get_project_epics(project: str):
	"""Group tasks with their child rollups, for the board's epic rail."""
	frappe.has_permission("Project", ptype="read", doc=project, throw=True)

	epics = frappe.get_list(
		"Task",
		filters={"project": project, "is_group": 1, "is_template": 0},
		fields=["name", "subject", "color", "status", "priority", "exp_end_date", "progress"],
		order_by="creation asc",
		limit_page_length=0,
	)
	if not epics:
		return []

	Task = frappe.qb.DocType("Task")
	rows = (
		frappe.qb.from_(Task)
		.select(Task.parent_task, Task.status, Count(Task.name).as_("count"))
		.where(Task.parent_task.isin([e.name for e in epics]))
		.groupby(Task.parent_task, Task.status)
	).run(as_dict=True)

	counts: dict[str, dict[str, int]] = {}
	for row in rows:
		counts.setdefault(row.parent_task, {})[row.status] = row.count

	for epic in epics:
		by_status = counts.get(epic.name, {})
		total = sum(by_status.values())
		done = by_status.get("Completed", 0) + by_status.get("Cancelled", 0)
		epic["total"] = total
		epic["done"] = done
		epic["open"] = total - done
		epic["percent"] = round((done / total) * 100) if total else 0

	return epics
