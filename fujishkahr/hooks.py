app_name = "fujishkahr"
app_title = "Fujishkahr"
app_publisher = "erpnextgit@fujishkaerp.in"
app_description = "ERP next - HR and Payroll"
app_email = "erpnextgit@fujishkaerp.in"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "fujishkahr",
# 		"logo": "/assets/fujishkahr/logo.png",
# 		"title": "Fujishkahr",
# 		"route": "/fujishkahr",
# 		"has_permission": "fujishkahr.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------
app_include_css = [
	"assets/fujishkahr/css/fujishka_theme.css",
	"assets/fujishkahr/css/responsive_css.css",
]
# include js, css files in header of desk.html
# app_include_css = "/assets/fujishkahr/css/fujishkahr.css"
app_include_js = [
	"/assets/fujishkahr/js/language_switcher.js",
	"/assets/fujishkahr/js/attendance_heatmap.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/fujishkahr/css/fujishkahr.css"
# web_include_js = "/assets/fujishkahr/js/fujishkahr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "fujishkahr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Employee": "fujishkahr/custom_scripts/employee/employee.js",
	"Timesheet": "fujishkahr/custom_scripts/timesheet/timesheet.js",
	"Holiday List": "fujishkahr/custom_scripts/holiday_list/holiday_list.js",
	"Employee Checkin": "fujishkahr/custom_scripts/employee_checkin/employee_checkin.js",
	"Shift Assignment": "fujishkahr/custom_scripts/shift_assignment/shift_assignment.js",
	"Payroll Entry": "fujishkahr/custom_scripts/payroll_entry/payroll_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "fujishkahr/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "fujishkahr.utils.jinja_methods",
# 	"filters": "fujishkahr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "stems.install.before_install"
after_install = "fujishkahr.install.after_install"

# Migration
# ------------

before_migrate = "fujishkahr.setup.before_migrate"
after_migrate = "fujishkahr.setup.after_migrate"

# Uninstallation
# ------------

before_uninstall = "fujishkahr.install.before_uninstall"
# after_uninstall = "fujishkahr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "fujishkahr.utils.before_app_install"
# after_app_install = "fujishkahr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "fujishkahr.utils.before_app_uninstall"
# after_app_uninstall = "fujishkahr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "fujishkahr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Leave Application": "fujishkahr.hr.leave_notifications.CustomLeaveApplication",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee Checkin": {
		"validate": "fujishkahr.fujishkahr.custom_scripts.employee_checkin.employee_checkin.check_late_entry",
	},
	"Salary Slip": {
		"before_save": "fujishkahr.fujishkahr.custom_scripts.salary_slip.salary_slip.set_fixed_30_days",
		"before_submit": "fujishkahr.fujishkahr.custom_scripts.salary_slip.salary_slip.set_fixed_30_days",
		"on_submit":     "fujishkahr.api.payroll.on_salary_slip_submit",
		"before_cancel": "fujishkahr.fujishkahr.custom_scripts.salary_slip.salary_slip.before_salary_slip_cancel",
	},
	"Journal Entry": {
		"before_cancel": "fujishkahr.fujishkahr.custom_scripts.journal_entry.journal_entry.before_journal_entry_cancel"
	},
	"Payment Entry": {
		"on_submit": "fujishkahr.fujishkahr.custom_scripts.payment_entry.payment_entry.update_advance_request_status",
		"on_cancel": "fujishkahr.fujishkahr.custom_scripts.payment_entry.payment_entry.update_adv_req_status_on_cancel"
	},
	"Advance Request": {
		"on_change": "fujishkahr.api.api.on_change",
	},
	"Branch": {
		"before_insert": "fujishkahr.fujishkahr.custom_scripts.branch.branch.set_branch_name",
	},
	"Payroll Entry": {
		"before_cancel": "fujishkahr.api.payroll.before_payroll_cancel",
		"validate": "fujishkahr.api.payroll.reset_amended_payroll_fields",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"fujishkahr.tasks.all"
# 	],
scheduler_events = {
	"daily": [
		"fujishkahr.fujishkahr.custom_scripts.employee.employee.notify_hr_probation",
		"fujishkahr.hr.holiday_reminders.send_holiday_reminders",
		"fujishkahr.hr.birthday_reminders.send_birthday_reminders",
		"fujishkahr.hr.anniversary_reminders.send_work_anniversary_reminders",
	],
	"cron": {
		"*/1 * * * *": [
			"fujishkahr.api.payroll.process_pending_payroll_entries"
		]
	}
}

# 	"hourly": [
# 		"fujishkahr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"fujishkahr.tasks.weekly"
# 	],
# 	"monthly": [
# 		"fujishkahr.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "fujishkahr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "fujishkahr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "fujishkahr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["fujishkahr.utils.before_request"]
# after_request = ["fujishkahr.utils.after_request"]

# Job Events
# ----------
# before_job = ["fujishkahr.utils.before_job"]
# after_job = ["fujishkahr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"fujishkahr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
	{
		"doctype": "Custom HTML Block",
		"filters": [
			["name", "=", "Welcome Message"]
		]
	}
]

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

