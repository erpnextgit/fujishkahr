def get_salary_component_custom_fields():
	"""
	Custom fields that need to be added to the Salary Component DocType
	"""
	return {
		"Salary Component": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "description",
				"options": "Company",
			},
		]
	}