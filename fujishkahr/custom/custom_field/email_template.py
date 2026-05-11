def get_email_template_custom_fields():
	"""
	Custom fields that need to be added to the Email Template DocType
	"""
	return {
		"Email Template": [
			{
				"fieldtype": "Link",
				"label": "Company",
				"fieldname": "company",
				"insert_after": "subject",
				"options": "Company",
			},
		]
	}