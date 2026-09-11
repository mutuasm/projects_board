app_name = "project_board"
app_title = "Project Board"
app_publisher = "Dime Tech Group"
app_description = "Jira-style project management portal for ERPNext Projects"
app_email = "smutua@dimetechgroup.com"
app_license = "mit"

required_apps = ["frappe/erpnext"]

# Apps screen
# -----------
# No tile of our own: the existing ERPNext "Projects" workspace is repointed at
# /project-board by project_board.install, so Projects is the single entry point.

after_install = "project_board.install.after_install"
after_migrate = "project_board.install.after_migrate"
before_uninstall = "project_board.install.before_uninstall"

# Website
# -------
website_route_rules = [
	{"from_route": "/project-board/<path:app_path>", "to_route": "project-board"},
]
