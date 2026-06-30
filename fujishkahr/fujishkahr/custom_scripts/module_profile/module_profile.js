frappe.ui.form.on(
	"Module Profile",
	{
		refresh(frm) {

			setTimeout(() => {

				const allowed = [
					"HR",
					"Payroll",
					"Fujishkahr",
					"Desk"
				];

				$(
					".checkbox.unit-checkbox"
				).each(function () {

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
							.hide();

					}

				});

			}, 10);

		}
	}
);