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
			{
				"fieldtype": "Check",
				"label": "Is Employee PF",
				"fieldname": "is_employee_pf",
				"insert_after": "disabled",
			},
			{
				"fieldtype": "Check",
				"label": "Is Employee ESI",
				"fieldname": "is_employee_esi",
				"insert_after": "is_employee_pf",
			},
		]
	}