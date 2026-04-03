def get_additional_salary_custom_fields():
	"""
	Custom fields that need to be added to the Additional Salary DocType
	"""
	return {
		"Additional Salary": [
			{
				"fieldtype": "Column Break",    
				"fieldname": "column_break_1",
				"insert_after": "ref_docname"
			},
			{
				"fieldtype": "Link",
				"label": "Advance Request",
				"fieldname": "advance_request",
				"insert_after": "column_break_1",
				"options": "Advance Request",
				"read_only": 1,
			},
		]
	}