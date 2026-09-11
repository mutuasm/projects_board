import json

import frappe
from frappe.boot import load_translations

no_cache = 1


def get_context(context):
	context = frappe._dict()
	context.boot = get_boot()
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	"""`vite dev` has no Jinja pass, so the SPA pulls the same payload over HTTP."""
	if not frappe.conf.developer_mode:
		frappe.throw(frappe._("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	boot = frappe._dict(
		{
			"site_name": str(frappe.local.site),
			"csrf_token": frappe.sessions.get_csrf_token(),
			"read_only_mode": bool(frappe.flags.read_only),
			"default_route": "/project-board",
		}
	)

	# This sets bootinfo.lang to frappe.local.lang, which is a LocalProxy --
	# hence the coercion pass below, not before.
	load_translations(boot)
	boot.lang = str(boot.lang or "en")

	frappe.db.commit()  # nosemgrep: generating the CSRF token writes to the session

	return _json_safe(boot)


def _json_safe(boot: dict) -> dict:
	"""The page template runs every boot value through Jinja's `tojson`.

	Anything that is not plain JSON (a LocalProxy, a date, a Document) would
	blow up template rendering with a 500, so coerce it to a string here.
	"""
	safe = {}
	for key, value in boot.items():
		try:
			json.dumps(value)
			safe[key] = value
		except TypeError:
			safe[key] = str(value)
	return safe
