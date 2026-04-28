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
			},
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "branch_code",
				"options": "Company",
				"reqd": 1,
			},
            {
                "fieldtype":    "Data",
                "label":        "Branch Unique Name",
                "fieldname":    "branch_unique_name",
                "insert_after": "company",
                "hidden":       1,
                "read_only":    1,
            },
		]
	}