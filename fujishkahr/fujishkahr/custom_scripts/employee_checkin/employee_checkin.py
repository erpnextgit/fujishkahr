import frappe
from frappe.utils import get_datetime
from datetime import timedelta

def check_late_entry(doc, method):
	"""
		Checks if an Employee Checkin is late based on the shift start time and grace period.
		Sets late_entry fields accordingly.
	"""

	if doc.log_type != "IN":
		return

	if not doc.shift_start:
		return

	checkin_time = get_datetime(doc.time)
	shift_start = get_datetime(doc.shift_start)

	shift = frappe.get_doc("Shift Type", doc.shift)
	grace = shift.late_entry_grace_period or 0

	late_limit = shift_start + timedelta(minutes=grace)

	if checkin_time > late_limit:
		doc.late_entry = 1
	else:
		doc.late_entry = 0