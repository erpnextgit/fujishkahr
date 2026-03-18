import frappe

def set_fixed_30_days(doc, method):
	"""
		Set total working days to 30 and adjust payment days
		based on LWP if the setting is enabled.
	"""
	settings = frappe.get_single("Fujishkahr Settings")

	if not settings.enable_fixed_payroll_days:
		return

	fixed_days = settings.fixed_working_days or 30
	lwp = doc.leave_without_pay or 0

	doc.total_working_days = fixed_days
	doc.payment_days = fixed_days - lwp
	doc.calculate_net_pay()