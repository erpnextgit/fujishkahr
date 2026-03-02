def get_shift_type_custom_fields():
	"""
	Custom fields that need to be added to the Shift Type DocType
	"""
	return {
		"Shift Type": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "end_time",
				"options": "Company",
			},
			{
				"fieldtype": "Float",
				"label": "Standard Working Hours",
				"fieldname": "std_working_hours",
				"insert_after": "company"
			},
			{
				"fieldtype": "Check",
				"label": "Allow Break Time",
				"fieldname": "allow_break_time",
				"insert_after": "std_working_hours"
			},
			{
				"fieldtype": "Float",
				"label": "Break Hours",
				"fieldname": "break_hours",
				"insert_after": "allow_break_time",
				"depends_on": "eval:doc.allow_break_time == 1"
			},
		]
	}