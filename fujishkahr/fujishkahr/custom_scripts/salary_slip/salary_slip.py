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

def before_salary_slip_cancel(doc, method):
	"""
	Before cancelling a Salary Slip, check if there are any linked Payroll Entries.
	If there are, prevent cancellation and prompt the user to cancel the PE first.
	"""
	if not doc.payroll_entry:
		return

	api_pushed = frappe.db.get_value(
		"Payroll Entry", doc.payroll_entry, "custom_api_pushed"
	)

	if not api_pushed:
		return

	frappe.throw(
		msg=(
			"Cannot cancel this Salary Slip directly. "
			"Please use the <b>Request Cancellation</b> button "
			"on the Payroll Entry instead."
		),
		title="Cancel Not Allowed"
	)