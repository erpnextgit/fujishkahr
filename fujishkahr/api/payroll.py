import frappe
import requests

def on_salary_slip_submit(doc, method):
	"""
	Just log — scheduler will pick it up
	"""
	if not doc.payroll_entry:
		return

	already_pushed = frappe.db.get_value(
		"Payroll Entry", doc.payroll_entry, "custom_api_pushed"
	)
	if already_pushed:
		return

	payroll_doc = frappe.get_doc("Payroll Entry", doc.payroll_entry)
	total_employees = payroll_doc.number_of_employees

	submitted_slips = frappe.db.count(
		"Salary Slip",
		filters={
			"payroll_entry": doc.payroll_entry,
			"docstatus": 1
		}
	)

	frappe.log_error(
		"Payroll Slip Check",
		f"{submitted_slips} of {total_employees} slips submitted for {doc.payroll_entry}"
	)

def process_payroll_submission(docname):
	"""
	Background job:
	1. Calculate total salary and deduction
	2. Push to external system via Branch Integration
	"""
	doc = frappe.get_doc("Payroll Entry", docname)

	# Step 1 - Calculate totals
	total_salary, total_deduction = calculate_payroll_totals(doc)

	if not total_salary:
		frappe.log_error(
			"Payroll Submission Error",
			f"No salary amount calculated for {docname}"
		)
		return

	# Step 2 - Store in custom fields
	frappe.db.set_value("Payroll Entry", docname, {
		"custom_total_salary":    total_salary,
		"custom_total_deduction": total_deduction,
		"custom_payment_status":  "Pending",
		"custom_salary_paid":     0,
		"custom_deduction_paid":  0,
	}, update_modified=False)

	frappe.db.commit()

	# Step 3 - Push to external system
	push_to_external_system(doc, total_salary, total_deduction)

def calculate_payroll_totals(doc):
	"""
	Loop all salary slips under this payroll entry.
	Calculate:
	  - total_salary    = sum of net_pay across all slips
	  - total_deduction = sum of employee PF+ESI + employer PF+ESI
	"""
	salary_slips = frappe.get_all(
		"Salary Slip",
		filters={
			"payroll_entry": doc.name,
			"docstatus": 1
		},
		fields=["name", "net_pay", "gross_pay"]
	)

	if not salary_slips:
		frappe.log_error(
			"Payroll Totals Error",
			f"No submitted salary slips found for {doc.name}"
		)
		return 0, 0

	total_salary    = 0
	total_deduction = 0

	for slip in salary_slips:
		slip_doc = frappe.get_doc("Salary Slip", slip.name)

		total_salary += slip_doc.net_pay or 0

		employee_pf  = 0
		employee_esi = 0
		other_deductions = 0

		for row in slip_doc.deductions:
			component = frappe.get_cached_doc(
				"Salary Component", row.salary_component
			)

			if component.is_employee_pf:
				employee_pf += row.amount or 0

			elif component.is_employee_esi:
				employee_esi += row.amount or 0

			else:
				other_deductions += row.amount or 0

		employer_pf = employee_pf

		employer_esi = (
			(slip_doc.gross_pay * 0.0325)
			if (slip_doc.gross_pay or 0) <= 21000
			else 0
		)

		slip_deduction = (
			employee_pf +
			employee_esi +
			employer_pf +
			employer_esi +
			other_deductions
		)

		total_deduction += slip_deduction

	return round(total_salary, 2), round(total_deduction, 2)


def push_to_external_system(doc, total_salary, total_deduction):
	"""
	Push payroll totals to external system
	using Branch Integration endpoint and token
	"""
	# Get Branch Integration for this company
	branch = frappe.db.get_value(
		"Branch Integration",
		{
			"company":               doc.company,
			"branch_erpnext_status": "Accepted"
		},
		["endpoint", "token"],
		as_dict=True
	)

	if not branch:
		frappe.log_error(
			"Payroll API Error",
			f"No active Branch Integration found for company {doc.company}"
		)
		return

	if not branch.endpoint or not branch.token:
		frappe.log_error(
			"Payroll API Error",
			f"Endpoint or token missing in Branch Integration for {doc.company}"
		)
		return

	data = {
		"payroll_id": doc.name,
		"salary":     total_salary,
		"deduction":  total_deduction,
	}

	frappe.log_error("Payroll API Request", str(data))

	try:
		response = requests.post(
			branch.endpoint.rstrip("/") + "/erpnext/salary-payment/create_salarys_payment",
			json=data,
			headers={
				"Content-Type": "application/json",
				"Accept":       "application/json",
				"erpnexttoken": branch.token,
				"User-Agent":   "Frappe"
			},
			timeout=10
		)

		frappe.log_error("Payroll API Response", response.text)

		if response.status_code != 200:
			frappe.db.set_value(
				"Payroll Entry", doc.name,
				"custom_api_pushed", 0,
				update_modified=False
			)
			frappe.log_error(
				"Payroll API Failed",
				response.text
			)
			return

		frappe.db.set_value(
			"Payroll Entry", doc.name,
			"custom_api_pushed", 1,
			update_modified=False
		)
		frappe.db.commit()

	except requests.exceptions.ConnectionError:
		frappe.log_error("Payroll API Error", "Connection error")

	except requests.exceptions.Timeout:
		frappe.log_error("Payroll API Error", "Request timed out")

	except Exception as e:
		frappe.log_error("Payroll API Error", str(e))
  
@frappe.whitelist(allow_guest=True)
def receive_payment():
	"""
	Endpoint to receive payment callbacks from external system
	"""
	try:
		data = frappe.request.get_json()
		frappe.log_error("Payroll Callback Received", str(data))

		token = frappe.request.headers.get("X-API-Key")
		if not token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		payroll_id = data.get("sp_payment_id")
		sp_type    = data.get("sp_type")
		amount     = data.get("sp_amount")
		sp_date    = data.get("sp_date")

		if not payroll_id:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing sp_payment_id"}

		if sp_type not in [1, 2]:
			frappe.local.response.http_status_code = 400
			return {"error": "Invalid sp_type. Must be 1 or 2"}

		if not amount:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing sp_amount"}

		if not frappe.db.exists("Payroll Entry", payroll_id):
			frappe.local.response.http_status_code = 404
			return {"error": f"Payroll Entry {payroll_id} not found"}

		company = frappe.db.get_value("Payroll Entry", payroll_id, "company")

		callback_token = frappe.db.get_value(
			"Branch Integration",
			{
				"company":               company,
				"branch_erpnext_status": "Accepted"
			},
			"callback_token"
		)

		if not callback_token or token != callback_token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		frappe.set_user("Administrator")

		process_payment_callback(
			payroll_id=payroll_id,
			sp_type=sp_type,
			amount=float(amount),
			sp_date=sp_date
		)

		return {"message": "Processed successfully"}

	except Exception as e:
		frappe.log_error("Payroll Callback Error", frappe.get_traceback())
		frappe.local.response.http_status_code = 500
		return {"error": str(e)}

	finally:
		frappe.set_user("Guest")


def process_payment_callback(payroll_id, sp_type, amount, sp_date):
	"""
	Update the payroll entry based on payment callback:
	- sp_type 1 = salary payment, 2 = deduction payment
	- Update custom fields for amount paid so far
	- If total paid >= total salary/deduction, create JE and mark as paid
	"""
	doc = frappe.get_doc("Payroll Entry", payroll_id)

	if sp_type == 1:
		new_salary_paid = (doc.custom_salary_paid or 0) + amount
		frappe.db.set_value(
			"Payroll Entry", payroll_id,
			"custom_salary_paid", new_salary_paid,
			update_modified=False
		)
		frappe.log_error(
			"Payroll Callback Type 1",
			f"Salary paid so far: {new_salary_paid} / {doc.custom_total_salary}"
		)
		if round(new_salary_paid, 2) >= round(doc.custom_total_salary, 2):
			if not doc.custom_salary_pe_created:
				create_salary_journal_entry(doc, new_salary_paid, sp_date)
				mark_salary_slips(payroll_id, "Paid")

	elif sp_type == 2:
		new_deduction_paid = (doc.custom_deduction_paid or 0) + amount
		frappe.db.set_value(
			"Payroll Entry", payroll_id,
			"custom_deduction_paid", new_deduction_paid,
			update_modified=False
		)
		frappe.log_error(
			"Payroll Callback Type 2",
			f"Deduction paid so far: {new_deduction_paid} / {doc.custom_total_deduction}"
		)
		if round(new_deduction_paid, 2) >= round(doc.custom_total_deduction, 2):
			if not doc.custom_deduction_pe_created:
				create_deduction_journal_entry(doc, new_deduction_paid, sp_date)
				mark_salary_slips(payroll_id, "Completed")

	frappe.db.commit()
	doc.reload()
	check_and_mark_paid(doc)


def create_salary_journal_entry(doc, amount, sp_date):
	"""
	Create Journal Entry to record salary payment
	"""
	company = doc.company
	payroll_payable = frappe.db.get_value("Company", company, "default_payroll_payable_account")
	bank_account = (
		frappe.db.get_value("Company", company, "default_bank_account")
		or frappe.db.get_value("Company", company, "default_cash_account")
	)

	if not payroll_payable or not bank_account:
		frappe.log_error("Salary JE Error", f"Accounts not set for {company}")
		return

	try:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Bank Entry"
		je.company      = company
		je.posting_date = sp_date or frappe.utils.nowdate()
		je.user_remark  = f"Salary payment for Payroll Entry {doc.name}"
		je.cheque_no    = doc.name
		je.cheque_date  = sp_date or frappe.utils.nowdate()
		cost_center = frappe.db.get_value("Company", company, "cost_center")

		je.append("accounts", {
			"account":                   payroll_payable,
			"debit_in_account_currency":  amount,
			"credit_in_account_currency": 0,
			"reference_type":            "Payroll Entry",
			"reference_name":            doc.name,
			"cost_center":               cost_center,
		})
		je.append("accounts", {
			"account":                   bank_account,
			"debit_in_account_currency":  0,
			"credit_in_account_currency": amount,
			"cost_center":               cost_center,
		})

		je.insert(ignore_permissions=True)
		je.submit()
		frappe.log_error("Salary JE Created", je.name)
		frappe.db.set_value("Payroll Entry", doc.name, "custom_salary_pe_created", 1, update_modified=False)
		frappe.db.commit()

	except Exception:
		frappe.log_error("Salary JE Creation Failed", frappe.get_traceback())


def create_deduction_journal_entry(doc, amount, sp_date):
	"""
	Create Journal Entry to record deduction payment
	"""
	company = doc.company
	payroll_payable = frappe.db.get_value("Company", company, "default_payroll_payable_account")
	bank_account = (
		frappe.db.get_value("Company", company, "default_bank_account")
		or frappe.db.get_value("Company", company, "default_cash_account")
	)

	if not payroll_payable or not bank_account:
		frappe.log_error("Deduction JE Error", f"Accounts not set for {company}")
		return

	try:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Bank Entry"
		je.company      = company
		je.posting_date = sp_date or frappe.utils.nowdate()
		je.user_remark  = f"Deduction payment for Payroll Entry {doc.name}"
		je.cheque_no    = doc.name
		je.cheque_date  = sp_date or frappe.utils.nowdate()

		cost_center = frappe.db.get_value("Company", company, "cost_center")

		je.append("accounts", {
			"account":                   payroll_payable,
			"debit_in_account_currency":  amount,
			"credit_in_account_currency": 0,
			"reference_type":            "Payroll Entry",
			"reference_name":            doc.name,
			"cost_center":               cost_center,
		})
		je.append("accounts", {
			"account":                   bank_account,
			"debit_in_account_currency":  0,
			"credit_in_account_currency": amount,
			"cost_center":               cost_center,
		})

		je.insert(ignore_permissions=True)
		je.submit()
		frappe.log_error("Deduction JE Created", je.name)
		frappe.db.set_value("Payroll Entry", doc.name, "custom_deduction_pe_created", 1, update_modified=False)
		frappe.db.commit()

	except Exception:
		frappe.log_error("Deduction JE Creation Failed", frappe.get_traceback())


def check_and_mark_paid(doc):
	"""
	Mark Payroll Entry as Paid only when
	both salary and deduction are fully settled.
	Salary slip status is now handled by mark_salary_slips.
	"""
	if not doc.custom_salary_pe_created or not doc.custom_deduction_pe_created:
		frappe.db.set_value(
			"Payroll Entry", doc.name,
			"custom_payment_status", "Partial",
			update_modified=False
		)
		frappe.db.commit()
		return

	frappe.db.set_value(
		"Payroll Entry", doc.name,
		"custom_payment_status", "Paid",
		update_modified=False
	)
	frappe.db.commit()
	frappe.log_error(
		"Payroll Marked Paid",
		f"{doc.name} fully settled"
	)

def mark_salary_slips(payroll_id, status):
	"""
	Mark all submitted salary slips under
	this payroll entry with the given status.

	Called twice:
	  Type 1 paid → status = "Paid"
		(employee received salary)
	  Type 2 paid → status = "Completed"
		(deductions fully settled)
	"""
	salary_slips = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": payroll_id, "docstatus": 1},
		pluck="name"
	)
	for slip_name in salary_slips:
		frappe.db.set_value(
			"Salary Slip", slip_name,
			"status", status,
			update_modified=False
		)
	frappe.db.commit()
	frappe.log_error(
		f"Salary Slips Marked {status}",
		f"{len(salary_slips)} slips marked as {status} for {payroll_id}"
	)

def process_pending_payroll_entries():
	"""
	Scheduled job — runs every 5 minutes.
	Finds submitted payroll entries that haven't been pushed yet
	and processes them.
	"""
	pending_entries = frappe.get_all(
		"Payroll Entry",
		filters={
			"docstatus": 1,
			"custom_api_pushed": 0,
		},
		fields=["name", "custom_payment_status"],
	)

	pending_entries = [
		e.name for e in pending_entries
		if not e.custom_payment_status
	]

	for docname in pending_entries:
		try:
			frappe.log_error(
				"Payroll Scheduler",
				f"Processing pending payroll entry: {docname}"
			)
			process_payroll_submission(docname)
		except Exception:
			frappe.log_error(
				"Payroll Scheduler Error",
				frappe.get_traceback()
			)

@frappe.whitelist()
def request_cancellation(payroll_id, reason):
	"""
	Employee requests cancellation of a payroll entry.
	"""
	try:
		doc = frappe.get_doc("Payroll Entry", payroll_id)

		branch = frappe.db.get_value(
			"Branch Integration",
			{
				"company":               doc.company,
				"branch_erpnext_status": "Accepted"
			},
			["endpoint", "token"],
			as_dict=True
		)

		if not branch:
			return {"status": "error", "error": "No active Branch Integration found"}

		data = {
			"payroll_id": payroll_id,
			"action":     "cancel",
			"reason":     reason
		}

		try:
			requests.post(
				branch.endpoint.rstrip("/") + "/erpnext/salary-payment/delete-payroll-payment",
				json=data,
				headers={
					"Content-Type": "application/json",
					"Accept":       "application/json",
					"erpnexttoken": branch.token,
					"User-Agent":   "Frappe"
				},
				timeout=10
			)
		except Exception:
			pass

		frappe.db.set_value("Payroll Entry", payroll_id, {
			"custom_cancel_status": "Cancel Requested",
			"custom_cancel_reason": reason,
		}, update_modified=False)
		frappe.db.commit()

		return {"status": "success"}

	except Exception as e:
		frappe.log_error("Payroll Cancel Error", frappe.get_traceback())
		return {"status": "error", "error": str(e)}


@frappe.whitelist(allow_guest=True)
def receive_cancel_response():
	"""
	Endpoint to receive cancellation approval/rejection from external system
	"""
	try:
		data = frappe.request.get_json()

		token = frappe.request.headers.get("X-Callback-Token")
		if not token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		payroll_id = data.get("payroll_id")
		status     = data.get("status")
		reason     = data.get("reason", "")

		if not payroll_id:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing payroll_id"}

		if status not in ["approved", "rejected"]:
			frappe.local.response.http_status_code = 400
			return {"error": "Invalid status. Must be approved or rejected"}

		if not frappe.db.exists("Payroll Entry", payroll_id):
			frappe.local.response.http_status_code = 404
			return {"error": f"Payroll Entry {payroll_id} not found"}

		company = frappe.db.get_value("Payroll Entry", payroll_id, "company")
		callback_token = frappe.db.get_value(
			"Branch Integration",
			{
				"company":               company,
				"branch_erpnext_status": "Accepted"
			},
			"callback_token"
		)

		if not callback_token or token != callback_token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		frappe.set_user("Administrator")

		if status == "approved":
			process_cancel_approval(payroll_id)
		elif status == "rejected":
			process_cancel_rejection(payroll_id, reason)

		return {"message": "Processed successfully"}

	except Exception as e:
		frappe.log_error("Payroll Cancel Callback Error", frappe.get_traceback())
		frappe.local.response.http_status_code = 500
		return {"error": str(e)}

	finally:
		frappe.set_user("Guest")


def process_cancel_approval(payroll_id):
	"""
	Process cancellation approval:
	- Cancel related Journal Entries and Salary Slips
	- Cancel Payroll Entry
	- Update custom fields to reflect cancellation
	"""
	cancel_journal_entries(payroll_id)

	salary_slips = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": payroll_id, "docstatus": 1},
		pluck="name"
	)
	for slip_name in salary_slips:
		try:
			frappe.get_doc("Salary Slip", slip_name).cancel()
		except Exception:
			frappe.log_error("Salary Slip Cancel Error", frappe.get_traceback())

	try:
		frappe.get_doc("Payroll Entry", payroll_id).cancel()
	except Exception:
		frappe.log_error("Payroll Entry Cancel Error", frappe.get_traceback())

	frappe.db.sql("""
		UPDATE `tabPayroll Entry`
		SET custom_cancel_status = 'Cancel Approved'
		WHERE name = %s
	""", payroll_id)

	frappe.db.commit()


def process_cancel_rejection(payroll_id, reason):
	"""
	Process cancellation rejection:
	Update custom fields to reflect rejection and reason
	"""
	frappe.db.set_value("Payroll Entry", payroll_id, {
		"custom_cancel_status":           "Cancel Rejected",
		"custom_cancel_rejection_reason": reason or "No reason provided",
	}, update_modified=False)
	frappe.db.commit()

def cancel_journal_entries(payroll_id):
	"""
	Find and cancel all Journal Entries linked to the given payroll entry
	"""
	journal_entries = list(set(frappe.get_all(
		"Journal Entry Account",
		filters={
			"reference_type": "Payroll Entry",
			"reference_name": payroll_id
		},
		pluck="parent"
	)))

	for je_name in journal_entries:
		try:
			je_doc = frappe.get_doc("Journal Entry", je_name)
			if je_doc.docstatus == 1:
				je_doc.cancel()
		except Exception:
			frappe.log_error("JE Cancel Error", frappe.get_traceback())

@frappe.whitelist(allow_guest=True)
def delete_payment():
	"""
	Endpoint called by Fujishka when they delete
	a salary or deduction payment.
	sp_type 1 = salary payment deleted
	sp_type 2 = deduction payment deleted
	"""
	try:
		data = frappe.request.get_json()

		token = frappe.request.headers.get("X-API-Key")
		if not token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		payroll_id = data.get("sp_payment_id")
		sp_type    = data.get("sp_type")

		if not payroll_id:
			frappe.local.response.http_status_code = 400
			return {"error": "Missing sp_payment_id"}

		if sp_type not in [1, 2]:
			frappe.local.response.http_status_code = 400
			return {"error": "Invalid sp_type. Must be 1 or 2"}

		if not frappe.db.exists("Payroll Entry", payroll_id):
			frappe.local.response.http_status_code = 404
			return {"error": f"Payroll Entry {payroll_id} not found"}

		company = frappe.db.get_value("Payroll Entry", payroll_id, "company")
		callback_token = frappe.db.get_value(
			"Branch Integration",
			{
				"company":               company,
				"branch_erpnext_status": "Accepted"
			},
			"callback_token"
		)

		if not callback_token or token != callback_token:
			frappe.local.response.http_status_code = 401
			return {"error": "Unauthorized"}

		frappe.set_user("Administrator")
		process_payment_deletion(payroll_id, sp_type)
		return {"message": "Processed successfully"}

	except Exception as e:
		frappe.log_error("Payment Delete Error", frappe.get_traceback())
		frappe.local.response.http_status_code = 500
		return {"error": str(e)}

	finally:
		frappe.set_user("Guest")

def process_payment_deletion(payroll_id, sp_type):
	"""
	Reset payroll fields based on which payment was deleted.
	sp_type 1 = salary payment deleted
	sp_type 2 = deduction payment deleted
	After reset, Fujishka will retry via existing receive_payment API.
	"""
	if sp_type == 1:
		cancel_journal_entry_by_type(payroll_id, "Salary payment")
		frappe.db.set_value("Payroll Entry", payroll_id, {
			"custom_salary_paid":       0,
			"custom_salary_pe_created": 0,
		}, update_modified=False)

	elif sp_type == 2:
		cancel_journal_entry_by_type(payroll_id, "Deduction payment")
		frappe.db.set_value("Payroll Entry", payroll_id, {
			"custom_deduction_paid":       0,
			"custom_deduction_pe_created": 0,
		}, update_modified=False)

	frappe.db.commit()

	doc = frappe.get_doc("Payroll Entry", payroll_id)
	update_status_after_deletion(doc)

def update_status_after_deletion(doc):
	"""
	After deletion check actual state of both
	salary and deduction to set correct statuses.

	Cases:
	  both deleted                     → Pending, slips = Submitted
	  salary deleted, deduction exists → Partial, slips = Submitted
	  deduction deleted, salary exists → Partial, slips = Paid
	"""
	salary_done    = doc.custom_salary_pe_created
	deduction_done = doc.custom_deduction_pe_created

	if not salary_done and not deduction_done:
		frappe.db.set_value(
			"Payroll Entry", doc.name,
			"custom_payment_status", "Pending",
			update_modified=False
		)
		mark_salary_slips(doc.name, "Submitted")

	elif salary_done and not deduction_done:
		frappe.db.set_value(
			"Payroll Entry", doc.name,
			"custom_payment_status", "Partial",
			update_modified=False
		)
		mark_salary_slips(doc.name, "Paid")

	elif not salary_done and deduction_done:
		frappe.db.set_value(
			"Payroll Entry", doc.name,
			"custom_payment_status", "Partial",
			update_modified=False
		)
		mark_salary_slips(doc.name, "Submitted")

	frappe.db.commit()

def cancel_journal_entry_by_type(payroll_id, remark_contains):
	"""
	Find and cancel Journal Entry linked to payroll entry
	identified by user_remark.

	remark_contains:
	  "Salary payment"    → cancels salary JE
	  "Deduction payment" → cancels deduction JE
	"""
	journal_entries = frappe.get_all(
		"Journal Entry Account",
		filters={
			"reference_type": "Payroll Entry",
			"reference_name": payroll_id
		},
		pluck="parent"
	)

	for je_name in list(set(journal_entries)):
		try:
			je_doc = frappe.get_doc("Journal Entry", je_name)
			if (
				je_doc.docstatus == 1 and
				remark_contains in (je_doc.user_remark or "")
			):
				je_doc.cancel()
		except Exception:
			frappe.log_error("JE Cancel Error", frappe.get_traceback())
