import frappe
from frappe.model.workflow import apply_workflow

def update_advance_request_status(doc, method):
	"""
		Update Advance Request status to "Complete Payment" when Payment Entry is submitted
	"""
	for ref in doc.references:
		if ref.reference_doctype == "Employee Advance":
			emp_adv = frappe.get_doc("Employee Advance", ref.reference_name)

			if emp_adv.advance_request and emp_adv.status == "Paid":
				adv_req = frappe.get_doc("Advance Request", emp_adv.advance_request)

				if adv_req.workflow_state != "Paid":
					apply_workflow(adv_req, "Complete Payment")


def update_adv_req_status_on_cancel(doc, method):
	"""
		Revert Advance Request workflow when Payment Entry is cancelled
	"""
	for ref in doc.references:
		if ref.reference_doctype == "Employee Advance":
			emp_adv = frappe.get_doc("Employee Advance", ref.reference_name)

			if emp_adv.advance_request:
				adv_req = frappe.get_doc("Advance Request", emp_adv.advance_request)

				if adv_req.workflow_state == "Paid":
					try:
						apply_workflow(adv_req, "Reopen")
					except Exception:
						frappe.log_error(frappe.get_traceback(), "Workflow Cancel Error")