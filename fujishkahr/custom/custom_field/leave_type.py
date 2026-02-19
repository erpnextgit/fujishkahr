def get_leave_type_custom_fields():
	"""
	Custom fields that need to be added to the Leave Type DocType
	"""
	return {
		"Leave Type": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "max_continuous_days_allowed",
				"options": "Company",
			},
		]
	}