import frappe

@frappe.whitelist()
def set_user_language(lang):
	"""Set the language preference for the logged-in user."""
	if lang in ["en", "ar"]:
		frappe.db.set_value("User", frappe.session.user, "language", lang)
		frappe.clear_cache(user=frappe.session.user)

@frappe.whitelist()
def get_employee_attendance_heatmap(employee, year):
	"""Get attendance data for an employee for a given year to render a heatmap."""
	data = {}

	attendance = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [f"{year}-01-01", f"{year}-12-31"]]
		},
		fields=[
			"attendance_date",
			"status",
			"late_entry",
			"early_exit"
		]
	)

	for row in attendance:
		date = row.attendance_date.strftime("%Y-%m-%d")

		if row.status == "Absent":
			data[date] = "absent"

		elif row.status == "On Leave":
			data[date] = "leave"

		elif row.status == "Work From Home":
			data[date] = "wfh"

		elif row.status == "Half Day":
			data[date] = "half_day"

		elif row.late_entry or row.early_exit:
			data[date] = "late_early"

		else:
			data[date] = "present"

	return data
