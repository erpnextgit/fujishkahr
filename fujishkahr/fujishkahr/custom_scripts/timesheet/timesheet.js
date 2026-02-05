// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		hide_currency_fields(frm);
	}
});

// Hide currency and exchange rate fields based on Fujishkahr Settings
function hide_currency_fields(frm) {
	frappe.db.get_single_value("Fujishkahr Settings", "hide_currency_fields")
	.then(value => {
		if (value) {
			frm.set_df_property("currency", "hidden", true);
			frm.set_df_property("exchange_rate", "hidden", true);
		}
		else {
			frm.set_df_property("currency", "hidden", false);
			frm.set_df_property("exchange_rate", "hidden", false);
		}
	})
}