def get_salary_slip_property_setters():
	return [
		{
			"doctype": "Property Setter",
			"doctype_or_field": "DocField",
			"doc_type": "Salary Slip",
			"field_name": "status",
			"property": "options",
			"value": "Draft\nSubmitted\nCancelled\nWithheld\nPaid\nCompleted"
		},
		{
			"doctype": "DocType State",
			"parent": "Salary Slip",
			"parentfield": "states",
			"parenttype": "DocType",
			"title": "Paid",
			"color": "Green"
		},
		{
			"doctype": "DocType State",
			"parent": "Salary Slip",
			"parentfield": "states",
			"parenttype": "DocType",
			"title": "Completed",
			"color": "Blue"
		},
	]

