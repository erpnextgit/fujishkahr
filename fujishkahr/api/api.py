import frappe
import requests
import json
from frappe.integrations.utils import make_get_request

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

@frappe.whitelist()
"""
	Call the external API to register the branch and retrieve token and endpoint.
	Returns a structured response indicating success or failure, along with relevant details.
"""
def call_external_registration_api(company_code, branch_code, branch_password):
	url = "http://fujishka.com/erp/api/registration/desk_register"

	params = {
		"company_code": company_code,
		"branch_code": branch_code,
		"branch_password": branch_password
	}

	try:
		headers = {
			"Accept": "*/*",
			"User-Agent": "PostmanRuntime/7.51.1",
			"Cache-Control": "no-cache",
			"Connection": "keep-alive"
		}

		response = make_get_request(
			url,
			params=params,
			headers=headers
		)

		# Case 1: If string → convert to JSON
		if isinstance(response, str):
			try:
				response = json.loads(response)
			except Exception:
				return {
					"status": "Failed",
					"error": "Invalid JSON response from external API",
					"full_response": response
				}

		# Case 2: If list → take first element
		if isinstance(response, list):
			if len(response) > 0:
				response = response[0]
			else:
				return {
					"status": "Failed",
					"error": "Empty response list from external API",
					"full_response": response
				}

		# Case 3: Ensure it's dict
		if not isinstance(response, dict):
			return {
				"status": "Failed",
				"error": "Unexpected response format from external API",
				"full_response": response
			}

		token = response.get("token")
		endpoint = response.get("endpoint")
		error_msg = response.get("error")

		if token and len(token) > 5:
			return {
				"status": "Success",
				"token": token,
				"endpoint": endpoint,
				"full_response": response
			}

		return {
			"status": "Failed",
			"error": error_msg or "Registration failed",
			"full_response": response
		}

	except Exception:

		frappe.log_error(
			message=frappe.get_traceback(),
			title="Branch Registration API Error"
		)

		return {
			"status": "Failed",
			"error": "Connection Error (Check Error Log)",
			"full_response": "Exception occurred"
		}