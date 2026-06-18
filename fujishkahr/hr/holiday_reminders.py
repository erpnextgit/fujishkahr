import frappe
from fujishkahr.utils.company_settings import (
	get_company_settings,
	get_all_companies,
	get_active_employees_by_company,
	get_employee_email,
	get_reminder_date_limit,
)
from frappe.utils import today


def send_holiday_reminders():
	"""
	Sends holiday reminders to employees per company.
	Runs daily via scheduler.
	Each company is checked against Company Ways Settings.
	"""
	companies = get_all_companies()

	for company in companies:
		settings = get_company_settings(company.name)

		if not settings.send_holiday_reminders:
			frappe.logger().info(f"Holiday reminders disabled for {company.name}. Skipping.")
			continue

		holiday_list = frappe.db.get_value("Company", company.name, "default_holiday_list")
		if not holiday_list:
			frappe.logger().info(f"No default holiday list for {company.name}. Skipping.")
			continue

		date_limit = get_reminder_date_limit(settings)

		upcoming_holidays = frappe.get_all(
			"Holiday",
			filters={
				"parent": holiday_list,
				"holiday_date": ["between", [today(), date_limit]],
			},
			fields=["holiday_date", "description"],
		)

		if not upcoming_holidays:
			frappe.logger().info(f"No upcoming holidays for {company.name}. Skipping.")
			continue

		employees = get_active_employees_by_company(company.name)

		for employee in employees:
			email = get_employee_email(employee)
			if not email:
				continue

			holiday_lines = "<br>".join(
				[f"- {h.holiday_date} : {h.description or 'Holiday'}" for h in upcoming_holidays]
			)

			message = f"""
				Dear {employee.employee_name},<br><br>
				Here are the upcoming holidays for <b>{company.name}</b>:<br><br>
				{holiday_lines}
				<br><br>Regards,<br>HR Team
			"""

			frappe.sendmail(
				recipients=[email],
				subject=f"Upcoming Holidays - {company.name}",
				message=message,
			)

		frappe.logger().info(
			f"Holiday reminders sent for {company.name} — {len(employees)} employees."
		)