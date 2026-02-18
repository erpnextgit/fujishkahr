def get_user_custom_fields():
	"""
	Custom fields that need to be added to the User DocType
	"""
	return {
		"User": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "username",
				"options": "Company",
				"reqd": 1,
			},
		]
	}