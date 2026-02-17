def get_company_custom_fields():
	"""
	Custom fields that need to be added to the Company DocType
	"""
	return {
		"Company": [
			{
				"fieldtype": "Data",
				"label": "Company Code",
				"fieldname": "company_code",
				"insert_after": "parent_company",
				"reqd": 1,
				"unique": 1,
			},
		]
	}