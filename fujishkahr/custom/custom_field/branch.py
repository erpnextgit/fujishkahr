def get_branch_custom_fields():
	"""
	Custom fields that need to be added to the Branch DocType
	"""
	return {
		"Branch": [
			{
				"fieldtype": "Data",
				"label": "Branch Code",
				"fieldname": "branch_code",
				"insert_after": "branch",
				"unique": 1,
			},
		]
	}