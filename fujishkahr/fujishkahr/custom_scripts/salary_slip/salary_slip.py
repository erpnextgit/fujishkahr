import frappe

def set_fixed_30_days(doc, method):
	"""
	Set total working days and adjust payment days
	based on LWP if the setting is enabled in Company Ways Settings.
	"""
	settings = frappe.db.get_value(
		"Company Ways Settings",
		{"company": doc.company},
		["enable_fixed_payroll_days", "fixed_working_days"],
		as_dict=True
	)

	if not settings or not settings.enable_fixed_payroll_days:
		return

	fixed_days = settings.fixed_working_days or 30
	lwp        = doc.leave_without_pay or 0

	doc.total_working_days = fixed_days
	doc.payment_days       = fixed_days - lwp
	doc.calculate_net_pay()