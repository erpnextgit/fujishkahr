def get_employee_custom_fields():
	"""
	Custom fields that need to be added to the Employee DocType
	"""
	return {
		"Employee": [
			{
				"fieldtype": "Section Break",
				"label": "Probation",
				"fieldname": "sb_probation",
				"insert_after": "grade",
			},
			{
				"fieldname": "probation_start_date",
				"fieldtype": "Date",
				"label": "Probation Start Date",
				"insert_after": "sb_probation",
			},
			{
				"fieldtype": "Column Break",
				"fieldname": "cb_probation",
				"insert_after": "probation_start_date",
			},
			{
				"fieldname": "probation_end_date",
				"fieldtype": "Date",
				"label": "Probation End Date",
				"insert_after": "cb_probation",
			},
			{
				"fieldtype": "Section Break",
				"label": "Employee Document History",
				"fieldname": "employee_document_history_section",
				"insert_after": "external_work_history",
				"collapsible": 1,
			},
			{
				"fieldname": "employee_documents",
				"fieldtype": "Table",
				"options": "Employee Documents",
				"label": "Employee Documents",
				"insert_after": "employee_document_history_section",
			},
		]
	}
