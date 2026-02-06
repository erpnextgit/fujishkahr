frappe.ui.form.on("Holiday List", {
	refresh(frm) {

		frm.add_custom_button("Add 1st Saturday", () => {
			add_nth_saturday(frm, 1);
		});

		frm.add_custom_button("Add 2nd Saturday", () => {
			add_nth_saturday(frm, 2);
		});

		frm.add_custom_button("Add 3rd Saturday", () => {
			add_nth_saturday(frm, 3);
		});

		frm.add_custom_button("Add 4th Saturday", () => {
			add_nth_saturday(frm, 4);
		});

		frm.add_custom_button("Add 5th Saturday", () => {
			add_nth_saturday(frm, 5);
		});
	}
});

/*
* Adds the 1st to 5th Saturday between from_date and to_date to the holidays table
*/
function add_nth_saturday(frm, n) {
	const from = frappe.datetime.str_to_obj(frm.doc.from_date);
	const to = frappe.datetime.str_to_obj(frm.doc.to_date);

	for (
		let d = new Date(from.getFullYear(), from.getMonth(), 1);
		d <= to;
		d.setMonth(d.getMonth() + 1)
	) {
		let saturdays = [];
		let temp = new Date(d.getFullYear(), d.getMonth(), 1);

		while (temp.getMonth() === d.getMonth()) {
			if (temp.getDay() === 6) {
				saturdays.push(new Date(temp));
			}
			temp.setDate(temp.getDate() + 1);
		}

		const target = saturdays[n - 1];

		// 5th Saturday may not exist
		if (target && target >= from && target <= to) {
			const date_str = frappe.datetime.obj_to_str(target);

			// prevent duplicates
			if (!frm.doc.holidays.some(h => h.holiday_date === date_str)) {
				frm.add_child("holidays", {
					holiday_date: date_str,
					description: `${n}${ordinal(n)} Saturday`
				});
			}
		}
	}

	frm.refresh_field("holidays");
}

/*
* Returns the ordinal suffix for a given number (1st, 2nd, 3rd, etc.)
*/
function ordinal(n) {
	if (n === 1) return "st";
	if (n === 2) return "nd";
	if (n === 3) return "rd";
	return "th";
}
