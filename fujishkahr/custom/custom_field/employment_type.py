def get_employment_type_custom_fields():
	'''
		Custom fields that need to be added to the Employment Type Doctype
	'''
	return {
		"Employment Type": [
			{
				"fieldname": "is_probation",
				"fieldtype": "Check",
				"label": "Is Probation",
				"insert_after": "employment_type",
				"description": "Check if this employment type is for probation period",
			},
		]
	}