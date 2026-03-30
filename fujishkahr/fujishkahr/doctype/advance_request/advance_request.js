// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance Request', {
	refresh: function(frm) {
		if (frm.doc.workflow_state === "Forward to CEO") {
			frm.set_df_property('approved_amount', 'reqd', 1);
		} else {
			frm.set_df_property('approved_amount', 'reqd', 0);
		}
	}
});