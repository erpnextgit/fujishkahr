def get_employee_checkin_custom_fields():
	"""
	Custom fields that need to be added to the Employee Checkin DocType
	"""
	return {
		"Employee Checkin": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "log_type",
				"options": "Company",
			},
			{
				"fieldtype": "Check",
				"label": "Is Late Entry",
				"fieldname": "late_entry",
				"insert_after": "skip_auto_attendance",
				"read_only": 1,
			}
		]
	}