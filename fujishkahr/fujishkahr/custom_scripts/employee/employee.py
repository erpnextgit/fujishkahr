# Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate ,today
from frappe.utils import add_years

@frappe.whitelist()
def get_default_probation_period(company):
	"""
	Return default probation period in days from Company Ways Settings Settings.
	"""
	period = frappe.db.get_value(
		"Company Ways Settings",
		{"company": company},
		"default_probation_period"
	)
	return int(period) if period else 0

def notify_hr_probation():
	"""
	Notify HR if any employee's probation end date
	is within the configured days — in Company Ways Settings.
	"""
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "probation_end_date", "company"]
	)

	if not employees:
		return

	companies = list(set(emp.company for emp in employees if emp.company))

	for company in companies:
		settings = frappe.db.get_value(
			"Company Ways Settings",
			{"company": company},
			["notify_probation_end_date_before", "probation_end_date_notification"],
			as_dict=True
		)

		if not settings:
			continue

		notify_days   = settings.notify_probation_end_date_before or 0
		template_name = settings.probation_end_date_notification

		if not template_name:
			frappe.log_error(
				f"No probation email template configured for {company}",
				"Probation Notification"
			)
			continue

		try:
			template = frappe.get_doc("Email Template", template_name)
		except frappe.DoesNotExistError:
			frappe.log_error(
				f"Email Template '{template_name}' not found for {company}",
				"Probation Notification"
			)
			continue

		hr_emails = get_hr_emails(company)
		if not hr_emails:
			continue

		company_employees = [e for e in employees if e.company == company]

		for emp in company_employees:
			if not emp.probation_end_date:
				continue

			days_left = (getdate(emp.probation_end_date) - getdate(today())).days

			if days_left != notify_days:
				continue

			context = {
				"employee_name":     emp.employee_name,
				"probation_end_date": emp.probation_end_date,
				"days_left":         days_left
			}

			subject = frappe.render_template(
				template.subject or "Probation Ending Soon", context
			)
			message = frappe.render_template(template.response_html, context)

			frappe.sendmail(
				recipients=hr_emails,
				subject=subject,
				message=message
			)

def get_hr_emails(company):
	"""
	Get HR Manager and HR User emails for a specific company.
	"""
	hr_users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["HR User", "HR Manager"]]},
		fields=["parent"]
	)

	hr_emails = []
	for u in hr_users:
		email = frappe.db.get_value(
			"Employee",
			{"user_id": u.parent, "company": company, "status": "Active"},
			"user_id"
		)
		if email:
			hr_emails.append(email)

	return list(set(hr_emails))