import frappe
import requests
from frappe.model.workflow import apply_workflow

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

def on_change(doc, method):
	"""
		Handle changes to Advance Request documents,
		specifically for workflow state transitions.
	"""
	old_doc = doc.get_doc_before_save()

	if not old_doc:
		return

	if (
		old_doc.workflow_state == "Payment Rejected"
		and doc.workflow_state == "Initiate Payment"
	):
		frappe.db.set_value("Advance Request", doc.name, {
			"api_status": "",
			"api_response": "",
			"rejection_reason": "",
		}, update_modified=False)

		frappe.msgprint("Request reset! You can now proceed again.", alert=True)
		return

	if (
		old_doc.workflow_state != "Payment Initiated"
		and doc.workflow_state == "Payment Initiated"
		and doc.api_status not in ["Sent", "Completed", "Payment Rejected"]
	):
		frappe.msgprint("Payment request sent to external system", alert=True)

		frappe.enqueue(
			"fujishkahr.api.api.call_external_api",
			docname=doc.name
		)

def call_external_api(docname):
	"""
		API for sending Advance Request data to external system when workflow
		state changes to "Payment Initiated"
		also handles the response and updates the Advance Request accordingly
	"""
	doc = frappe.get_doc("Advance Request", docname)

	# Get branch from employee
	emp_branch = frappe.db.get_value(
		"Employee", doc.employee, "branch"
	)

	if not emp_branch:
		doc.db_set("api_status", "Error")
		doc.db_set("api_response",
			f"No branch linked to employee {doc.employee}")
		frappe.log_error("API ERROR",
			f"No branch linked to employee {doc.employee}")
		return

	# Get token from Branch Integration for this branch
	branch = frappe.db.get_value(
		"Branch Integration",
		{
			"branch": emp_branch,
			"branch_erpnext_status": "Accepted"
		},
		["token", "endpoint"],
		as_dict=True
	)

	if not branch:
		doc.db_set("api_status", "Error")
		doc.db_set("api_response",
			f"No active Branch Integration found for branch {emp_branch}")
		frappe.log_error("API ERROR",
			f"No active Branch Integration for branch {emp_branch}")
		return

	employee_advance = frappe.db.get_value(
		"Employee Advance",
		{"advance_request": doc.name},
		"name"
	)

	data = {
		"eap_employee_id":     doc.employee,
		"eap_employee_name":   doc.employee_name,
		"eap_advance_id":      employee_advance or "",
		"eap_advance_request": doc.name,
		"eap_amount":          doc.approved_amount,
		"eap_request_date":    str(doc.posting_date)
	}

	frappe.log_error(title="API REQUEST", message=str(data))

	try:
		response = requests.post(
			branch.endpoint.rstrip('/') + "/erpnext/employee-advance/create",
			json=data,
			headers={
				"Content-Type": "application/json",
				"Accept":       "application/json",
				"erpnexttoken": branch.token,
				"User-Agent":   "Frappe"
			},
			timeout=10
		)

		doc.db_set("api_response", response.text)

		if response.status_code != 200:
			doc.db_set("api_status", "Failed")
			frappe.log_error("API FAILED", response.text)
			return

		doc.db_set("api_status", "Sent")

	except requests.exceptions.ConnectionError:
		doc.db_set("api_status", "Error")
		doc.db_set("api_response", "Connection error - could not reach external server")
		frappe.log_error("API ERROR", "Connection error")

	except requests.exceptions.Timeout:
		doc.db_set("api_status", "Error")
		doc.db_set("api_response", "Request timed out")
		frappe.log_error("API ERROR", "Timeout")

	except Exception as e:
		doc.db_set("api_status", "Error")
		doc.db_set("api_response", str(e))
		frappe.log_error("API ERROR", str(e))

@frappe.whitelist(allow_guest=True)
def payment_callback():
	"""
	Endpoint for external system to send payment status updates
	Handles: Approved, Rejected, Cancelled
	Token verified per branch from Branch Integration
	"""
	try:
		data = frappe.request.get_json()
		frappe.log_error("CALLBACK RECEIVED", str(data))

		# Get token from header
		token = frappe.request.headers.get("X-API-Key")

		if not token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		# Validate required fields
		advance_request = data.get("advance_request")
		status          = data.get("status")
		reason          = data.get("reject_reason")

		if not advance_request:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing advance_request"}

		if status not in ["Approved", "Rejected", "Cancelled"]:
			frappe.local.response.http_status_code = 400
			return {"error": "Invalid status"}

		# Get employee and branch from Advance Request
		employee = frappe.db.get_value(
			"Advance Request", advance_request, "employee"
		)
		emp_branch = frappe.db.get_value(
			"Employee", employee, "branch"
		)

		# Get callback token from Branch Integration for this branch
		callback_token = frappe.db.get_value(
			"Branch Integration",
			{
				"branch":                emp_branch,
				"branch_erpnext_status": "Accepted"
			},
			"callback_token"
		)

		# Verify token
		if not callback_token or token != callback_token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		frappe.set_user("Administrator")

		doc = frappe.get_doc("Advance Request", advance_request)

		# Prevent duplicate processing
		if status != "Cancelled" and doc.api_status in ["Completed", "Payment Rejected"]:
			return {"message": "Already processed"}

		# Handle Rejection
		if status == "Rejected":
			doc.db_set("rejection_reason", reason or "No reason provided")
			doc.reload()
			apply_workflow(doc, "Reject Payment")
			doc.db_set("api_status", "Payment Rejected")
			send_rejection_email(doc, reason)

		# Handle Approval
		elif status == "Approved":
			create_payment_entry(doc)
			doc.db_set("api_status", "Completed")

		# Handle Cancellation
		elif status == "Cancelled":
			cancel_payment_entry(doc)

		return {"message": "Processed successfully"}

	except Exception as e:
		frappe.log_error("CALLBACK ERROR", frappe.get_traceback())
		frappe.local.response.http_status_code = 500
		return {"error": str(e)}

	finally:
		frappe.set_user("Guest")


def cancel_payment_entry(doc):
	"""
	Cancel Payment Entry linked to Advance Request
	Reset Employee Advance to Unpaid
	Reset Advance Request back to Payment Initiated
	"""
	# Get Employee Advance linked to this Advance Request
	employee_advance = frappe.db.get_value(
		"Employee Advance",
		{"advance_request": doc.name},
		"name"
	)

	if not employee_advance:
		frappe.log_error(
			"Cancel Error",
			f"No Employee Advance found for {doc.name}"
		)
		return

	# Find submitted Payment Entry for this Employee Advance
	payment_entry = frappe.db.get_value(
		"Payment Entry Reference",
		{
			"reference_doctype": "Employee Advance",
			"reference_name":    employee_advance
		},
		"parent"
	)

	if not payment_entry:
		frappe.log_error(
			"Cancel Error",
			f"No Payment Entry found for {employee_advance}"
		)
		return

	# Cancel Payment Entry if submitted
	pe_doc = frappe.get_doc("Payment Entry", payment_entry)
	if pe_doc.docstatus == 1:
		pe_doc.cancel()
		frappe.log_error(
			"Payment Entry Cancelled",
			f"{payment_entry} cancelled successfully"
		)

	# Reset Employee Advance to Unpaid
	frappe.db.set_value(
		"Employee Advance",
		employee_advance,
		"status", "Unpaid"
	)

	# Reset Advance Request to Payment Initiated using existing Reopen transition
	doc.reload()
	if doc.workflow_state == "Paid":
		apply_workflow(doc, "Reopen")

	# Reset API fields
	doc.db_set("api_status", "")
	doc.db_set("api_response",
		"Payment cancelled by external system. Waiting for new payment.")

	frappe.log_error(
		"Advance Request Reset",
		f"{doc.name} reset to Payment Initiated after cancellation"
	)

def create_payment_entry(doc):
	"""
	Create a Payment Entry for the approved Advance Request
	and link it to the corresponding Employee Advance record.
	After payment confirmed, enable repay_unclaimed_amount_from_salary
	so salary can now deduct the advance amount.
	"""
	employee_advance = frappe.db.get_value(
		"Employee Advance",
		{"advance_request": doc.name},
		"name"
	)

	if not employee_advance:
		frappe.log_error("No Employee Advance found", doc.name)
		return

	# Prevent duplicate payment entry
	if frappe.db.exists("Payment Entry Reference", {
		"reference_doctype": "Employee Advance",
		"reference_name": employee_advance
	}):
		frappe.log_error("Payment Entry already exists", employee_advance)
		return

	advance_doc = frappe.get_doc("Employee Advance", employee_advance)
	company = advance_doc.company

	paid_from = (
		frappe.db.get_value("Company", company, "default_bank_account")
		or frappe.db.get_value("Company", company, "default_cash_account")
	)

	if not paid_from:
		frappe.log_error("Payment Entry Error", f"No default bank/cash account for {company}")
		return

	paid_to = advance_doc.advance_account
	if not paid_to:
		frappe.log_error("Payment Entry Error", "Advance account missing in Employee Advance")
		return

	paid_from_currency = frappe.db.get_value("Account", paid_from, "account_currency")
	paid_to_currency   = frappe.db.get_value("Account", paid_to, "account_currency")

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type                = "Pay"
	pe.party_type                  = "Employee"
	pe.party                       = doc.employee
	pe.company                     = company
	pe.posting_date                = frappe.utils.nowdate()
	pe.paid_amount                 = doc.approved_amount
	pe.received_amount             = doc.approved_amount
	pe.paid_from                   = paid_from
	pe.paid_to                     = paid_to
	pe.paid_from_account_currency  = paid_from_currency
	pe.paid_to_account_currency    = paid_to_currency
	pe.source_exchange_rate        = 1
	pe.target_exchange_rate        = 1
	pe.mode_of_payment             = "Cash"
	pe.reference_no                = doc.name
	pe.reference_date              = frappe.utils.nowdate()

	pe.append("references", {
		"reference_doctype": "Employee Advance",
		"reference_name":    employee_advance,
		"allocated_amount":  doc.approved_amount
	})

	try:
		pe.insert(ignore_permissions=True)
		pe.submit()
		frappe.log_error("Payment Entry Created Successfully", pe.name)

		# Payment confirmed by Fujishka
		# NOW enable salary repayment — employee has received the money
		# This prevents "Return amount cannot be greater than unclaimed amount" error
		frappe.db.set_value(
			"Employee Advance",
			employee_advance,
			"repay_unclaimed_amount_from_salary", 1
		)
		frappe.db.commit()
		frappe.log_error("Advance Repayment Enabled", employee_advance)

	except Exception:
		frappe.log_error("Payment Entry Creation Failed", frappe.get_traceback())

def send_rejection_email(doc, reason):
	"""
		Send an email notification to HR Managers when a payment request is rejected,
		including details of the request and the reason for rejection
	"""
	hr_users = frappe.db.get_all(
		"Employee",
		filters={
			"company": doc.company,
			"status": "Active"
		},
		pluck="user_id"
	)

	hr_managers = []
	for user in hr_users:
		if not user:
			continue
		has_role = frappe.db.exists("Has Role", {
			"parent": user,
			"role": "HR Manager",
			"parenttype": "User"
		})
		if has_role:
			hr_managers.append(user)

	if not hr_managers:
		frappe.log_error(
			f"No HR Manager found for company {doc.company}",
			"Rejection Email"
		)
		return

	frappe.sendmail(
		recipients=hr_managers,
		subject=f"Payment Rejected – {doc.name} ({doc.employee_name})",
		message=f"""
			<p>Dear HR Team,</p>

			<p>The payment request has been
			<b style="color: red;">Rejected</b>.</p>

			<table border="1" cellpadding="8" cellspacing="0"
				   style="border-collapse: collapse; width: 100%;">
				<tr>
					<td><b>Request ID</b></td>
					<td>{doc.name}</td>
				</tr>
				<tr>
					<td><b>Employee</b></td>
					<td>{doc.employee_name}</td>
				</tr>
				<tr>
					<td><b>Company</b></td>
					<td>{doc.company}</td>
				</tr>
				<tr>
					<td><b>Department</b></td>
					<td>{doc.department}</td>
				</tr>
				<tr>
					<td><b>Approved Amount</b></td>
					<td>{doc.approved_amount}</td>
				</tr>
				<tr>
					<td><b>Rejection Reason</b></td>
					<td><b style="color: red;">{reason or "No reason provided"}</b></td>
				</tr>
			</table>

			<br>
			<p>Please review and take necessary action.</p>

			<p>Regards,<br>System</p>
		""",
		now=True
	)

@frappe.whitelist()
def generate_callback_token(branch_name):
	"""
	Generate and save a random callback token
	for a Branch Integration record
	"""
	import secrets
	callback_token = secrets.token_hex(32)

	frappe.db.set_value(
		"Branch Integration",
		branch_name,
		"callback_token", callback_token
	)
	frappe.db.commit()

	return callback_token