// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Timesheet", {
	refresh(frm) {
		hide_currency_fields(frm);
	}
});

// Hide currency and exchange rate fields based on Fujishkahr Settings
function hide_currency_fields(frm) {
	const company = frm.doc.company
		|| frappe.defaults.get_default("company");

	frappe.db.get_value(
		"Company Ways Settings",
		{"company": company},
		"hide_currency_fields"
	).then(r => {
		const value = r.message?.hide_currency_fields;
		frm.set_df_property("currency", "hidden", value ? true : false);
		frm.set_df_property("exchange_rate", "hidden", value ? true : false);
	});
}