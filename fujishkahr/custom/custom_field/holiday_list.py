def get_holiday_list_custom_fields():
	"""
	Custom fields that need to be added to the Holiday List DocType
	"""
	return {
		"Holiday List": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "total_holidays",
				"options": "Company",
				"reqd": 1,
			},
		]
	}