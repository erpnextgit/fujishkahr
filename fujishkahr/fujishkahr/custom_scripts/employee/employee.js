// Copyright (c) 2026, erpnextgit@fujishkaerp.in and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh(frm) {
		if (!frm.doc.name) return;
		const field = frm.fields_dict.custom_attendance_heatmap;
		if (!field) return;
		field.wrapper.innerHTML = "";

		new custom.attendance.Heatmap({
			wrapper: field.wrapper,
			employee: frm.doc.name,
			year: new Date().getFullYear()
		});
	},
	validate(frm) {
		validate_probation_dates(frm);
	},
	date_of_joining: function(frm) {
		set_probation_dates(frm);
	},
	probation_start_date: function(frm) {
		set_probation_dates(frm);
		validate_probation_dates(frm);
	},
	probation_end_date: function(frm) {
		validate_probation_dates(frm);
	},
	employment_type: function(frm) {
		set_probation_dates(frm);
		validate_probation_dates(frm);
	},
	company: function(frm) {
		filter_reports_to_company(frm);
		filter_holiday_list(frm);
	},
});

/*
 * function to set probation start and end dates
 * based on date of joining and default probation period from settings
 */
function set_probation_dates(frm) {
	if (!frm.doc.is_probation) {
		frm.set_value('probation_start_date', null);
		frm.set_value('probation_end_date', null);
		return;
	}

	let start_date = frm.doc.probation_start_date || frm.doc.date_of_joining;

	if (!start_date) return;

	if (!frm.doc.probation_start_date) {
		frm.set_value('probation_start_date', start_date);
	}

	if (!frm.doc.probation_end_date) {
		frappe.call({
			method: "fujishkahr.fujishkahr.custom_scripts.employee.employee.get_default_probation_period",
			callback: function(r) {
				if (r.message && r.message > 0) {
					let end_date = frappe.datetime.add_days(start_date, r.message);
					frm.set_value('probation_end_date', end_date);
				} else {
					frappe.msgprint({
						title: __('Missing Data'),
						message: __('Default Probation Period is not set in Fujishkahr Settings.'),
						indicator: 'red'
					});
					frm.set_value('probation_end_date', null);
				}
			}
		});
	}
}

/*
 * function to validate probation start and end dates
 * 1. probation end date cannot be before probation start date
 * 2. probation start date cannot be before date of joining
 */
function validate_probation_dates(frm) {
	if (frm.doc.probation_start_date && frm.doc.probation_end_date) {
		if (frm.doc.probation_end_date < frm.doc.probation_start_date) {
			frappe.throw({
				message: __('Probation End Date must be after Probation Start Date'),
				title: __('Invalid Probation Date')
			});
		}
	}

	if (frm.doc.date_of_joining && frm.doc.probation_start_date) {
		if (frm.doc.probation_start_date < frm.doc.date_of_joining) {
			frappe.throw({
				message: __('Probation Start Date must be after Date of Joining'),
				title: __('Invalid Probation Date')
			});
		}
	}
}

/*
 * function to filter reports_to field based on selected company
 * only active employees of the same company will be shown in the reports_to field
 * current employee will be excluded from the list
 */
function filter_reports_to_company(frm) {
	frm.set_query("reports_to", function(){
		return {
			filters: {
				"company": frm.doc.company,
				"status": "Active",
				"name": ["!=", frm.doc.name]
			}
		}
	})
}

/*
 * function to filter holiday list field based on selected company
 * only holiday lists of the same company will be shown in the holiday list field
 */
function filter_holiday_list(frm) {
	frm.set_query("holiday_list", function() {
		return {
			filters: {
				"company": frm.doc.company
			}
		}
	})
}