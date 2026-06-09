import frappe

def before_journal_entry_cancel(doc, method):
	"""
	Before cancelling a Journal Entry, check if there are any linked Payroll Entries.
	If there are, prevent cancellation and prompt the user to cancel the Payroll Entries first.
	"""
	for row in doc.accounts:
		if row.reference_type == "Payroll Entry" and row.reference_name:
			api_pushed = frappe.db.get_value(
				"Payroll Entry", row.reference_name, "custom_api_pushed"
			)
			
			if api_pushed:
				frappe.throw(
					msg=(
						"Cannot cancel this Journal Entry directly. "
						"It is linked to Payroll Entry <b>{}</b> which has "
						"already been sent to the external payment system. "
						"Please use the <b>Request Cancellation</b> button "
						"on the Payroll Entry instead.".format(row.reference_name)
					),
					title="Cancel Not Allowed"
				)
			break
