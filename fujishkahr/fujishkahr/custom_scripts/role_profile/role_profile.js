frappe.ui.form.on("Role Profile", {
	refresh(frm) {
		hide_unwanted_role_profile_roles(frm);
	}
});

function hide_unwanted_role_profile_roles(frm) {

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
			.find(".checkbox.unit-checkbox")
			.each(function () {

				const role =
					$(this)
						.find("input[type='checkbox']")
						.attr("data-unit");

				if (
					role &&
					!allowed_roles.includes(role)
				) {

					$(this).hide();

				}

			});

	}, 5);

}