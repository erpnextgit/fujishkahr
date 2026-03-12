# Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate ,today
from frappe.utils import add_years

@frappe.whitelist()
def get_default_probation_period():
	"""
	Return default probation period in days from Fujishkahr Settings.
	"""
	period = frappe.db.get_single_value("Fujishkahr Settings", "default_probation_period")
	return int(period)

def notify_hr_probation():
	"""
	Notify HR if any employee's probation end date is within the configured days.
	"""
	notify_days = frappe.db.get_single_value("Fujishkahr Settings", "notify_probation_end_date_before") or 0
	template_name = frappe.db.get_single_value("Fujishkahr Settings", "probation_end_date_notification")

	if not template_name:
		frappe.log_error("No email template configured in Fujishkahr Settings", "Probation Notification")
		return

	hr_roles = ["HR User", "HR Manager"]
	hr_users = frappe.get_all("Has Role", filters={"role": ["in", hr_roles]}, fields=["parent"])
	hr_emails = []
	for u in hr_users:
		email = frappe.get_value("User", u.parent, "email")
		if email:
			hr_emails.append(email)

	if not hr_emails:
		return

	try:
		template = frappe.get_doc("Email Template", template_name)
	except frappe.DoesNotExistError:
		frappe.log_error(f"Email Template '{template_name}' not found", "Probation Notification")
		return

	employees = frappe.get_all("Employee", fields=["name", "employee_name", "probation_end_date"])
	for emp in employees:
		if not emp.probation_end_date:
			continue

		days_left = (getdate(emp.probation_end_date) - getdate(today())).days
		if days_left != notify_days:
			continue

		context = {
			"employee_name": emp.employee_name,
			"probation_end_date": emp.probation_end_date,
			"days_left": days_left
		}

		subject = frappe.render_template(template.subject or "Probation Ending Soon", context)
		message = frappe.render_template(template.response_html, context)

		frappe.sendmail(
			recipients=hr_emails,
			subject=subject,
			message=message
		)
