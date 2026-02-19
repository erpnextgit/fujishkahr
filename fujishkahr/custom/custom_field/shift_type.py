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
		]
	}