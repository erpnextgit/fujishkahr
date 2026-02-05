# Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate ,today
from frappe.utils import add_years

@frappe.whitelist()
def get_default_probation_period():
	"""
	Return default probation period in days from Fujishkahr Settings.
	"""
	period = frappe.db.get_single_value("Fujishkahr Settings", "default_probation_period")
	return int(period)

