def get_payroll_entry_custom_fields():
	return {
		"Payroll Entry": [
			{
				"fieldtype": "Section Break",
				"label": "External Payment Details",
				"fieldname": "custom_external_payment_section",
				"insert_after": "end_date",
			},
			{
				"fieldtype": "Currency",
				"label": "Total Salary",
				"fieldname": "custom_total_salary",
				"insert_after": "custom_external_payment_section",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Currency",
				"label": "Total Deduction",
				"fieldname": "custom_total_deduction",
				"insert_after": "custom_total_salary",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Column Break",
				"fieldname": "custom_col_break_payment",
				"insert_after": "custom_total_deduction",
			},
			{
				"fieldtype": "Currency",
				"label": "Salary Paid",
				"fieldname": "custom_salary_paid",
				"insert_after": "custom_col_break_payment",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Currency",
				"label": "Deduction Paid",
				"fieldname": "custom_deduction_paid",
				"insert_after": "custom_salary_paid",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "custom_payment_status_section",
				"insert_after": "custom_deduction_paid",
			},
			{
				"fieldtype": "Select",
				"label": "Payment Status",
				"fieldname": "custom_payment_status",
				"insert_after": "custom_payment_status_section",
				"options": "\nPending\nPartial\nPaid",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Check",
				"label": "Salary PE Created",
				"fieldname": "custom_salary_pe_created",
				"insert_after": "custom_payment_status",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Check",
				"label": "Deduction PE Created",
				"fieldname": "custom_deduction_pe_created",
				"insert_after": "custom_salary_pe_created",
				"allow_on_submit": 1,
			},
			{
				"fieldtype": "Check",
				"label": "API Pushed",
				"fieldname": "custom_api_pushed",
				"insert_after": "custom_deduction_pe_created",
				"allow_on_submit": 1,
			},
		]
	}