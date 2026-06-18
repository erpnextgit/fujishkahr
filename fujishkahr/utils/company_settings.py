import frappe
from frappe.utils import today, add_days


def get_company_settings(company):
	"""
	Fetch Company Ways Settings for a given company.
	Falls back to HR Settings if no company-specific document exists.

	Usage:
		from fujishkahr.utils.company_settings import get_company_settings

		settings = get_company_settings(company)
		if settings.send_holiday_reminders:
			# send the notification
	"""
	if company and frappe.db.exists("Company Ways Settings", company):
		return frappe.get_doc("Company Ways Settings", company)

	return frappe.get_single("HR Settings")

def get_company_from_employee(employee):
	"""
	Get company name from an employee.

	Usage:
		from fujishkahr.utils.company_settings import get_company_from_employee

		company = get_company_from_employee("EMP-0001")
	"""
	return frappe.db.get_value("Employee", employee, "company")

def get_company_settings_for_employee(employee):
	"""
	Directly get company settings from an employee name.
	Combines get_company_from_employee + get_company_settings.

	Usage:
		from fujishkahr.utils.company_settings import get_company_settings_for_employee

		settings = get_company_settings_for_employee("EMP-0001")
		if settings.send_birthday_reminders:
			# send the notification
	"""
	company = get_company_from_employee(employee)
	return get_company_settings(company)

def get_all_companies():
	"""
	Get all companies in the system dynamically.
	No hardcoding — automatically picks up any new company added.

	Usage:
		from fujishkahr.utils.company_settings import get_all_companies

		companies = get_all_companies()
		for company in companies:
			# do something
	"""
	return frappe.get_all("Company", fields=["name"])

def get_active_employees_by_company(company):
	"""
	Get all active employees for a given company.

	Usage:
		from fujishkahr.utils.company_settings import get_active_employees_by_company

		employees = get_active_employees_by_company("Company A")
		for emp in employees:
			# send notification
	"""
	return frappe.get_all(
		"Employee",
		filters={
			"company": company,
			"status": "Active",
		},
		fields=[
			"name",
			"employee_name",
			"user_id",
			"company_email",
			"personal_email",
			"date_of_birth",
			"date_of_joining",
		],
	)

def get_employee_email(employee):
	"""
	Get the best available email for an employee.
	Priority: company_email → personal_email → user_id

	Usage:
		from fujishkahr.utils.company_settings import get_employee_email

		email = get_employee_email(employee)
		if email:
			frappe.sendmail(recipients=[email], ...)
	"""
	return (
		employee.company_email
		or employee.personal_email
		or employee.user_id
		or None
	)

def get_reminder_date_limit(settings):
	"""
	Get the date limit for upcoming reminders based on frequency setting.
	Daily → tomorrow, Weekly → 7 days, Monthly → 30 days.

	Usage:
		from fujishkahr.utils.company_settings import get_reminder_date_limit

		date_limit = get_reminder_date_limit(settings)
	"""
	frequency = getattr(settings, "frequency", "Weekly")

	if frequency == "Daily":
		return add_days(today(), 1)
	elif frequency == "Monthly":
		return add_days(today(), 30)
	else:
		return add_days(today(), 7)