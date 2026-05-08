import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from fujishkahr.utils.company_settings import get_company_settings, get_company_from_employee

class CustomLeaveApplication(LeaveApplication):

	def _should_send_leave_notification(self):
		"""
		Check Company Ways Settings for this employee's company.
		Returns True if notification should be sent, False otherwise.
		"""
		company = get_company_from_employee(self.employee)
		settings = get_company_settings(company)
		return bool(settings.send_leave_notification)

	def on_submit(self):
		"""
		Override on_submit to handle leave notification per company.
		All other HRMS logic runs normally.
		"""
		super().on_submit()

		if self._should_send_leave_notification():
			frappe.logger().info(
				f"Sending leave approver notification for {self.employee_name} ({self.company})"
			)
			self.notify_leave_approver()
		else:
			frappe.logger().info(
				f"Leave notification disabled for {self.company}. Skipping approver notification."
			)

	def on_update_after_submit(self):
		"""
		Override on_update_after_submit to handle leave status notification per company.
		"""
		super().on_update_after_submit()

		if self.status in ("Approved", "Rejected"):
			if self._should_send_leave_notification():
				frappe.logger().info(
					f"Sending leave status notification to {self.employee_name} ({self.company}) — {self.status}"
				)
				self.notify_employee()
			else:
				frappe.logger().info(
					f"Leave notification disabled for {self.company}. Skipping status notification."
				)

	def on_cancel(self):
		"""
		Override on_cancel to handle leave cancellation notification per company.
		"""
		super().on_cancel()

		if self._should_send_leave_notification():
			frappe.logger().info(
				f"Sending leave cancellation notification to {self.employee_name} ({self.company})"
			)
			self.notify_employee()
		else:
			frappe.logger().info(
				f"Leave notification disabled for {self.company}. Skipping cancellation notification."
			)