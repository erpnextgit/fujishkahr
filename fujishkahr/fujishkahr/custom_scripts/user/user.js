frappe.ui.form.on("User", {
	refresh(frm) {

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
});