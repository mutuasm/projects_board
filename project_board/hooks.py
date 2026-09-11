app_name = "project_board"
app_title = "Project Board"
app_publisher = "Dime Tech Group"
app_description = "Jira-style project management portal for ERPNext Projects"
app_email = "smutua@dimetechgroup.com"
app_license = "mit"

required_apps = ["frappe/erpnext"]

# Apps screen
# -----------
add_to_apps_screen = [
	{
		"name": "project_board",
		"logo": "/assets/project_board/images/logo.svg",
		"title": "Project Board",
		"route": "/project-board",
		"has_permission": "project_board.api.check_app_permission",
	}
]

# Website
# -------
website_route_rules = [
	{"from_route": "/project-board/<path:app_path>", "to_route": "project-board"},
]
