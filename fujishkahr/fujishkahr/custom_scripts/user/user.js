frappe.ui.form.on("User", {
	refresh(frm) {
		hide_unwanted_roles(frm);
		hide_unwanted_modules(frm);
	}
});

/* function to hide unwanted modules from the user form */
function hide_unwanted_modules(frm) {
	console.log("hide_unwanted_modules called");

	setTimeout(() => {

		const allowed = [
			"HR",
			"Payroll",
			"Fujishkahr",
			"Desk",
		];

		const wrapper =
			frm.fields_dict
				.modules_html
				.$wrapper;

		wrapper
			.find(
				".checkbox.unit-checkbox"
			)
			.each(function () {

				const text =
					$(this)
					.find(
						".label-area"
					)
					.text()
					.trim();

				if (
					!allowed.includes(
						text
					)
				) {

					$(this)
						.remove();

				}

			});

	}, 10);

}

/* function to hide unwanted roles from the user form */
function hide_unwanted_roles(frm) {

	setTimeout(() => {

		const allowed_roles = [
			"Accounts Manager",
			"Accounts User",
			"CEO",
			"Employee",
			"Expense Approver",
			"Fujishka Employee",
			"Fujishka HR",
			"Interviewer",
			"HR Manager",
			"HR User",
			"Leave Approver",
			"Projects Manager",
			"Projects User",
			"Report Manager",
			"Support Team",
			"System Manager",
			"Website Manager",
			"Workspace Manager",
			"Manager"
		];

		frm.$wrapper
			.find(".checkbox-options .checkbox")
			.each(function () {

				const role =
					$(this)
					.find(".label-area")
					.text()
					.trim();

				if (
					role &&
					!allowed_roles.includes(role)
				) {
					$(this).hide();
				}

			});

	}, 10);

}