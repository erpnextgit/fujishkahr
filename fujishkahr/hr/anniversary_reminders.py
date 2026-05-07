import frappe
from fujishkahr.utils.company_settings import (
	get_company_settings,
	get_all_companies,
	get_active_employees_by_company,
	get_employee_email,
)
from frappe.utils import today, getdate


def send_work_anniversary_reminders():
	"""
	Sends work anniversary reminders to employees per company.
	Runs daily via scheduler.
	Each company is checked against Company Ways Settings.
	"""
	companies = get_all_companies()

	for company in companies:
		settings = get_company_settings(company.name)

		if not settings.send_work_anniversary_reminders:
			frappe.logger().info(f"Anniversary reminders disabled for {company.name}. Skipping.")
			continue

		employees = get_active_employees_by_company(company.name)

		for employee in employees:
			if not employee.date_of_joining:
				continue

			doj = getdate(employee.date_of_joining)
			today_date = getdate(today())

			if doj.day == today_date.day and doj.month == today_date.month:
				years = today_date.year - doj.year
				if years <= 0:
					continue

				email = get_employee_email(employee)
				if not email:
					continue

				message = f"""
					Dear {employee.employee_name},<br><br>
					Congratulations on completing <b>{years} year(s)</b> with us! 🎊<br><br>
					Thank you for your dedication and hard work.<br><br>
					Regards,<br>HR Team - {company.name}
				"""

				frappe.sendmail(
					recipients=[email],
					subject=f"Work Anniversary - {years} Year(s) with {company.name}!",
					message=message,
				)

				frappe.logger().info(
					f"Anniversary reminder sent to {employee.employee_name} ({company.name}) — {years} year(s)."
				)