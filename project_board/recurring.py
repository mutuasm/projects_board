"""Recurring tasks, on top of Frappe's Auto Repeat.

A repeating series is an ordinary Auto Repeat record whose reference document
is the task you created: that task is the first occurrence and the template
for the rest. Each day the scheduler copies it for any series that is due.

Auto Repeat copies a document as-is, which suits invoices but not tasks, so
`on_recurring` turns each copy into a fresh occurrence: its dates move to the
day it is created, and the state of the original (done, in review, who it was
blocked by) is left behind.
"""

import frappe
from frappe.desk.form.assign_to import add as assign_to_add
from frappe.utils import add_days, date_diff, getdate, today

from project_board.api import _parse_assign


def on_recurring(doc, method=None, reference_doc=None, auto_repeat_doc=None):
	"""Called by Auto Repeat on the unsaved copy, just before it is inserted."""
	occurrence = getdate(auto_repeat_doc.next_schedule_date if auto_repeat_doc else today())

	# Keep the original's length: a two-day task stays two days long.
	anchor = reference_doc.exp_start_date or reference_doc.exp_end_date
	if anchor:
		shift = date_diff(occurrence, anchor)
		for field in ("exp_start_date", "exp_end_date"):
			if reference_doc.get(field):
				doc.set(field, add_days(reference_doc.get(field), shift))

	doc.status = "Open"
	doc.progress = 0
	for field in ("completed_on", "completed_by", "closing_date", "review_date"):
		doc.set(field, None)

	# The original's blockers are its own; a new occurrence starts unblocked.
	doc.set("depends_on", [])
	doc.depends_on_tasks = ""

	# The copy carries the original's `_assign` list without the ToDos behind
	# it. Assign the people properly once it exists, from the original's
	# *current* assignees, so changing who is on the series carries forward.
	doc.flags.pb_recurring_assignees = _parse_assign(reference_doc.get("_assign"))
	# whoever set the series up hands out each occurrence - and so reviews it
	doc.flags.pb_recurring_assigner = auto_repeat_doc.owner if auto_repeat_doc else None
	for field in ("_assign", "_comments", "_liked_by", "_seen"):
		doc.set(field, None)


def assign_recurring_copy(doc, method=None):
	"""After insert: assign a freshly made occurrence to the series' people.

	Auto Repeat runs in the scheduler as Administrator, so the permission check
	inside assign_to.add passes; the assignee still gets the usual notification.
	"""
	for user in doc.flags.get("pb_recurring_assignees") or []:
		try:
			assign_to_add(
				{
					"assign_to": [user],
					"doctype": "Task",
					"name": doc.name,
					"description": doc.subject,
					"assigned_by": doc.flags.get("pb_recurring_assigner") or frappe.session.user,
				}
			)
		except Exception:
			# a disabled user, say - the rest still get theirs
			frappe.log_error(title=f"Could not assign recurring task {doc.name} to {user}")
