"""Wiring the portal into the desk.

The app deliberately does NOT add its own tile to the apps screen. Instead the
existing ERPNext "Projects" workspace is repointed at /project-board, so there
is a single Projects entry point rather than two competing ones.

Workspace records ship with ERPNext (standard = 1) and are re-synced from their
JSON on every `bench migrate`, so this runs on install *and* after migrate.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

WORKSPACE = "Projects"
PORTAL_ROUTE = "/project-board"


def after_install():
	link_projects_workspace()
	enable_task_change_tracking()
	_enable_recurring_tasks()


def after_migrate():
	link_projects_workspace()
	enable_task_change_tracking()
	_enable_recurring_tasks()


def _enable_recurring_tasks():
	"""Recurring tasks are an extra: if switching them on fails, say so in the
	Error Log rather than abort the whole install or migrate."""
	# A savepoint, not a full rollback: the workspace link and change tracking
	# set just before this are in the same transaction and must survive.
	frappe.db.savepoint("pb_recurring")
	try:
		enable_task_auto_repeat()
	except Exception:
		frappe.db.rollback(save_point="pb_recurring")
		frappe.log_error(title="Project Board: could not switch on Auto Repeat for Task")
		print("Project Board: could not switch on recurring tasks - see the Error Log")


def link_projects_workspace():
	"""Point the Projects workspace at the portal. Safe to run repeatedly."""
	if not frappe.db.exists("Workspace", WORKSPACE):
		return

	current = frappe.db.get_value(
		"Workspace", WORKSPACE, ["type", "external_link"], as_dict=True
	)
	if current and current.type == "URL" and current.external_link == PORTAL_ROUTE:
		return

	frappe.db.set_value(
		"Workspace",
		WORKSPACE,
		{"type": "URL", "external_link": PORTAL_ROUTE},
		update_modified=False,
	)
	frappe.clear_cache()


def enable_task_change_tracking():
	"""Turn on Frappe's built-in audit trail for Task.

	Task ships with `track_changes` off, so no Version records are written and
	the portal's task history would always be empty. This is the same switch as
	Customize Form > Track Changes, set through a Property Setter so it survives
	migrate and is undone cleanly on uninstall.
	"""
	if frappe.db.get_value("DocType", "Task", "track_changes"):
		return

	make_property_setter(
		"Task",
		None,
		"track_changes",
		1,
		"Check",
		validate_fields_for_doctype=False,
		for_doctype=True,
	)


def enable_task_auto_repeat():
	"""Let Tasks repeat with Frappe's Auto Repeat. Safe to run repeatedly.

	This is the desk's Customize Form > "Allow Auto Repeat" switch, plus the
	read-only `auto_repeat` link field that switch adds - the board's recurring
	tasks are ordinary Auto Repeat records.
	"""
	meta = frappe.get_meta("Task")
	if not meta.allow_auto_repeat:
		make_property_setter(
			"Task",
			None,
			"allow_auto_repeat",
			1,
			"Check",
			validate_fields_for_doctype=False,
			for_doctype=True,
		)

	if not meta.has_field("auto_repeat"):
		create_custom_field(
			"Task",
			{
				"fieldname": "auto_repeat",
				"label": "Auto Repeat",
				"fieldtype": "Link",
				"options": "Auto Repeat",
				"insert_after": meta.fields[-1].fieldname,
				"read_only": 1,
				"no_copy": 1,
				"print_hide": 1,
			},
			# Adding a field re-validates every field on Task. A site where an
			# uninstalled app left custom fields linking to doctypes that no
			# longer exist would then refuse ours; this field is valid on its own.
			ignore_validate=True,
		)

	frappe.clear_cache(doctype="Task")


def before_uninstall():
	"""Hand the Projects workspace back to the desk."""
	if not frappe.db.exists("Workspace", WORKSPACE):
		return

	frappe.db.set_value(
		"Workspace",
		WORKSPACE,
		{"type": "Workspace", "external_link": None},
		update_modified=False,
	)

	# Auto Repeat stays on: switching it off would break every repeating task
	# series already set up, and those belong to ERPNext, not to the board.
	for name in frappe.get_all(
		"Property Setter",
		filters={"doc_type": "Task", "property": "track_changes"},
		pluck="name",
	):
		frappe.delete_doc("Property Setter", name, ignore_permissions=True)

	frappe.clear_cache()
