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
	}
});
