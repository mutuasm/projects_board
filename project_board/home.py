"""Endpoints behind the Home page: today's brief, team workload and milestones.

Like the rest of the app this only reads native records - Task, ToDo, Comment,
Project - through `frappe.get_list`, so every list is limited to what the
user is allowed to see.
"""

import frappe
from frappe.utils import (
	add_days,
	add_months,
	add_to_date,
	cint,
	get_first_day,
	get_last_day,
	getdate,
	now_datetime,
	today,
)

from project_board.api import (
	_attach_assignees,
	_attach_blocked_state,
	_attach_project_titles,
	_my_task_names,
	_task_list_fields,
	_user_map,
	get_review_queue,
)

CLOSED_TASK = ["Completed", "Cancelled", "Template"]

# The order the brief lists things in: what is already late first, good news last.
BRIEF_ORDER = ["overdue", "due_today", "review", "assigned", "comment", "blocked", "unassigned", "done"]

# How far back "new" assignments and comments reach.
RECENT_HOURS = 48

PERIODS = {
	"this_week": "This week",
	"last_7_days": "Last 7 days",
	"this_month": "This month",
	"last_month": "Last month",
	"last_90_days": "Last 90 days",
}


def _open_projects(project: str | None = None) -> list[str]:
	"""Projects the brief looks at: one, or every open one the user can see."""
	if project:
		frappe.has_permission("Project", ptype="read", doc=project, throw=True)
		return [project]
	return frappe.get_list("Project", filters={"status": "Open"}, pluck="name", limit_page_length=0)


def _open_tasks(projects: list[str], names: set[str] | None = None) -> list[dict]:
	if not projects:
		return []
	filters = [
		["project", "in", projects],
		["status", "not in", CLOSED_TASK],
		["is_template", "=", 0],
	]
	if names is not None:
		if not names:
			return []
		filters.append(["name", "in", list(names)])
	rows = frappe.get_list(
		"Task",
		filters=filters,
		fields=_task_list_fields(),
		order_by="exp_end_date asc, modified desc",
		limit_page_length=2000,
	)
	return _attach_blocked_state(_attach_assignees(rows))


def _item(kind: str, task: dict, when=None, actor: str | None = None, detail: str | None = None) -> dict:
	return {
		"kind": kind,
		"task": task.get("name"),
		"subject": task.get("subject"),
		"project": task.get("project"),
		"project_title": task.get("project_title"),
		"status": task.get("status"),
		"priority": task.get("priority"),
		"is_milestone": task.get("is_milestone"),
		"exp_end_date": task.get("exp_end_date"),
		"assignees": task.get("assignees") or [],
		"when": when,
		"actor": actor,
		"detail": detail,
	}


def _due_items(tasks: list[dict]) -> list[dict]:
	items = []
	now = getdate(today())
	for task in tasks:
		end = task.get("exp_end_date")
		if not end:
			continue
		end = getdate(end)
		# In review with a review date still ahead: ERPNext holds it back from
		# Overdue until then, so the brief does too.
		if task.status == "Pending Review" and task.get("review_date") and getdate(task.review_date) >= now:
			continue
		if end < now:
			items.append(_item("overdue", task, when=end))
		elif end == now:
			items.append(_item("due_today", task, when=end))
	return items


def _recent_comments(task_names: list[str], exclude_user: str | None) -> list[dict]:
	if not task_names:
		return []
	filters = {
		"reference_doctype": "Task",
		"reference_name": ("in", task_names),
		"comment_type": "Comment",
		"creation": (">=", add_to_date(now_datetime(), hours=-RECENT_HOURS)),
	}
	if exclude_user:
		filters["owner"] = ("!=", exclude_user)
	return frappe.get_all(
		"Comment",
		filters=filters,
		fields=["reference_name", "content", "owner", "creation"],
		order_by="creation desc",
		limit_page_length=50,
	)


def _brief_for_me(projects: list[str]) -> list[dict]:
	user = frappe.session.user
	open_assignments, _all = _my_task_names()
	mine = _open_tasks(projects, open_assignments)
	by_name = {t.name: t for t in mine}
	items = _due_items(mine)

	# reviews wait on you whether or not you are on the task
	for task in get_review_queue():
		if task.get("project") in projects:
			items.append(_item("review", task, when=task.get("review_date") or task.get("modified")))

	since = add_to_date(now_datetime(), hours=-RECENT_HOURS)
	for todo in frappe.get_all(
		"ToDo",
		filters={
			"allocated_to": user,
			"reference_type": "Task",
			"status": "Open",
			"assigned_by": ("!=", user),
			"creation": (">=", since),
		},
		fields=["reference_name", "assigned_by", "creation"],
		order_by="creation desc",
	):
		if task := by_name.get(todo.reference_name):
			items.append(_item("assigned", task, when=todo.creation, actor=todo.assigned_by))

	# a comment on a task you are on, or a task you created, by someone else
	created = {
		t.name: t
		for t in _open_tasks(projects, set(frappe.get_list("Task", filters={"owner": user}, pluck="name")))
	}
	watched = {**created, **by_name}
	seen = set()
	for comment in _recent_comments(list(watched), exclude_user=user):
		if comment.reference_name in seen:
			continue  # one line per task: its latest comment
		seen.add(comment.reference_name)
		items.append(
			_item(
				"comment",
				watched[comment.reference_name],
				when=comment.creation,
				actor=comment.owner,
				detail=frappe.utils.strip_html(comment.content or "")[:160],
			)
		)

	for task in mine:
		if task.get("is_blocked"):
			items.append(_item("blocked", task, when=task.get("modified")))
	return items


def _brief_for_team(projects: list[str]) -> list[dict]:
	tasks = _open_tasks(projects)
	items = _due_items(tasks)
	week_ahead = getdate(add_days(today(), 7))

	for task in tasks:
		if task.status == "Pending Review":
			items.append(_item("review", task, when=task.get("review_date") or task.get("modified")))
		if task.get("is_blocked"):
			items.append(_item("blocked", task, when=task.get("modified")))
		# nobody on it, and it is due within the week (or already late)
		if (
			not task.get("assignees")
			and not task.get("is_group")
			and task.get("exp_end_date")
			and getdate(task.exp_end_date) <= week_ahead
		):
			items.append(_item("unassigned", task, when=task.exp_end_date))

	done_today = frappe.get_list(
		"Task",
		filters=[
			["project", "in", projects],
			["status", "=", "Completed"],
			["completed_on", "=", today()],
		],
		fields=_task_list_fields(),
		order_by="modified desc",
		limit_page_length=50,
	)
	for task in _attach_assignees(done_today):
		items.append(_item("done", task, when=task.get("modified"), actor=task.get("completed_by")))
	return items


@frappe.whitelist()
def get_brief(scope: str = "me", project: str | None = None):
	"""Today's brief: what needs attention, for you or for the whole team."""
	projects = _open_projects(project)
	if not projects:
		return {"items": [], "needs_you": 0}

	items = _brief_for_team(projects) if scope == "team" else _brief_for_me(projects)
	_attach_project_titles(items)

	actors = _user_map({i["actor"] for i in items if i.get("actor")})
	for item in items:
		if item.get("actor"):
			item["actor"] = actors.get(item["actor"]) or {"name": item["actor"], "full_name": item["actor"]}

	rank = {kind: i for i, kind in enumerate(BRIEF_ORDER)}
	items.sort(key=lambda i: (rank.get(i["kind"], 99), str(i.get("when") or "")))

	# the greeting always speaks to you, whichever brief is showing
	mine = items if scope != "team" else _brief_for_me(projects)
	needs_you = len({i["task"] for i in mine if i["kind"] in ("overdue", "due_today", "review")})
	return {"items": items[:200], "total": len(items), "needs_you": needs_you}


def _period_range(period: str):
	now = getdate(today())
	if period == "this_week":
		start = add_days(now, -now.weekday())
		return start, now
	if period == "last_7_days":
		return add_days(now, -6), now
	if period == "this_month":
		return get_first_day(now), now
	if period == "last_90_days":
		return add_days(now, -89), now
	last_month = add_months(now, -1)
	return get_first_day(last_month), get_last_day(last_month)


@frappe.whitelist()
def get_team_workload(period: str = "last_month", project: str | None = None):
	"""Per person: open work right now, and tasks they finished in the period."""
	if period not in PERIODS:
		period = "last_month"
	projects = _open_projects(project)
	start, end = _period_range(period)
	now = getdate(today())
	week_end = add_days(now, 6 - now.weekday())

	open_tasks = {
		t.name: t
		for t in frappe.get_list(
			"Task",
			filters=[["project", "in", projects or [""]], ["status", "not in", CLOSED_TASK], ["is_template", "=", 0]],
			fields=["name", "status", "exp_end_date", "is_group"],
			limit_page_length=0,
		)
	}
	done_tasks = set(
		frappe.get_list(
			"Task",
			filters=[
				["project", "in", projects or [""]],
				["status", "=", "Completed"],
				["completed_on", "between", [start, end]],
			],
			pluck="name",
			limit_page_length=0,
		)
	)

	stats: dict[str, dict] = {}

	def row(user):
		return stats.setdefault(
			user, {"open": 0, "overdue": 0, "due_this_week": 0, "in_review": 0, "done": 0}
		)

	if open_tasks:
		for todo in frappe.get_all(
			"ToDo",
			filters={"reference_type": "Task", "reference_name": ("in", list(open_tasks)), "status": "Open"},
			fields=["allocated_to", "reference_name"],
		):
			task = open_tasks[todo.reference_name]
			if task.is_group:
				continue  # an epic is a container, not work on someone's plate
			r = row(todo.allocated_to)
			r["open"] += 1
			if task.status == "Pending Review":
				r["in_review"] += 1
			if task.exp_end_date:
				end_date = getdate(task.exp_end_date)
				if end_date < now:
					r["overdue"] += 1
				elif end_date <= week_end:
					r["due_this_week"] += 1

	if done_tasks:
		# closing a task closes its assignments, so the closed ToDos say who did it
		credited = set()
		for todo in frappe.get_all(
			"ToDo",
			filters={"reference_type": "Task", "reference_name": ("in", list(done_tasks)), "status": "Closed"},
			fields=["allocated_to", "reference_name"],
		):
			key = (todo.allocated_to, todo.reference_name)
			if key not in credited:
				credited.add(key)
				row(todo.allocated_to)["done"] += 1

	users = _user_map(set(stats))
	members = []
	for name, values in stats.items():
		user = users.get(name)
		if not user:
			continue  # a deleted or disabled account
		members.append({"user": user, **values})
	members.sort(key=lambda m: (-m["open"], -m["done"], m["user"].get("full_name") or ""))

	return {
		"period": period,
		"periods": [{"value": k, "label": v} for k, v in PERIODS.items()],
		"start": start,
		"end": end,
		"members": members,
	}


@frappe.whitelist()
def get_milestones(project: str | None = None, days: int = 30):
	"""Open milestones due in the coming days, plus any that slipped past."""
	projects = _open_projects(project)
	if not projects:
		return []
	horizon = add_days(today(), min(cint(days) or 30, 180))
	rows = frappe.get_list(
		"Task",
		filters=[
			["project", "in", projects],
			["is_milestone", "=", 1],
			["status", "not in", CLOSED_TASK],
			["exp_end_date", "is", "set"],
			["exp_end_date", "<=", horizon],
		],
		fields=_task_list_fields(),
		order_by="exp_end_date asc",
		limit_page_length=50,
	)
	rows = _attach_assignees(rows)
	_attach_project_titles(rows)
	return rows
