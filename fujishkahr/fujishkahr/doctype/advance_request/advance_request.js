// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Request', {
	refresh(frm) {
		toggle_required(frm);
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
