# Copyright (c) 2026, erpnextgit@fujishkaerp.in
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	filters.company = frappe.defaults.get_user_default("Company")
	return columns, data, None, None, summary


def get_columns():
	return [
		{"label": "Date", "fieldname": "attendance_date", "fieldtype": "Date", "width": 120},
		{"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "Employee Name", "fieldname": "employee_name", "width": 180},
		{"label": "Shift Type", "fieldname": "shift", "fieldtype": "Link", "options": "Shift Type", "width": 140},
		{"label": "Status", "fieldname": "status", "width": 100},
		{"label": "In Time", "fieldname": "in_time", "fieldtype": "Time", "width": 160},
		{"label": "Out Time", "fieldname": "out_time", "fieldtype": "Time", "width": 160},
		{"label": "Working Hours", "fieldname": "working_time", "fieldtype": "Data", "width": 120},
		{"label": "Break Hours", "fieldname": "break_time", "fieldtype": "Data", "width": 110},
		{"label": "Actual Working Hours", "fieldname": "actual_working_time", "fieldtype": "Data", "width": 140},
		{"label": "OT Hours", "fieldname": "ot_time", "fieldtype": "Data", "width": 100},		{"label": "Late Entry", "fieldname": "late_entry", "fieldtype": "Check", "width": 100},
		{"label": "Early Exit", "fieldname": "early_exit", "fieldtype": "Check", "width": 100},
		{"label": "Remarks", "fieldname": "remarks", "width": 150},
	]

def decimal_to_time(decimal_hours):
	if not decimal_hours:
		return "00:00"

	hours = int(decimal_hours)
	minutes = int(round((decimal_hours - hours) * 60))

	return f"{hours:02d}:{minutes:02d}"

def get_data(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND att.company = %(company)s"

	if filters.get("department"):
		conditions += " AND emp.department = %(department)s"

	data = frappe.db.sql(f"""
		SELECT
			att.attendance_date,
			att.employee,
			emp.employee_name,
			att.shift,
			att.status,
			att.in_time,
			att.out_time,
			att.working_hours,
			att.late_entry,
			att.early_exit
		FROM `tabAttendance` att
		JOIN `tabEmployee` emp ON emp.name = att.employee
		WHERE att.attendance_date 
			BETWEEN %(from_date)s AND %(to_date)s
		{conditions}
		ORDER BY att.attendance_date, emp.employee_name
	""", filters, as_dict=1)

	for row in data:

		shift_config = frappe.db.get_value(
			"Shift Type",
			row.shift,
			["std_working_hours", "allow_break_time", "break_hours"],
			as_dict=1
		) if row.shift else None

		std_hours = shift_config.std_working_hours if shift_config and shift_config.std_working_hours else 0
		allow_break = shift_config.allow_break_time if shift_config else 0
		break_hours = shift_config.break_hours if shift_config and shift_config.break_hours else 0
		row.break_hours = break_hours if allow_break else 0

		# Actual Working Hours Calculation
		if row.working_hours and row.status == "Present":

			if allow_break and break_hours:
				row.actual_working_hours = round(
					max(row.working_hours - break_hours, 0), 2
				)
			else:
				row.actual_working_hours = row.working_hours

		else:
			row.actual_working_hours = row.working_hours or 0

		# OT Calculation
		if std_hours and row.actual_working_hours > std_hours:
			row.ot_hours = round(row.actual_working_hours - std_hours, 2)
		else:
			row.ot_hours = 0

		# Time Formatting
		row.working_time = decimal_to_time(row.working_hours)
		row.actual_working_time = decimal_to_time(row.actual_working_hours)
		row.ot_time = decimal_to_time(row.ot_hours)
		row.break_time = decimal_to_time(row.break_hours)

		row.remarks = generate_remarks(row)

		if row.in_time:
			row.in_time = get_datetime(row.in_time).time()

		if row.out_time:
			row.out_time = get_datetime(row.out_time).time()

	return data

def generate_remarks(row):
	remarks = []

	if row.status == "Absent":
		remarks.append("A")

	if row.status == "Half Day":
		remarks.append("HD")

	if row.late_entry:
		remarks.append("LT")

	if row.early_exit:
		remarks.append("EI")

	if row.ot_hours and row.ot_hours > 0:
		remarks.append("OT")

	return "-".join(remarks) if remarks else ""

def get_summary(data):
	total_present = len([d for d in data if d.status == "Present"])
	total_absent = len([d for d in data if d.status == "Absent"])
	total_half_day = len([d for d in data if d.status == "Half Day"])
	total_late = len([d for d in data if d.late_entry])
	total_early_exit = len([d for d in data if d.early_exit])

	return [
		{"label": "Present", "value": total_present, "indicator": "Green"},
		{"label": "Absent", "value": total_absent, "indicator": "Red"},
		{"label": "Half Day", "value": total_half_day, "indicator": "Orange"},
		{"label": "Late Entry", "value": total_late, "indicator": "Dark Blue"},
		{"label": "Early Exit", "value": total_early_exit, "indicator": "Light Blue"},
	]