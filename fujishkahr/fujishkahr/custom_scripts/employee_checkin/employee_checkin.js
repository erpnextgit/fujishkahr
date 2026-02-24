frappe.ui.form.on("Employee Checkin", {
	onload(frm) {
		set_employee_from_logged_user(frm);
	}
})

function set_employee_from_logged_user(frm) {
	if (frappe.session.user != "Administrator") {
		frappe.db.get_value("Employee", 
			{"user_id": frappe.session.user}, "name").then((r) => {
				if (r && r.message && r.message.name) {
					frm.set_value("employee", r.message.name);
				}
			})

	}
}
