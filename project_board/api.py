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
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, today

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
	"department",
	"_assign",
	"modified",
	"creation",
	"owner",
	"idx",
]

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

	return rows


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
		fields=TASK_LIST_FIELDS,
		order_by=order_by,
		limit_page_length=cint(limit) or 0,
	)

	return _attach_comment_counts(_attach_assignees(tasks))


@frappe.whitelist()
def get_my_tasks(include_completed: int = 0):
	"""Tasks assigned to the logged-in user, across every project they can see."""
	tasks = frappe.get_list(
		"Task",
		filters=[
			["is_template", "=", 0],
			["_assign", "like", f"%{frappe.session.user}%"],
		]
		+ ([] if cint(include_completed) else [["status", "not in", ["Completed", "Cancelled"]]]),
		fields=TASK_LIST_FIELDS,
		order_by="exp_end_date asc, priority desc, modified desc",
		limit_page_length=0,
	)

	tasks = _attach_comment_counts(_attach_assignees(tasks))
	_attach_project_titles(tasks)
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
	data["depends_on"] = _dependency_details([d.task for d in doc.depends_on])
	data["can_write"] = frappe.has_permission("Task", ptype="write", doc=name)
	data["can_delete"] = frappe.has_permission("Task", ptype="delete", doc=name)

	return data


def _dependency_details(task_names: list[str]) -> list[dict]:
	if not task_names:
		return []
	return frappe.get_all(
		"Task",
		filters={"name": ("in", task_names)},
		fields=["name", "subject", "status", "priority"],
		ignore_permissions=True,
	)


@frappe.whitelist()
def create_task(**kwargs):
	frappe.has_permission("Task", ptype="create", throw=True)

	values = {k: v for k, v in kwargs.items() if k in TASK_WRITABLE_FIELDS and v not in (None, "")}
	if not values.get("subject"):
		frappe.throw(_("Subject is required"))

	doc = frappe.new_doc("Task")
	doc.update(values)
	doc.insert()

	assignees = kwargs.get("assignees")
	if isinstance(assignees, str):
		assignees = json.loads(assignees)
	if assignees:
		set_assignees(doc.name, assignees)

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
		doc.save()

	if assignees is not None:
		set_assignees(name, assignees)

	return get_task(name)


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
	if status == "Completed":
		doc.completed_by = doc.completed_by or frappe.session.user
		doc.completed_on = doc.completed_on or today()
	doc.save()

	return _move_task_response(name)


def _move_task_response(name: str) -> dict:
	"""Re-read via get_list so the row has the exact shape the board renders."""
	row = frappe.get_list("Task", filters={"name": name}, fields=TASK_LIST_FIELDS)[0]
	return _attach_comment_counts(_attach_assignees([row]))[0]


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
