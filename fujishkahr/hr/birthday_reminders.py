import frappe
from fujishkahr.utils.company_settings import (
	get_company_settings,
	get_all_companies,
	get_active_employees_by_company,
	get_employee_email,
)
from frappe.utils import today, getdate


def send_birthday_reminders():
	"""
	Sends birthday reminders to employees per company.
	Runs daily via scheduler.
	Each company is checked against Company Ways Settings.
	"""
	companies = get_all_companies()

	for company in companies:
		settings = get_company_settings(company.name)

		if not settings.send_birthday_reminders:
			frappe.logger().info(f"Birthday reminders disabled for {company.name}. Skipping.")
			continue

		employees = get_active_employees_by_company(company.name)

		for employee in employees:
			if not employee.date_of_birth:
				continue

			dob = getdate(employee.date_of_birth)
			today_date = getdate(today())

			if dob.day == today_date.day and dob.month == today_date.month:
				email = get_employee_email(employee)
				if not email:
					continue

				message = f"""
					Dear {employee.employee_name},<br><br>
					Wishing you a very <b>Happy Birthday</b>! 🎉<br><br>
					May this year bring you great success and happiness.<br><br>
					Regards,<br>HR Team - {company.name}
				"""

				frappe.sendmail(
					recipients=[email],
					subject=f"Happy Birthday, {employee.employee_name}! 🎂",
					message=message,
				)

				frappe.logger().info(
					f"Birthday reminder sent to {employee.employee_name} ({company.name})."
				)