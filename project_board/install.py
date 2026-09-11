"""Wiring the portal into the desk.

The app deliberately does NOT add its own tile to the apps screen. Instead the
existing ERPNext "Projects" workspace is repointed at /project-board, so there
is a single Projects entry point rather than two competing ones.

Workspace records ship with ERPNext (standard = 1) and are re-synced from their
JSON on every `bench migrate`, so this runs on install *and* after migrate.
"""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

WORKSPACE = "Projects"
PORTAL_ROUTE = "/project-board"


def after_install():
	link_projects_workspace()
	enable_task_change_tracking()


def after_migrate():
	link_projects_workspace()
	enable_task_change_tracking()


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

	for name in frappe.get_all(
		"Property Setter",
		filters={"doc_type": "Task", "property": "track_changes"},
		pluck="name",
	):
		frappe.delete_doc("Property Setter", name, ignore_permissions=True)

	frappe.clear_cache()
