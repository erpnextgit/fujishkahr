// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Request', {
	refresh(frm) {
		toggle_required(frm);
		create_additional_salary(frm);
	},
	workflow_state(frm) {
		toggle_required(frm);
	}
});

function toggle_required(frm) {
	if (frm.doc.workflow_state === "Forward to CEO") {
		frm.set_df_property('payment_credit_date', 'reqd', 1);
		frm.set_df_property('approved_amount', 'reqd', 1);
	} else {
		frm.set_df_property('payment_credit_date', 'reqd', 0);
		frm.set_df_property('approved_amount', 'reqd', 0);
	}
}

function create_additional_salary(frm) {
	if (frm.doc.workflow_state === "Approved") {
		frm.add_custom_button(__('Create Additional Salary'), function() {
			let d = new frappe.ui.Dialog({
				title: 'Create Additional Salary',
				fields: [
					{
						label: 'Employee',
						fieldname: 'employee',
						fieldtype: 'Link',
						options: 'Employee',
						default: frm.doc.employee,
						read_only: 1,
					},
					{
						label: 'Company',
						fieldname: 'company',
						fieldtype: 'Link',
						options: 'Company',
						default: frm.doc.company,
						read_only: 1,
					},
					{
						fieldtype: 'Column Break'
					},
					{
						label: 'Advance Amount',
						fieldname: 'advance_amount',
						fieldtype: 'Currency',
						default: frm.doc.approved_amount,
						read_only: 1,
					},
					{
						label: 'Salary Component',
						fieldname: 'salary_component',
						fieldtype: 'Link',
						options: 'Salary Component',
						reqd: 1,
						get_query() {
							return {
								filters: {
									"type": "Deduction"
								}
							};
						}
					},
					{
						fieldtype: 'Section Break'
					},
					{
						label: 'Is Installment',
						fieldname: 'is_installment',
						fieldtype: 'Check',
					},
					{
						label: 'Number of Months',
						fieldname: 'months',
						fieldtype: 'Int',
						depends_on: 'eval:doc.is_installment == 1',
					},
					{
						label: 'Start Month',
						fieldname: 'start_month',
						fieldtype: 'Date',
						depends_on: 'eval:doc.is_installment == 1',
					},
					{
						label: 'Monthly Amount',
						fieldname: 'monthly_amount',
						fieldtype: 'Currency',
						read_only: 1,
						depends_on: 'eval:doc.is_installment == 1',
					},
					{
						fieldtype: 'Section Break'
					},
					{
						label: 'Deduct Full Amount',
						fieldname: 'deduct_full',
						fieldtype: 'Check',
					},
					{
						label: 'Deduction Month',
						fieldname: 'deduction_month',
						fieldtype: 'Date',
						depends_on: 'eval:doc.deduct_full == 1',
					}

				],
				primary_action_label: 'Submit',
				primary_action(values) {
					if (!values.is_installment && !values.deduct_full) {
						frappe.msgprint("Select either Installment or Full Deduction");
						return;
					}
					frappe.call({
						method: 'fujishkahr.fujishkahr.doctype.advance_request.advance_request.create_additional_salary',
						args: {
							docname: frm.doc.name,
							data: values
						},
						callback: function(r) {
							if (r.message) {
								let links = r.message.map(name => {
									return `<a href="/app/additional-salary/${name}" target="_blank">${name}</a>`;
								}).join("<br>");

								frappe.msgprint({
									title: "Success",
									message: `Additional Salary Created:<br>${links}`,
									indicator: "green"
								});
							}
							d.hide();
						}
					});
				}
			});

			d.show();
			d.fields_dict.months.df.onchange = () => calculate();
			d.fields_dict.advance_amount.df.onchange = () => calculate();

			d.fields_dict.is_installment.df.onchange = () => {
				if (d.get_value('is_installment')) {
					d.set_value('deduct_full', 0);
					d.set_value('months', 0)
					d.set_value('start_month', null);
					d.set_value('monthly_amount', 0);
				}
			};

			d.fields_dict.deduct_full.df.onchange = () => {
				if (d.get_value('deduct_full')) {
					d.set_value('is_installment', 0);
					d.set_value('deduction_month', 0)
				}
			};

			function calculate() {
				let values = d.get_values();
				if (values.months && values.advance_amount) {
					let monthly = values.advance_amount / values.months;
					d.set_value('monthly_amount', monthly);
				}
			}
		});

	}
}