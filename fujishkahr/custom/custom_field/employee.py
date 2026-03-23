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
				"depends_on": "eval:doc.is_probation",
			},
			{
				"fieldname": "probation_start_date",
				"fieldtype": "Date",
				"label": "Probation Start Date",
				"insert_after": "sb_probation",
				"depends_on": "eval:doc.is_probation",
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
				"depends_on": "eval:doc.is_probation",
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
			{
				"fieldtype": "Section Break",
				"label": "Attendance Summary",
				"fieldname": "sb_attendance_summary",
				"insert_after": "connections_tab",
				"collapsible": 1,
				"depends_on": "eval: !doc.__islocal",
			},
			{
				"fieldname": "custom_attendance_heatmap",
				"fieldtype": "HTML",
				"label": "Attendance Heatmap",
				"insert_after": "sb_attendance_summary",
				"depends_on": "eval:!doc.__islocal",
			},
			{
				"fieldname": "is_probation",
				"fieldtype": "Check",
				"label": "Is Probation",
				"insert_after": "employment_type",
				"hidden": 1,
				"fetch_from": "employment_type.is_probation",
			},
		]
	}
