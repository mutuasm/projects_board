import json
from urllib.parse import urlencode

import frappe
from frappe.boot import load_translations

no_cache = 1


def get_context(context):
	# Guests would get the page shell and then a wall of failed API calls, so
	# send them to log in first and bring them back to the page they asked for.
	if frappe.session.user == "Guest":
		target = frappe.request.full_path.rstrip("?") if frappe.request else "/project-board"
		frappe.local.flags.redirect_location = "/login?" + urlencode({"redirect-to": target})
		raise frappe.Redirect(302)  # not 301: browsers cache those, and this one is temporary

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
			# only used when the page is served on a port (bench serve); behind
			# nginx the socket shares the page's origin
			"socketio_port": frappe.conf.socketio_port or 9000,
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
