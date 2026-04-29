// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Assignment", {
	refresh(frm) {
		filter_shift_type(frm);
	},
	onload: function(frm) {
		filter_shift_type(frm);
	},
	company: function(frm) {
		filter_shift_type(frm);
	},
});

/*
 * function to filter  shift type field based on selected company
 */
function filter_shift_type(frm) {
	frm.set_query("shift_type", function() {
		return {
			filters: {
				"company": frm.doc.company
			}
		}
	})
}