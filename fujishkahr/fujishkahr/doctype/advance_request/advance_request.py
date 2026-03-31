# Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.setup.utils import get_exchange_rate

class AdvanceRequest(Document):

	def on_submit(self):
		if self.workflow_state == "Approved":
			self.create_employee_advance()
			self.send_approval_email()

	def create_employee_advance(self):
		"""
			Creates an Employee Advance document based on the approved Advance Request.
			Calculates exchange rate if the advance account currency differs from the company currency.
		"""
		if not self.approved_amount or self.approved_amount <= 0:
			frappe.throw("Approved amount must be set before creating Employee Advance.")

		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		account_currency = frappe.get_cached_value("Account", self.advance_account, "account_currency")

		if account_currency == company_currency:
			exchange_rate = 1.0
		else:
			exchange_rate = get_exchange_rate(
				account_currency,
				company_currency,
				self.posting_date or frappe.utils.today()
			) or 1.0

		advance = frappe.new_doc("Employee Advance")
		advance.employee = self.employee
		advance.employee_name  = self.employee_name
		advance.purpose = self.purpose or "Salary Advance"
		advance.company = self.company
		advance.posting_date = frappe.utils.today()
		advance.advance_amount = self.approved_amount
		advance.advance_account = self.advance_account
		advance.currency = account_currency
		advance.exchange_rate = exchange_rate
		advance.repay_unclaimed_amount_from_salary = 1

		advance.insert(ignore_permissions=True)
		advance.submit()

		frappe.msgprint(
			f"Employee Advance <b>{advance.name}</b> created and submitted successfully.",
			alert=True
		)

	def send_approval_email(self):
		"""
			Sends an email notification to the employee when their advance request is approved.
		"""
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id")

		if not employee_user:
			frappe.log_error(
				f"No user linked to employee {self.employee}. Approval email not sent.",
				"Advance Request Email"
			)
			return

		frappe.sendmail(
			recipients=[employee_user],
			subject=f"Your Advance Request {self.name} has been Approved",
			message=f"""
				<p>Dear {self.employee_name},</p>

				<p>We are pleased to inform you that your advance request has been 
				<b style="color: green;">Approved</b>.</p>

				<table border="1" cellpadding="8" cellspacing="0" 
					   style="border-collapse: collapse; width: 100%;">
					<tr>
						<td><b>Request ID</b></td>
						<td>{self.name}</td>
					</tr>
					<tr>
						<td><b>Requested Amount</b></td>
						<td>{self.requested_amount}</td>
					</tr>
					<tr>
						<td><b>Approved Amount</b></td>
						<td>{self.approved_amount}</td>
					</tr>
					<tr>
						<td><b>Purpose</b></td>
						<td>{self.purpose}</td>
					</tr>
					<tr>
						<td><b>Date</b></td>
						<td>{self.posting_date}</td>
					</tr>
				</table>

				<br>
				<p>The advance amount will be processed on {self.payment_credit_date}.</p>

				<p>Regards,<br>HR Team</p>
			""",
			now=True
		)