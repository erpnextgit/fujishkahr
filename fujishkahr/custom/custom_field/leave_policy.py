def get_leave_policy_custom_fields():
	"""
	Custom fields that need to be added to the Leave Policy DocType
	"""
	return {
		"Leave Policy": [
			{
				"fieldtype": "Column Break",
				"fieldname": "cb_leave_policy_1",
				"insert_after": "title",
			},
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "cb_leave_policy_1",
				"options": "Company",
				"reqd": 1,
			},
		]
	}