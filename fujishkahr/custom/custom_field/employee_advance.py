def get_employee_advance_custom_fields():
	"""
	Custom fields that need to be added to the Employee Advance DocType
	"""
	return {
		"Employee Advance": [
			{
				"fieldtype": "Link",
				"label": "Advance Request",
				"fieldname": "advance_request",
				"insert_after": "column_break_kimx",
				"options": "Advance Request",
				"read_only": 1,
			},
		]
	}